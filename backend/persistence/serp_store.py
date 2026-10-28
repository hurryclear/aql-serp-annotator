"""cleaned SERP HTML snapshots, stored as files next to the database (ADR 0004)"""
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
