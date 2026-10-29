"""read the feature-type taxonomy: the categories an annotator can give a feature block"""
import json
from pathlib import Path

from schemas import FeatureType


TAXONOMY_PATH = Path(__file__).resolve().parent / "resources" / "serp_features_taxonomy.json"


def load_feature_types() -> list[FeatureType]:
    with TAXONOMY_PATH.open("r", encoding="utf-8") as f:
        categories = json.load(f)["categories"]
    # strip: one id in the file carries a trailing space, which must not reach feature.type
    return [FeatureType(id=c["id"].strip(), label=c["label"].strip()) for c in categories]
