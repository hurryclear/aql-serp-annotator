from __future__ import annotations

import json
import logging

from docs.adr.src.utils.path import DataPaths, make_pyl
from docs.adr.src.annotation.core.models import AnnotationSession
from docs.adr.src.annotation.utils.jsonl_io import get_annotated_serp_ids

logger = logging.getLogger(__name__)


def init_session(
    provider: str, year: int, language: str, batch_size: int,
) -> AnnotationSession:
    pyl = make_pyl(provider, year, language)
    output_dir = DataPaths.get_annotation_dir() / pyl

    ids_file = DataPaths.get_qserp_ids_file("prod", provider, year, language)
    if ids_file.exists():
        with ids_file.open("r", encoding="utf-8") as f:
            cached_data = json.load(f)
        cached_ids = cached_data.get("serp_ids", []) if isinstance(cached_data, dict) else cached_data
    else:
        logger.warning("No cached IDs file: %s", ids_file)
        cached_ids = []
    total_cached = len(cached_ids)

    annotated_ids = get_annotated_serp_ids(output_dir)
    already_annotated = len(annotated_ids)

    available = [sid for sid in cached_ids if sid not in annotated_ids]
    remaining = len(available)
    serp_ids = available[:batch_size]

    logger.info(
        "Session: %d cached, %d annotated, %d remaining, batch=%d",
        total_cached, already_annotated, remaining, len(serp_ids),
    )

    return AnnotationSession(
        provider=provider,
        year=year,
        language=language,
        batch_size=batch_size,
        serp_ids=serp_ids,
        output_dir=output_dir,
        total_cached=total_cached,
        already_annotated=already_annotated,
        remaining=remaining,
    )
