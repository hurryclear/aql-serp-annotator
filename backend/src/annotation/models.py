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
