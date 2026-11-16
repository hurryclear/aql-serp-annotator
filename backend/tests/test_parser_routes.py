import json
from uuid import UUID, uuid5

import pytest
from fastapi.testclient import TestClient

from config import config
from main import app
from namespaces import NAMESPACE_FEATURE_PARSER
from src.annotation.service import feature_id
from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature
from src.entities.parser import Parser
from src.serp.service import save_serp_html
from utils.html_utils import number_elements

# from the test question file: A and B share a provider but not a year, C has another provider
RECORDS = [json.loads(line) for line in config.question_serps_path.open(encoding="utf-8")]
A = next(r for r in RECORDS[3:] if r["provider"] == RECORDS[3]["provider"])
B = next(r for r in RECORDS[3:] if r["provider"] == A["provider"] and r["year"] != A["year"])
C = next(r for r in RECORDS[3:] if r["provider"] != A["provider"])
SERP_A, SERP_B, SERP_C = (UUID(r["serp"]) for r in (A, B, C))

# nodes: html 1, body 2, div.kp 3, p 4, div.kp 5, div.ad 6; the first kp div and the ad are annotated
PAGE = ('<html><body><div class="kp">a</div><p>x</p>'
        '<div class="kp">b</div><div class="ad">c</div></body></html>')
FEATURES = [{"feature_type": "kp", "node": 3}, {"feature_type": "ads", "node": 6}]


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def annotated(client):
    for serp in (SERP_A, SERP_B, SERP_C):
        save_serp_html(serp, number_elements(PAGE))
        response = client.post("/annotations", json={"serp_id": str(serp), "created_by": "test", "features": FEATURES})
        assert response.status_code == 201
    yield
    with SessionLocal() as s:
        for serp in (SERP_A, SERP_B, SERP_C):
            s.query(Feature).filter_by(serp_id=serp).update({"parser_id": None})
            s.query(Feature).filter_by(serp_id=serp).delete()
            s.query(Annotation).filter_by(serp_id=serp).delete()
        s.query(Parser).delete()
        s.commit()


def try_(client, xpath, serp=SERP_A, feature_type="kp"):
    return client.post("/parsers/try", json={"serp_id": str(serp), "feature_type": feature_type, "xpath": xpath})


def save(client, xpath, serp=SERP_A, feature_type="kp"):
    return client.post("/parsers", json={"serp_id": str(serp), "feature_type": feature_type, "xpath": xpath})


def use(client, parser_id, serp):
    return client.put(f"/parsers/{parser_id}/serps/{serp}")


def parser_of(serp, feature_type="kp", n=1):
    with SessionLocal() as s:
        return s.get(Feature, feature_id(serp, feature_type, n)).parser_id


# ---- trying ----------------------------------------------------------------


def test_try_compares_found_elements_with_this_serps_annotated_blocks(client):
    # node 3 is the annotated kp, node 5 looks the same but isn't annotated
    assert try_(client, "//div[@class='kp']").json() == {
        "serp_id": str(SERP_A), "found": [3, 5], "matched": [3], "missed": [], "extra": [5],
    }


def test_text_results_count_as_nothing_found(client):
    assert try_(client, "//div/text()").json()["found"] == []


def test_invalid_xpath_is_422(client):
    response = try_(client, "//div[")
    assert response.status_code == 422 and "//div[" in response.json()["detail"]


# ---- a new parser ----------------------------------------------------------


def test_save_links_the_blocks_it_finds_on_this_serp_only(client):
    response = save(client, "//div[@class='kp']")
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(uuid5(NAMESPACE_FEATURE_PARSER, f"{A['provider']}:{A['year']}:kp:1"))
    assert (body["serps"], body["years"]) == (1, [A["year"]])
    assert parser_of(SERP_A) == UUID(body["id"])
    assert parser_of(SERP_B) is None  # another SERP isn't linked by saving


def test_a_parser_that_finds_no_annotated_block_here_is_refused(client):
    response = save(client, "//p")
    assert response.status_code == 422 and "finds none" in response.json()["detail"]


# ---- reusing an existing parser --------------------------------------------


