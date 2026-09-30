import io

import pymupdf
import pytesseract
from PIL import Image

from app.ocr.base import OcrEngine, OcrResult


# Free local OCR engine, used in dev.
# Handles images and PDFs (each PDF page becomes an image).
class TesseractEngine(OcrEngine):
    def read(self, file_bytes: bytes) -> OcrResult:
        texts = []
        confs = []
        for image in self._to_images(file_bytes):
            data = pytesseract.image_to_data(
                image, output_type=pytesseract.Output.DICT
            )
            words = []
            for word, conf in zip(data["text"], data["conf"]):
                if word.strip() and float(conf) >= 0:
                    words.append(word)
                    confs.append(float(conf))
            texts.append(" ".join(words))

        text = "\n".join(texts).strip()
        confidence = sum(confs) / len(confs) if confs else 0.0
        return OcrResult(text=text, confidence=confidence)

    # Turn the file into a list of images.
    # PDFs are rendered page by page, anything else opens as an image.
    def _to_images(self, file_bytes: bytes) -> list[Image.Image]:
        if file_bytes[:4] == b"%PDF":
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            images = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
            return images
        return [Image.open(io.BytesIO(file_bytes))]
