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
