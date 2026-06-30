def test_register_and_login(client):
    reg = client.post("/auth/register", json={"email": "a@example.com", "username": "alice", "password": "secret12"})
    assert reg.status_code == 200

    login = client.post("/auth/login", json={"username": "alice", "password": "secret12"})
    assert login.status_code == 200
    assert "access_token" in login.json()
