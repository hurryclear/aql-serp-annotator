from __future__ import annotations

from uuid import UUID
from dataclasses import dataclass, field


@dataclass
class Answer:
    text: str
    source: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"text": self.text, "source": self.source}

    @classmethod
    def from_dict(cls, d: dict) -> Answer:
        return cls(text=d["text"], source=d.get("source", ""))


@dataclass
class FeatureBlockData:
    id: UUID
    rank: int
    content: str
    answers: list[Answer] = field(default_factory=list)


@dataclass
class FeatureBlock:
    id: UUID
    serp_id: UUID
    category: str
    provider_id: UUID
    parser_id: UUID
    year: int
    rank: int
    content: str
    query: str | None = None
    xpath: str | None = None
    answers: list[Answer] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {
            "id": str(self.id),
            "serp_id": str(self.serp_id),
            "provider_id": str(self.provider_id),
            "parser_id": str(self.parser_id),
            "rank": self.rank,
            "category": self.category,
            "year": self.year,
            # "content": self.content,
        }
        if self.query is not None:
            d["question"] = self.query
        if self.answers:
            d["answers"] = [a.to_dict() for a in self.answers]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> FeatureBlock:
        return cls(
            id=UUID(d["id"]),
            serp_id=UUID(d["serp_id"]),
            category=d["category"],
            provider_id=UUID(d["provider_id"]),
            year=int(d["year"]),
            rank=int(d["rank"]),
            content=d.get("content", ""),
            parser_id=UUID(d["parser_id"]),
            query=d.get("query"),
            answers=[Answer.from_dict(a) for a in d.get("answers", [])],
        )
