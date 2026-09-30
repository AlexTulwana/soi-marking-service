from app.ocr.base import OcrEngine
from app.ocr.tesseract_engine import TesseractEngine


# Picks the OCR engine to use.
# Only Tesseract for now. A cloud engine gets added here later.
def get_ocr_engine() -> OcrEngine:
    return TesseractEngine()
