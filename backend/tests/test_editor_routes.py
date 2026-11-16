import json
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from config import config
from main import app
from src.annotation.service import PROVIDER_NAMES, feature_id
from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature
from src.entities.parser import Parser
from src.serp.service import get_serp_html, save_serp_html
from utils.html_utils import number_elements

# the second line of the test question file (the create-route tests use the first)
RECORD = json.loads(config.question_serps_path.open(encoding="utf-8").readlines()[1])
SERP_ID = UUID(RECORD["serp"])
PAGE = "<html><body><div>a</div><div>b</div><div>c</div></body></html>"  # divs are nodes 3, 4, 5


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def annotated(client):
    save_serp_html(SERP_ID, number_elements(PAGE))
    response = client.post("/annotations", json={
        "serp_id": str(SERP_ID),
        "created_by": "test",
        "features": [{"feature_type": "kp", "node": 5}, {"feature_type": "ads", "node": 3}],
    })
    assert response.status_code == 201
    yield
    with SessionLocal() as s:
        s.query(Feature).filter_by(serp_id=SERP_ID).delete()
        s.query(Annotation).filter_by(serp_id=SERP_ID).delete()
        s.query(Parser).delete()
        s.commit()


def test_read_returns_features_in_page_order_with_their_elements(client):
    body = client.get(f"/annotations/{SERP_ID}").json()
    assert [(f["feature_type"], f["node"]) for f in body["features"]] == [("ads", 3), ("kp", 5)]
    assert body["features"][1]["id"] == str(feature_id(SERP_ID, "kp", 1))
    assert body["provider"] == PROVIDER_NAMES[RECORD["provider"]] and body["year"] == RECORD["year"]
    assert body["ground_truth"] is False


def test_groups_count_by_provider_and_year(client):
    groups = client.get("/annotations/groups").json()
    mine = [g for g in groups if g["provider_id"] == RECORD["provider"] and g["year"] == RECORD["year"]]
    assert mine == [{
        "provider_id": RECORD["provider"], "provider": PROVIDER_NAMES[RECORD["provider"]], "year": RECORD["year"],
        "annotations": 1, "ground_truth": 0,
    }]


def test_groups_are_ordered_by_provider_then_year(client):
    groups = client.get("/annotations/groups").json()
    keys = [(g["provider"], g["year"]) for g in groups]
    assert keys == sorted(keys)


def test_unknown_serp_is_404(client):
    assert client.get("/annotations/00000000-0000-0000-0000-000000000000").status_code == 404
