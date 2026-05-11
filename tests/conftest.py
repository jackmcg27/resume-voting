import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import sessions

# Smallest valid-enough PDF for upload tests — the server stores whatever bytes it receives
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n%%EOF"


@pytest.fixture(autouse=True)
def clear_store():
    """Reset all in-memory state before and after every test."""
    sessions.clear()
    yield
    sessions.clear()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient with UPLOAD_DIR redirected to a temp directory."""
    monkeypatch.setattr("app.routers.resumes.UPLOAD_DIR", tmp_path)
    return TestClient(app)


@pytest.fixture
def session_code(client):
    resp = client.post("/api/sessions", json={"name": "Test Session"})
    assert resp.status_code == 200
    return resp.json()["code"]


@pytest.fixture
def resume_id(client, session_code):
    resp = client.post(
        f"/api/sessions/{session_code}/resumes",
        files={"file": ("alice.pdf", MINIMAL_PDF, "application/pdf")},
    )
    assert resp.status_code == 200
    return resp.json()["id"]
