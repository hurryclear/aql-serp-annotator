def test_feature_types_lists_taxonomy(client):
    response = client.get("/features/type")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 26
    assert body[0] == {"id": "exploration_features", "label": "Exploration Features"}


def test_feature_type_ids_have_no_stray_spaces(client):
    ids = [t["id"] for t in client.get("/features/type").json()]
    assert "travel-related_features" in ids
    assert all(i == i.strip() for i in ids)
