import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from config import config
from main import app
from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature

# a real line of the test question file, so the provider/language/year lookup works
RECORD = json.loads(config.question_serps_path.open(encoding="utf-8").readline())
SERP_ID = UUID(RECORD["serp"])


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
    # clean up, so every test starts with this SERP unannotated
    with SessionLocal() as s:
        s.query(Feature).filter_by(serp_id=SERP_ID).delete()
        s.query(Annotation).filter_by(serp_id=SERP_ID).delete()
        s.commit()


def post(client, serp_id, features):
    return client.post("/annotations", json={"serp_id": str(serp_id), "created_by": "test", "features": features})


def test_save_takes_provider_language_year_from_the_question_file(client):
    assert post(client, SERP_ID, [{"feature_type": "kp"}, {"feature_type": "kp"}]).status_code == 201
    with SessionLocal() as s:
        a = s.get(Annotation, SERP_ID)
        assert (a.provider, a.language, a.year) == (RECORD["provider"], RECORD["language"], RECORD["year"])
        assert s.query(Feature).filter_by(serp_id=SERP_ID).count() == 2


def test_second_save_is_409_and_unknown_serp_is_404(client):
    assert post(client, SERP_ID, []).status_code == 201  # "No features" is a real answer
    assert post(client, SERP_ID, []).status_code == 409
    assert post(client, "00000000-0000-0000-0000-000000000000", []).status_code == 404


def test_wrong_body_is_422(client):
    # FastAPI checks the body against AnnotationInput before our code runs
    assert client.post("/annotations", json={"serp_id": "not-a-uuid"}).status_code == 422
