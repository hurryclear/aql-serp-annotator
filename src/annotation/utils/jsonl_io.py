from __future__ import annotations

import json
import logging
from pathlib import Path

from docs.adr.src.utils.path import make_pyl

logger = logging.getLogger(__name__)


def _ids_file(annotation_dir: Path) -> Path:
    return annotation_dir / f"{annotation_dir.name}.json"


def get_annotated_serp_ids(annotation_dir: Path) -> set[str]:
    path = _ids_file(annotation_dir)
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("serp_ids", []))


def save_serp_id(
    annotation_dir: Path,
    serp_id: str,
    provider: str, year: int, language: str,
) -> None:
    path = _ids_file(annotation_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "provider": provider,
            "year": year,
            "language": language,
            "question_type": "qphrase",
            "validated_count": 0,
            "serp_ids": [],
        }

    if serp_id not in data["serp_ids"]:
        data["serp_ids"].append(serp_id)
        data["validated_count"] = len(data["serp_ids"])

    path.write_text(json.dumps(data, indent=2) + "\n")
