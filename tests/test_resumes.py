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


def test_delete_resume_removes_from_queue(client, session_code, resume_id, tmp_path):
    client.delete(f"/api/sessions/{session_code}/resumes/{resume_id}")
    resumes = client.get(f"/api/sessions/{session_code}").json()["resumes"]
    assert len(resumes) == 0


def test_delete_resume_deletes_file(client, session_code, resume_id, tmp_path):
    pdf_path = tmp_path / f"{resume_id}.pdf"
    assert pdf_path.exists()
    client.delete(f"/api/sessions/{session_code}/resumes/{resume_id}")
    assert not pdf_path.exists()


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


def test_update_candidate_name(client, session_code, resume_id):
    resp = client.patch(
        f"/api/sessions/{session_code}/resumes/{resume_id}",
        json={"candidate_name": "Alice Smith"},
    )
    assert resp.status_code == 200

    resume = client.get(f"/api/sessions/{session_code}").json()["resumes"][0]
    assert resume["candidate_name"] == "Alice Smith"
    assert resume["original_name"] == "alice.pdf"


def test_update_candidate_name_session_not_found(client):
    resp = client.patch("/api/sessions/NOPE99/resumes/someid", json={"candidate_name": "X"})
    assert resp.status_code == 404


def test_update_candidate_name_resume_not_found(client, session_code):
    resp = client.patch(
        f"/api/sessions/{session_code}/resumes/nonexistent",
        json={"candidate_name": "X"},
    )
    assert resp.status_code == 404


def test_serve_pdf_returns_content(client, session_code, resume_id):
    resp = client.get(f"/uploads/{resume_id}.pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content == MINIMAL_PDF


def test_serve_pdf_not_found(client):
    assert client.get("/uploads/doesnotexist.pdf").status_code == 404
