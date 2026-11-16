"""the feature-type taxonomy (resources/serp_features_taxonomy.json)"""
from utils.resource_json_loader import FEATURE_TYPES

from src.feature_type.models import FeatureTypeOutput


def list_feature_types() -> list[FeatureTypeOutput]:
    # strip: one id in the file carries a trailing space, which must not reach feature.feature_type
    return [FeatureTypeOutput(id=t["id"].strip(), label=t["label"].strip()) for t in FEATURE_TYPES]
