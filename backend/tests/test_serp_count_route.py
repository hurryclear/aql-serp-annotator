import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from config import config
from main import app
from src.annotation.service import PROVIDER_NAMES
from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.serp.service import save_serp_html
from utils.html_utils import number_elements

# the third line of the test question file (the other route tests use the first two)
LINES = config.question_serps_path.open(encoding="utf-8").readlines()
RECORD = json.loads(LINES[2])
SERP_ID = UUID(RECORD["serp"])
# the start page's names for this record: "Google", "Simplified Chinese"
PARAMS = {
    "provider": PROVIDER_NAMES[RECORD["provider"]],
    "language": RECORD["language"].replace("_", " ").title(),
    "year": RECORD["year"],
}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def no_annotation():
    yield
    with SessionLocal() as s:
        s.query(Annotation).filter_by(serp_id=SERP_ID).delete()
        s.commit()


def test_total_counts_every_line_with_that_provider_language_year(client):
    expected = sum(
        1
        for record in map(json.loads, LINES)
        if (record["provider"], record["language"], record["year"])
        == (RECORD["provider"], RECORD["language"], RECORD["year"])
    )
    response = client.get("/serps/count", params=PARAMS)
    assert response.status_code == 200
    assert response.json()["total"] == expected


def test_saving_an_annotation_raises_the_annotated_count(client):
    before = client.get("/serps/count", params=PARAMS).json()["annotated"]
    save_serp_html(SERP_ID, number_elements("<html><body><div>a</div></body></html>"))
    saved = client.post("/annotations", json={"serp_id": str(SERP_ID), "created_by": "test", "features": []})
    assert saved.status_code == 201
    assert client.get("/serps/count", params=PARAMS).json()["annotated"] == before + 1


def test_a_choice_left_out_matches_every_value(client):
    same_provider = sum(1 for record in map(json.loads, LINES) if record["provider"] == RECORD["provider"])
    response = client.get("/serps/count", params={"provider": PARAMS["provider"]})
    assert response.status_code == 200
    assert response.json()["total"] == same_provider


def test_no_choices_counts_the_whole_file(client):
    assert client.get("/serps/count").json()["total"] == len(LINES)


def test_unknown_provider_is_a_422(client):
    response = client.get("/serps/count", params={**PARAMS, "provider": "Altavista"})
    assert response.status_code == 422
