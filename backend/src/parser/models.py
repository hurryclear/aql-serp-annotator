from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# POST /parsers/try: run an xpath on one SERP
class TryInput(BaseModel):
    serp_id: UUID
    feature_type: str
    xpath: str


# what one xpath does on one SERP, compared with that SERP's annotated blocks of the type
class TryOutput(BaseModel):
    serp_id: UUID
    found: list[int]    # aqlqa-node numbers of everything the xpath finds
    matched: list[int]  # annotated and found
    missed: list[int]   # annotated, not found
    extra: list[int]    # found, not annotated


