from uuid import UUID
from pydantic import BaseModel

class FeatureInput(BaseModel):
    feature_type: str

class AnnotationInput(BaseModel):
    serp_id: UUID
    created_by: str
    # empty list = "No features": the SERP is still marked as done
    features: list[FeatureInput]
