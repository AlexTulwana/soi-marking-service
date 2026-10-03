import io

import docx
import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.config import settings
from app.markers.similarity_marker import SimilarityMarker
from app.ocr.base import OcrEngine, OcrResult


class FakeOcr(OcrEngine):
    def read(self, file_bytes):
        return OcrResult("", 0.0)


# Stands in for Gemini being down.
class BrokenMarker:
    def mark(self, marking_input):
        raise RuntimeError("Gemini is down")


def word_file(lines):
    d = docx.Document()
    for line in lines:
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


MEMO = ["Solve 2x + 6 = 14", "2x = 14 - 6", "2x = 8", "x = 4"]
FILES = {
    "memo": word_file(MEMO),
    "work": word_file(["2x = 14 - 6", "2x = 8", "x = 4"]),
}
BODY = {"submission_id": 1, "submission_url": "work", "memo_url": "memo", "total_points": 10}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "service_api_key", "k")
    monkeypatch.setattr(settings, "fallback_enabled", True)
    monkeypatch.setattr(main, "fetch_file", lambda url: FILES[url])
    monkeypatch.setattr(main, "get_marker", lambda: BrokenMarker())
    monkeypatch.setattr(main, "get_fallback_marker", lambda: SimilarityMarker(FakeOcr()))
    return TestClient(main.app, headers={"X-API-Key": "k"})


def test_fallback_gives_a_provisional_mark_when_gemini_is_down(client):
    response = client.post("/mark", json=BODY)
    assert response.status_code == 200
    assert response.json()["provisional"] is True
    assert response.json()["score"] == 10


def test_unreadable_photo_still_ends_in_503(client, monkeypatch):
    monkeypatch.setitem(FILES, "work", b"\x89PNG not really an image")
    monkeypatch.setitem(FILES, "photo", FILES["work"])
    # a real-looking image that the fake OCR cannot read
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (50, 50), "white").save(buf, format="PNG")
    monkeypatch.setitem(FILES, "work", buf.getvalue())
    assert client.post("/mark", json=BODY).status_code == 503


def test_fallback_can_be_switched_off(client, monkeypatch):
    monkeypatch.setattr(settings, "fallback_enabled", False)
    monkeypatch.setattr(main, "get_fallback_marker", main.get_fallback_marker.__wrapped__
                        if hasattr(main.get_fallback_marker, "__wrapped__") else lambda: None)
    assert client.post("/mark", json=BODY).status_code == 503


def test_normal_marker_result_is_not_provisional(client, monkeypatch):
    from app.schemas import MarkResponse

    class GoodMarker:
        def mark(self, marking_input):
            return MarkResponse(score=9, confidence=95, feedback="ok")

    monkeypatch.setattr(main, "get_marker", lambda: GoodMarker())
    assert client.post("/mark", json=BODY).json()["provisional"] is False
