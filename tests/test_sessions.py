def test_create_session_returns_six_char_code(client):
    resp = client.post("/api/sessions", json={"name": "May 2026"})
    assert resp.status_code == 200
    code = resp.json()["code"]
    assert len(code) == 6
    assert code.isalnum()


def test_create_session_stores_name(client):
    code = client.post("/api/sessions", json={"name": "Backend Eng"}).json()["code"]
    data = client.get(f"/api/sessions/{code}").json()
    assert data["name"] == "Backend Eng"


def test_create_session_trims_name_whitespace(client):
    code = client.post("/api/sessions", json={"name": "  Trimmed  "}).json()["code"]
    data = client.get(f"/api/sessions/{code}").json()
    assert data["name"] == "Trimmed"


def test_create_session_empty_name_allowed(client):
    resp = client.post("/api/sessions", json={})
    assert resp.status_code == 200


def test_multiple_sessions_have_unique_codes(client):
    codes = {
        client.post("/api/sessions", json={"name": f"S{i}"}).json()["code"]
        for i in range(5)
    }
    assert len(codes) == 5


def test_get_session_returns_initial_state(client, session_code):
    resp = client.get(f"/api/sessions/{session_code}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == session_code
    assert data["name"] == "Test Session"
    assert data["resumes"] == []
    assert data["panelists"] == []
    assert data["voting_open"] is False
    assert data["active_resume_id"] is None


def test_get_session_not_found(client):
    assert client.get("/api/sessions/NOPE99").status_code == 404
