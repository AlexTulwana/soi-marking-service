from abc import ABC, abstractmethod
from dataclasses import dataclass


# What an OCR engine returns.
# text = everything it read, confidence = 0-100 average.
@dataclass
class OcrResult:
    text: str
    confidence: float


# Contract for any OCR engine (Tesseract now, cloud later).
# Marking code only talks to this, so engines are swappable.
class OcrEngine(ABC):
    @abstractmethod
    def read(self, file_bytes: bytes) -> OcrResult:
        ...
