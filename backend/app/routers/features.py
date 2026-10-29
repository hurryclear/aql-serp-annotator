from fastapi import APIRouter

from schemas import FeatureType
from feature_types import load_feature_types


router = APIRouter(prefix="/features", tags=["features"])


@router.get("/type")
def list_types() -> list[FeatureType]:
    return load_feature_types()
