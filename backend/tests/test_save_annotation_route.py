from uuid import uuid4

from persistence.database import SessionLocal
from persistence.models import Annotation


def test_save_annotation_route(client, cart_id):
    r = client.post(
        f"/serps/{uuid4()}/annotation",
        json={"cart_id": str(cart_id), "features": [{"type": "carousel", "content": "<div>x</div>", "xpath": None}]},
    )
    assert r.status_code == 204


def test_no_blocks_saves_empty_annotation(client, cart_id):
    serp_id = uuid4()
    r = client.post(f"/serps/{serp_id}/annotation", json={"cart_id": str(cart_id), "features": []})
    assert r.status_code == 204
    with SessionLocal() as session:
        assert session.get(Annotation, serp_id) is not None


def test_second_save_is_conflict(client, cart_id):
    serp_id, body = uuid4(), {"cart_id": str(cart_id), "features": []}
    client.post(f"/serps/{serp_id}/annotation", json=body)
    assert client.post(f"/serps/{serp_id}/annotation", json=body).status_code == 409


def test_unknown_cart_is_not_found(client):
    r = client.post(f"/serps/{uuid4()}/annotation", json={"cart_id": str(uuid4()), "features": []})
    assert r.status_code == 404
