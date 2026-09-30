import logging

from fastapi import Depends, FastAPI, HTTPException

from app.fetcher import fetch_file
from app.inspector import inspect_file
from app.markers.base import Marker, MarkingInput
from app.markers.gemini_marker import GeminiMarker
from app.schemas import MarkRequest, MarkResponse
from app.security import require_api_key

log = logging.getLogger("soi.marking")

# Main FastAPI app for the SOI marking service.
# Laravel sends submissions here for marking.
app = FastAPI(title="SOI Marking Service")

BAD_FILE_FEEDBACK = (
    "We could not open your file. Please upload a clear photo, "
    "a PDF, or a Word document and try again."
)


# Picks the marker to use.
# Only Gemini for now. The fallback marker gets added here later.
def get_marker() -> Marker:
    return GeminiMarker()


# Simple health check.
# Used to confirm the service is up (and later by the load balancer).
@app.get("/health")
def health():
    return {"status": "ok"}


# Response for a student file we cannot use.
# Laravel treats this as unreadable, so no attempt is used up.
def _unusable_submission() -> MarkResponse:
    return MarkResponse(
        score=None, confidence=0, feedback=BAD_FILE_FEEDBACK, unreadable=True
    )


# Mark a submission.
# Download both files, check their type, then ask the marker.
@app.post("/mark", response_model=MarkResponse,
          dependencies=[Depends(require_api_key)])
def mark(request: MarkRequest):
    try:
        memo_bytes = fetch_file(request.memo_url)
        submission_bytes = fetch_file(request.submission_url)
    except Exception as exc:
        log.warning("Download failed for submission %s: %s",
                    request.submission_id, exc)
        raise HTTPException(status_code=502, detail="Could not download files")

    try:
        memo = inspect_file(memo_bytes)
    except ValueError:
        raise HTTPException(status_code=422, detail="Memo file type not supported")

    try:
        submission = inspect_file(submission_bytes)
    except ValueError:
        return _unusable_submission()

    marking_input = MarkingInput(
        total_points=request.total_points,
        submission=submission,
        memo=memo,
        rubric=request.rubric_criteria,
    )
    try:
        return get_marker().mark(marking_input)
    except Exception:
        log.exception("Marker failed for submission %s", request.submission_id)
        raise HTTPException(status_code=503, detail="Marking is unavailable")
