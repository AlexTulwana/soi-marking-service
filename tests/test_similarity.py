import pytest

from app.markers.base import FilePayload, MarkingInput
from app.markers.similarity_marker import CannotRead, SimilarityMarker
from app.ocr.base import OcrEngine, OcrResult


# Fake OCR so these tests need no Tesseract.
class FakeOcr(OcrEngine):
    def __init__(self, text="", confidence=90.0):
        self.text = text
        self.confidence = confidence

    def read(self, file_bytes):
        return OcrResult(self.text, self.confidence)


def typed(text):
    return FilePayload(b"", "application/pdf", text)


def photo():
    return FilePayload(b"img", "image/png", None)


MEMO = "Solve 2x + 6 = 14\n2x = 14 - 6\n2x = 8\nx = 4"


def mark(memo, work, ocr=None, total=10):
    marker = SimilarityMarker(ocr or FakeOcr())
    return marker.mark(MarkingInput(total, work, memo))


def test_correct_typed_work_gets_full_marks_and_is_provisional():
    result = mark(typed(MEMO), typed("2x = 14 - 6\n2x = 8\nx = 4\nAnswer: x = 4"))
    assert result.score == 10
    assert result.provisional is True
    assert result.unreadable is False
    assert result.criterion_scores == {}


def test_wrong_final_answer_scores_lower():
    result = mark(typed(MEMO), typed("2x = 14 - 6\n2x = 8\nx = 10"))
    assert 0 < result.score < 10


def test_decimal_comma_and_trailing_zero_count_as_the_same_number():
    result = mark(typed("x = 4,5 and y = 2"), typed("x = 4.5; y = 2.0 is my answer"))
    assert result.score == 10


def test_words_decide_when_the_memo_has_no_numbers():
    memo = "Photosynthesis converts sunlight water carbon dioxide into glucose and oxygen"
    work = "Plants use sunlight, water and carbon dioxide to make glucose and release oxygen"
    assert mark(typed(memo), typed(work)).score == 7.5


def test_photo_is_read_with_ocr():
    result = mark(typed(MEMO), photo(), ocr=FakeOcr("2x = 14 - 6\n2x = 8\nx = 4"))
    assert result.score == 10


def test_weak_ocr_is_refused_not_guessed():
    with pytest.raises(CannotRead):
        mark(typed(MEMO), photo(), ocr=FakeOcr("2x = 14 - 6 x = 4", confidence=20.0))


def test_blank_work_is_refused():
    with pytest.raises(CannotRead):
        mark(typed(MEMO), photo(), ocr=FakeOcr("", confidence=0.0))


def test_score_is_never_above_the_total():
    result = mark(typed(MEMO), typed("2 6 14 8 4 and more numbers 99"), total=7)
    assert result.score <= 7
