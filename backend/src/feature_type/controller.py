from fastapi import APIRouter

from src.feature_type.models import FeatureTypeOutput
from src.feature_type.service import list_feature_types


router = APIRouter(prefix="/feature-types", tags=["feature types"])


@router.get("")
def list_all() -> list[FeatureTypeOutput]:
    return list_feature_types()
