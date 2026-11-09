import json
from uuid import UUID
from config import config


def save_serp_html(serp_id: UUID, html: str) -> None:
    serp_path = config.persistence.serp_path / f"{serp_id}.html"
    serp_path.write_text(html, encoding="utf-8")


def get_serp_html(serp_id: UUID) -> str | None:
    serp_path = config.persistence.serp_path / f"{serp_id}.html"
    if not serp_path.exists():
        return None
    return serp_path.read_text(encoding="utf-8")


def search_candidate_serps(provider: str, language: str, year: int) -> list[UUID]:
    ids: list[UUID] = []
    with config.candidate_serps_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if (
                record["provider"] == provider
                and record["language"] == language
                and record["year"] == year
            ):
                ids.append(UUID(record["serp_id"]))
    return ids
