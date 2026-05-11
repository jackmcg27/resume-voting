import json

import pytest

from tests.conftest import MINIMAL_PDF


def test_upload_resume_adds_to_queue(client, session_code):
    resp = client.post(
        f"/api/sessions/{session_code}/resumes",
        files={"file": ("alice.pdf", MINIMAL_PDF, "application/pdf")},
    )
    assert resp.status_code == 200
    assert "id" in resp.json()

    resumes = client.get(f"/api/sessions/{session_code}").json()["resumes"]
    assert len(resumes) == 1
    assert resumes[0]["original_name"] == "alice.pdf"
    assert resumes[0]["status"] == "pending"


def test_upload_resume_session_not_found(client):
    resp = client.post(
        "/api/sessions/NOPE99/resumes",
        files={"file": ("x.pdf", MINIMAL_PDF, "application/pdf")},
    )
    assert resp.status_code == 404


def test_upload_multiple_resumes(client, session_code):
    for name in ("alice.pdf", "bob.pdf", "carol.pdf"):
        client.post(
            f"/api/sessions/{session_code}/resumes",
            files={"file": (name, MINIMAL_PDF, "application/pdf")},
        )
    resumes = client.get(f"/api/sessions/{session_code}").json()["resumes"]
    assert len(resumes) == 3


def test_add_from_server(client, session_code, tmp_path):
    # Seed a file directly in the upload dir (simulating a prior upload)
    (tmp_path / "abc123.pdf").write_bytes(MINIMAL_PDF)
    (tmp_path / "abc123.json").write_text(json.dumps({"original_name": "bob.pdf"}))

    resp = client.post(
        f"/api/sessions/{session_code}/resumes/from-server",
        json={"filename": "abc123.pdf"},
    )
    assert resp.status_code == 200

    resumes = client.get(f"/api/sessions/{session_code}").json()["resumes"]
    assert resumes[0]["original_name"] == "bob.pdf"


def test_add_from_server_file_not_found(client, session_code):
    resp = client.post(
        f"/api/sessions/{session_code}/resumes/from-server",
        json={"filename": "missing.pdf"},
    )
    assert resp.status_code == 404


def test_add_from_server_duplicate_rejected(client, session_code, resume_id):
    resp = client.post(
        f"/api/sessions/{session_code}/resumes/from-server",
        json={"filename": f"{resume_id}.pdf"},
    )
    assert resp.status_code == 400


def test_delete_resume_removes_from_queue(client, session_code, resume_id):
    client.delete(f"/api/sessions/{session_code}/resumes/{resume_id}")
    resumes = client.get(f"/api/sessions/{session_code}").json()["resumes"]
    assert len(resumes) == 0


def test_delete_active_resume_clears_state(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")

    client.delete(f"/api/sessions/{session_code}/resumes/{resume_id}")

    session = client.get(f"/api/sessions/{session_code}").json()
    assert session["active_resume_id"] is None
    assert session["voting_open"] is False


def test_activate_resume_sets_active(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    session = client.get(f"/api/sessions/{session_code}").json()
    assert session["active_resume_id"] == resume_id


def test_activate_resume_closes_open_voting(client, session_code):
    r1 = client.post(
        f"/api/sessions/{session_code}/resumes",
        files={"file": ("r1.pdf", MINIMAL_PDF, "application/pdf")},
    ).json()["id"]
    r2 = client.post(
        f"/api/sessions/{session_code}/resumes",
        files={"file": ("r2.pdf", MINIMAL_PDF, "application/pdf")},
    ).json()["id"]

    client.post(f"/api/sessions/{session_code}/resumes/{r1}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    client.post(f"/api/sessions/{session_code}/resumes/{r2}/activate")

    session = client.get(f"/api/sessions/{session_code}").json()
    assert session["voting_open"] is False


def test_activate_resume_not_found(client, session_code):
    resp = client.post(f"/api/sessions/{session_code}/resumes/nonexistent/activate")
    assert resp.status_code == 404


def test_serve_pdf_returns_content(client, session_code, resume_id):
    resp = client.get(f"/uploads/{resume_id}.pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content == MINIMAL_PDF


def test_serve_pdf_not_found(client):
    assert client.get("/uploads/doesnotexist.pdf").status_code == 404


def test_list_uploads(client, session_code, resume_id):
    resp = client.get("/api/uploads")
    assert resp.status_code == 200
    files = resp.json()
    assert len(files) == 1
    assert files[0]["original_name"] == "alice.pdf"
    assert files[0]["size"] == len(MINIMAL_PDF)
    assert "uploaded_at" in files[0]


def test_list_uploads_sorted_newest_first(client, session_code, tmp_path):
    # Create files with different mtimes using direct filesystem writes
    for i, name in enumerate(("old.pdf", "new.pdf")):
        p = tmp_path / f"file{i}.pdf"
        p.write_bytes(MINIMAL_PDF)
        (tmp_path / f"file{i}.json").write_text(json.dumps({"original_name": name}))
        import os
        os.utime(p, (i * 1000, i * 1000))

    files = client.get("/api/uploads").json()
    assert files[0]["original_name"] == "new.pdf"
