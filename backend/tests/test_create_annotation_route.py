import json
import re
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from config import config
from main import app
from src.annotation.service import feature_id
from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature
from src.serp.service import get_serp_html, save_serp_html
from utils.html_utils import number_elements

# a real line of the test question file, so the provider/language/year lookup works
RECORD = json.loads(config.question_serps_path.open(encoding="utf-8").readline())
SERP_ID = UUID(RECORD["serp"])
# a tiny stand-in for the SERP's cached snapshot: html=1, body=2, the divs are 3, 4, 5
PAGE = "<html><body><div>first</div><div>second</div><div>third</div></body></html>"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def fresh_snapshot():
    # every test starts with a numbered, unmarked snapshot and no annotation
    save_serp_html(SERP_ID, number_elements(PAGE))
    yield
    with SessionLocal() as s:
        s.query(Feature).filter_by(serp_id=SERP_ID).delete()
        s.query(Annotation).filter_by(serp_id=SERP_ID).delete()
        s.commit()


def post(client, serp_id, features):
    return client.post("/annotations", json={"serp_id": str(serp_id), "created_by": "test", "features": features})


def test_save_takes_provider_language_year_from_the_question_file(client):
    assert post(client, SERP_ID, [{"feature_type": "kp", "node": 3}, {"feature_type": "kp", "node": 5}]).status_code == 201
    with SessionLocal() as s:
        a = s.get(Annotation, SERP_ID)
        assert (a.provider, a.language, a.year) == (RECORD["provider"], RECORD["language"], RECORD["year"])
        assert s.query(Feature).filter_by(serp_id=SERP_ID).count() == 2


def test_save_marks_types_and_the_page_order_gives_each_row_its_element(client):
    # clicked bottom-up: the lower panel first
    assert post(client, SERP_ID, [{"feature_type": "kp", "node": 5}, {"feature_type": "kp", "node": 3}]).status_code == 201
    html = get_serp_html(SERP_ID)
    assert '<div aqlqa-node="3" aqlqa-sf-type="kp">first</div>' in html
    assert '<div aqlqa-node="4">second</div>' in html
    assert '<div aqlqa-node="5" aqlqa-sf-type="kp">third</div>' in html

    # the link: the n-th "kp" element in page order is the row with id uuid5(serp:kp:n)
    with SessionLocal() as s:
        ids = {row.id for row in s.query(Feature).filter_by(serp_id=SERP_ID)}
    assert re.findall(r'aqlqa-node="(\d+)" aqlqa-sf-type="kp"', html) == ["3", "5"]
    assert ids == {feature_id(SERP_ID, "kp", n) for n in (1, 2)}


def test_second_save_is_409_and_unknown_serp_is_404(client):
    assert post(client, SERP_ID, []).status_code == 201  # "No features" is a real answer
    assert post(client, SERP_ID, []).status_code == 409
    assert post(client, "00000000-0000-0000-0000-000000000000", []).status_code == 404


def test_unknown_element_is_refused_and_nothing_is_saved(client):
    assert post(client, SERP_ID, [{"feature_type": "kp", "node": 99}]).status_code == 422
    assert post(client, SERP_ID, []).status_code == 201  # the failed save left no annotation behind


def test_same_element_twice_is_refused(client):
    features = [{"feature_type": "kp", "node": 3}, {"feature_type": "ads", "node": 3}]
    assert post(client, SERP_ID, features).status_code == 422


def test_wrong_body_is_422(client):
    # FastAPI checks the body against AnnotationInput before our code runs
    assert client.post("/annotations", json={"serp_id": "not-a-uuid"}).status_code == 422
    assert post(client, SERP_ID, [{"feature_type": "kp"}]).status_code == 422  # no node
