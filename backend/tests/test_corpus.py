def test_corpus_crud(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    create = client.post("/corpora", json={"name": "Docs", "description": "My docs"}, headers=headers)
    assert create.status_code == 200
    corpus_id = create.json()["id"]

    listing = client.get("/corpora", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    get_one = client.get(f"/corpora/{corpus_id}", headers=headers)
    assert get_one.status_code == 200

    delete = client.delete(f"/corpora/{corpus_id}", headers=headers)
    assert delete.status_code == 204
