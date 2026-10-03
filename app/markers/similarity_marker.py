import re

from app.config import settings
from app.markers.base import FilePayload, Marker, MarkingInput
from app.ocr.base import OcrEngine
from app.schemas import MarkResponse

NUMBER = re.compile(r"\d+(?:\.\d+)?")
WORD = re.compile(r"[^\W\d_]{4,}")
STOPWORDS = {
    "this", "that", "with", "from", "have", "been", "were", "will", "would",
    "could", "should", "their", "there", "which", "about", "into", "than",
    "then", "them", "these", "those", "what", "when", "where", "your", "also",
    "each", "some", "such", "only", "other", "more", "most", "very", "does",
    "memo", "mark", "marks", "answer", "answers", "question",
}
PROVISIONAL_FEEDBACK = (
    "This is a provisional mark from a basic automatic check, because our "
    "marking assistant was unavailable. A tutor will confirm your final mark."
)


# Raised when a file cannot be read clearly enough for a safe fallback mark.
class CannotRead(ValueError):
    pass


# Basic fallback marker: compares the student's text with the memo's text.
# Crude on purpose, so every mark it gives is provisional.
class SimilarityMarker(Marker):
    def __init__(self, ocr: OcrEngine):
        self.ocr = ocr

    def mark(self, marking_input: MarkingInput) -> MarkResponse:
        memo_text = self._text(marking_input.memo)
        work_text = self._text(marking_input.submission)
        coverage = self._coverage(memo_text, work_text)

        # nearest half mark, never above the total
        score = round(marking_input.total_points * coverage * 2) / 2
        score = max(0.0, min(float(marking_input.total_points), score))

        return MarkResponse(
            score=score,
            confidence=40.0,
            feedback=PROVISIONAL_FEEDBACK,
            criterion_scores={},
            unreadable=False,
            provisional=True,
        )

    # Typed files already carry their text. Photos and scans go through OCR,
    # and a weak or empty read is refused instead of guessed.
    def _text(self, payload: FilePayload) -> str:
        if payload.text is not None:
            text = payload.text
        else:
            result = self.ocr.read(payload.data)
            if result.confidence < settings.fallback_min_ocr_confidence:
                raise CannotRead("OCR confidence too low for a fallback mark")
            text = result.text

        text = re.sub(r"(?<=\d),(?=\d)", ".", text.lower())
        if len(text.strip()) < 10:
            raise CannotRead("Not enough text to mark")
        return text

    # Share of the memo (0 to 1) that shows up in the student's work.
    # Numbers decide when the memo has them; otherwise key words decide.
    def _coverage(self, memo_text: str, work_text: str) -> float:
        memo_numbers = [self._number(n) for n in NUMBER.findall(memo_text)]
        unique = list(dict.fromkeys(memo_numbers))

        if len(unique) >= 2:
            work_numbers = {self._number(n) for n in NUMBER.findall(work_text)}
            final = memo_numbers[-1]  # the last number is the final answer
            weights = {n: (3 if n == final else 1) for n in unique}
            got = sum(w for n, w in weights.items() if n in work_numbers)
            return got / sum(weights.values())

        memo_words = {w for w in WORD.findall(memo_text) if w not in STOPWORDS}
        if not memo_words:
            raise CannotRead("Memo has nothing comparable")
        work_words = set(WORD.findall(work_text))
        return len(memo_words & work_words) / len(memo_words)

    # 4.0 and 4 are the same number.
    def _number(self, text: str) -> str:
        value = float(text)
        return str(int(value)) if value == int(value) else str(value)
