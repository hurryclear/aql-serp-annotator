from pydantic import BaseModel


# only id + label: the workspace shows labels and saves ids
class FeatureTypeOutput(BaseModel):
    id: str
    label: str
