"""read the candidate SERPs file: the curated set of SERPs that carts are drawn from (ADR 0005)"""
import json
from uuid import UUID
from config import config


def search_candidate_serps(provider: str, language: str, year: int) -> list[UUID]:
    ids: list[UUID] = []
    with config.candidate_serps_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record["provider"] == provider and record["language"] == language and record["year"] == year:
                ids.append(UUID(record["serp_id"]))
    return ids
