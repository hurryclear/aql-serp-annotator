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


# POST /parsers: an xpath that works on this SERP becomes a new parser
class ParserInput(BaseModel):
    serp_id: UUID  # the SERP it was designed on: its blocks get linked
    feature_type: str
    xpath: str


class ParserOutput(BaseModel):
    id: UUID
    provider_id: str
    feature_type: str
    xpath: str
    created_at: datetime
    updated_at: datetime
    serps: int        # SERPs whose blocks are linked to it (feature.parser_id)
    years: list[int]  # the years of those SERPs: a parser can be reused across years


