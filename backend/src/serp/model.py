from uuid import UUID
from pydantic import BaseModel


class SerpSimple(BaseModel):
    serp_id: UUID
    query: str


class Serp(BaseModel):
    serp_id: UUID
    query: str
    provider: str
    year: int
    language: str
    question_type: str
    matched: list[str]
