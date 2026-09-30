from fastapi import FastAPI

from app.schemas import MarkRequest, MarkResponse

# Main FastAPI app for the SOI marking service.
# Laravel sends submissions here for OCR and marking.
app = FastAPI(title="SOI Marking Service")


# Simple health check.
# Used to confirm the service is up (and later by the load balancer).
@app.get("/health")
def health():
    return {"status": "ok"}


# Mark a submission.
# Stub for now: returns fixed data so we can test the shape.
# Real OCR and marking come in Steps 3 and 4.
@app.post("/mark", response_model=MarkResponse)
def mark(request: MarkRequest):
    scores = {str(c.id): c.max_points for c in request.rubric_criteria}
    return MarkResponse(
        score=request.total_points * 0.75,
        confidence=90,
        feedback="Stub feedback",
        criterion_scores=scores,
    )
