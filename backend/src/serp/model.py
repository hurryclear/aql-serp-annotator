from uuid import UUID
from pydantic import BaseModel


class SerpSimple(BaseModel):
    serp_id: UUID
    query: str


class SerpCount(BaseModel):
    """Question SERPs for one provider/language/year, and how many are annotated."""
    total: int
    annotated: int


class Serp(BaseModel):
    serp_id: UUID
    query: str
    provider: str
    year: int
    language: str
    question_type: str
    matched: list[str]
