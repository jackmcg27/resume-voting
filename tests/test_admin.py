from tests.conftest import MINIMAL_PDF


def test_list_sessions_empty(client):
    resp = client.get("/api/admin/sessions")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_sessions_returns_all(client):
    client.post("/api/sessions", json={"name": "Session A"})
    client.post("/api/sessions", json={"name": "Session B"})

    sessions = client.get("/api/admin/sessions").json()
    assert len(sessions) == 2
    names = {s["name"] for s in sessions}
    assert names == {"Session A", "Session B"}


def test_list_sessions_includes_expected_fields(client):
    client.post("/api/sessions", json={"name": "Backend Eng - May 2026"})
    session = client.get("/api/admin/sessions").json()[0]

    assert session["name"] == "Backend Eng - May 2026"
    assert len(session["code"]) == 6
    assert "panelist_count" in session
    assert "resume_count" in session
    assert "reviewed_count" in session
    assert "voting_open" in session


def test_list_sessions_counts_resumes(client):
    code = client.post("/api/sessions", json={"name": "S"}).json()["code"]
    for name in ("a.pdf", "b.pdf"):
        client.post(
            f"/api/sessions/{code}/resumes",
            files={"file": (name, MINIMAL_PDF, "application/pdf")},
        )

    session = next(
        s for s in client.get("/api/admin/sessions").json()
        if s["code"] == code
    )
    assert session["resume_count"] == 2
    assert session["reviewed_count"] == 0


def test_list_sessions_counts_reviewed(client):
    code = client.post("/api/sessions", json={"name": "S"}).json()["code"]
    r = client.post(
        f"/api/sessions/{code}/resumes",
        files={"file": ("x.pdf", MINIMAL_PDF, "application/pdf")},
    ).json()["id"]
    client.post(f"/api/sessions/{code}/resumes/{r}/activate")
    client.post(f"/api/sessions/{code}/voting/open")
    client.post(f"/api/sessions/{code}/vote", json={"panelist_name": "Alice", "score": 4})
    client.post(f"/api/sessions/{code}/reveal")

    session = next(s for s in client.get("/api/admin/sessions").json() if s["code"] == code)
    assert session["reviewed_count"] == 1


def test_list_sessions_sorted_by_reviewed_count_descending(client):
    code_a = client.post("/api/sessions", json={"name": "A"}).json()["code"]
    code_b = client.post("/api/sessions", json={"name": "B"}).json()["code"]

    # Review one resume in B, none in A
    r = client.post(
        f"/api/sessions/{code_b}/resumes",
        files={"file": ("x.pdf", MINIMAL_PDF, "application/pdf")},
    ).json()["id"]
    client.post(f"/api/sessions/{code_b}/resumes/{r}/activate")
    client.post(f"/api/sessions/{code_b}/voting/open")
    client.post(f"/api/sessions/{code_b}/vote", json={"panelist_name": "Alice", "score": 4})
    client.post(f"/api/sessions/{code_b}/reveal")

    sessions = client.get("/api/admin/sessions").json()
    assert sessions[0]["name"] == "B"
    assert sessions[1]["name"] == "A"
