"""load the fixed .json files in resources/: they ship with the code and are the same in every environment.
human-friendly names (as entered on the landing page) -> canonical values used in the candidate SERPs file and Cart records"""
import json
from pathlib import Path

RESOURCES_PATH = Path(__file__).resolve().parent.parent / "resources"


def read_json(file_name: str):
    return json.loads((RESOURCES_PATH / file_name).read_text(encoding="utf-8"))


# read once, at import: the files only change together with the code
PROVIDERS: dict[str, str] = {
    provider["name"]: provider["id"] for provider in read_json("providers.json")["providers"]
}

LANGUAGES: dict[str, str] = {
    language["name"]: language["code"] for language in read_json("languages.json")["languages"]
}

# the full entries (id, label, description, remark), for GET /features/type
FEATURE_TYPES: list[dict] = read_json("serp_features_taxonomy.json")["categories"]
