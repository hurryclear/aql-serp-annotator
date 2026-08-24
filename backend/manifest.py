"""read manifest file
placeholder
"""
import json
from uuid import UUID
from config import Config

config = Config()


def search_manifest(provider: str, language: str, year: int) -> list[UUID]:
    ids: list[UUID] = []
    with config.manifest_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record["provider"] == provider and record["language"] == language and record["year"] == year:
                ids.append(UUID(record["serp_id"]))
    return ids
