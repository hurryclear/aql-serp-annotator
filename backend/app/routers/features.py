from fastapi import APIRouter

from schemas import FeatureType
from utils.resource_json_loader import FEATURE_TYPES


router = APIRouter(prefix="/features", tags=["features"])


# only id + label: the workspace shows labels and saves ids
@router.get("/type")
def list_types() -> list[FeatureType]:
    # strip: one id in the file carries a trailing space, which must not reach feature.type
    return [FeatureType(id=t["id"].strip(), label=t["label"].strip()) for t in FEATURE_TYPES]
