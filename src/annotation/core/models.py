from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AnnotationSession:
    provider: str
    year: int
    language: str
    batch_size: int
    serp_ids: list[str] = field(default_factory=list)
    output_dir: Path = field(default_factory=Path)
    total_cached: int = 0
    already_annotated: int = 0
    remaining: int = 0
