from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class FeatureInput(BaseModel):
    feature_type: str
    # the aqlqa-node number of the element the annotator marked, read off the page
    node: int = Field(ge=1)

class AnnotationInput(BaseModel):
    serp_id: UUID
    created_by: str
    # empty list = "No features": the SERP is still marked as done
    features: list[FeatureInput]


# PUT /annotations/{serp_id}: the editor sends the whole new feature list
class AnnotationReplace(BaseModel):
    features: list[FeatureInput]


# PATCH /annotations/{serp_id}: change single fields; only ground_truth for now
class AnnotationPatch(BaseModel):
    ground_truth: bool


class FeatureOutput(BaseModel):
    id: UUID
    feature_type: str
    # the marked element's aqlqa-node; None for annotations saved before marking existed
    node: int | None
    parser_id: UUID | None


class AnnotationOutput(BaseModel):
    serp_id: UUID
    provider_id: str
    provider: str  # display name, e.g. "google"
    language: str
    year: int
    created_by: str
    ground_truth: bool
    created_at: datetime
    updated_at: datetime
    features: list[FeatureOutput]  # in page order


# one row of GET /annotations?provider_id=…&year=…
class AnnotationSummary(BaseModel):
    serp_id: UUID
    year: int
    created_by: str
    ground_truth: bool
    feature_count: int


# one row of GET /annotations/groups
class AnnotationGroup(BaseModel):
    provider_id: str
    provider: str
    year: int
    annotations: int  # how many annotations (one per SERP) the group has
    ground_truth: int
