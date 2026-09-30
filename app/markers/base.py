from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.schemas import MarkResponse, RubricCriterion


# One downloaded file, ready for a marker.
# text is filled for typed files, data is always the raw bytes.
@dataclass
class FilePayload:
    data: bytes
    mime_type: str
    text: str | None = None


# Everything a marker needs to do its job.
# Built by the /mark endpoint after files are downloaded.
@dataclass
class MarkingInput:
    total_points: float
    submission: FilePayload
    memo: FilePayload
    rubric: list[RubricCriterion] = field(default_factory=list)


# Contract for any marker (Gemini now, Similarity fallback later).
# Every marker returns the same MarkResponse Laravel expects.
class Marker(ABC):
    @abstractmethod
    def mark(self, marking_input: MarkingInput) -> MarkResponse:
        ...
