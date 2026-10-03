from pydantic import BaseModel, Field


# One rubric row sent by Laravel.
# Example: "Shows working" worth 3 points.
class RubricCriterion(BaseModel):
    id: int
    criterion: str
    max_points: float


# What Laravel sends to /mark.
# URLs are signed, so this service needs no login or storage access.
class MarkRequest(BaseModel):
    submission_id: int
    submission_url: str
    memo_url: str
    total_points: float
    rubric_criteria: list[RubricCriterion] = []


# What this service sends back to Laravel.
# Matches Laravel's MarkingResult class field by field.
class MarkResponse(BaseModel):
    score: float | None = None
    confidence: float = Field(ge=0, le=100)
    feedback: str
    criterion_scores: dict[str, float] = {}
    unreadable: bool = False
    provisional: bool = False
