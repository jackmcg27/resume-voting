import csv
import io

import pytest

from tests.conftest import MINIMAL_PDF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _full_workflow(client, session_code, resume_id, votes: dict):
    """Activate a resume, open voting, submit votes, and reveal results."""
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    for name, score in votes.items():
        client.post(
            f"/api/sessions/{session_code}/vote",
            json={"panelist_name": name, "score": score},
        )
    client.post(f"/api/sessions/{session_code}/reveal")


# ---------------------------------------------------------------------------
# Open / close voting
# ---------------------------------------------------------------------------

def test_open_voting(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    resp = client.post(f"/api/sessions/{session_code}/voting/open")
    assert resp.status_code == 200
    assert client.get(f"/api/sessions/{session_code}").json()["voting_open"] is True


def test_open_voting_requires_active_resume(client, session_code):
    resp = client.post(f"/api/sessions/{session_code}/voting/open")
    assert resp.status_code == 400


def test_close_voting(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    resp = client.post(f"/api/sessions/{session_code}/voting/close")
    assert resp.status_code == 200
    assert client.get(f"/api/sessions/{session_code}").json()["voting_open"] is False


# ---------------------------------------------------------------------------
# Submitting votes
# ---------------------------------------------------------------------------

def test_submit_vote_accepted(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    resp = client.post(
        f"/api/sessions/{session_code}/vote",
        json={"panelist_name": "Alice", "score": 4},
    )
    assert resp.status_code == 200


@pytest.mark.parametrize("score", [0, 6, -1, 100])
def test_submit_vote_rejects_invalid_score(client, session_code, resume_id, score):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    resp = client.post(
        f"/api/sessions/{session_code}/vote",
        json={"panelist_name": "Alice", "score": score},
    )
    assert resp.status_code == 400


def test_submit_vote_rejected_when_voting_closed(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    resp = client.post(
        f"/api/sessions/{session_code}/vote",
        json={"panelist_name": "Alice", "score": 4},
    )
    assert resp.status_code == 400


def test_later_vote_overwrites_earlier_vote(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    client.post(f"/api/sessions/{session_code}/vote", json={"panelist_name": "Alice", "score": 2})
    client.post(f"/api/sessions/{session_code}/vote", json={"panelist_name": "Alice", "score": 5})
    client.post(f"/api/sessions/{session_code}/reveal")

    resume = next(
        r for r in client.get(f"/api/sessions/{session_code}").json()["resumes"]
        if r["id"] == resume_id
    )
    assert resume["votes"]["Alice"] == 5


# ---------------------------------------------------------------------------
# Blind voting — votes must stay hidden until reveal
# ---------------------------------------------------------------------------

def test_votes_hidden_while_voting_open(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    client.post(f"/api/sessions/{session_code}/vote", json={"panelist_name": "Alice", "score": 5})

    resume = next(
        r for r in client.get(f"/api/sessions/{session_code}").json()["resumes"]
        if r["id"] == resume_id
    )
    assert resume["votes"] == {}
    assert resume["vote_count"] == 1  # count is always visible


def test_votes_visible_after_reveal(client, session_code, resume_id):
    _full_workflow(client, session_code, resume_id, {"Alice": 5, "Bob": 3})

    resume = next(
        r for r in client.get(f"/api/sessions/{session_code}").json()["resumes"]
        if r["id"] == resume_id
    )
    assert resume["votes"] == {"Alice": 5, "Bob": 3}
    assert resume["average"] == 4.0


# ---------------------------------------------------------------------------
# Reveal
# ---------------------------------------------------------------------------

def test_reveal_marks_resume_reviewed(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/reveal")

    resume = next(
        r for r in client.get(f"/api/sessions/{session_code}").json()["resumes"]
        if r["id"] == resume_id
    )
    assert resume["revealed"] is True
    assert resume["status"] == "reviewed"


def test_reveal_closes_voting(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    client.post(f"/api/sessions/{session_code}/reveal")
    assert client.get(f"/api/sessions/{session_code}").json()["voting_open"] is False


# ---------------------------------------------------------------------------
# Deactivate
# ---------------------------------------------------------------------------

def test_deactivate_clears_active_resume(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/deactivate")
    assert client.get(f"/api/sessions/{session_code}").json()["active_resume_id"] is None


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def test_get_results_returns_reviewed_resumes(client, session_code, resume_id):
    _full_workflow(client, session_code, resume_id, {"Alice": 3, "Bob": 5})

    rows = client.get(f"/api/sessions/{session_code}/results").json()
    assert len(rows) == 1
    assert rows[0]["average"] == 4.0
    assert rows[0]["votes"] == {"Alice": 3, "Bob": 5}


def test_get_results_sorted_by_average_descending(client, session_code):
    r1 = client.post(
        f"/api/sessions/{session_code}/resumes",
        files={"file": ("low.pdf", MINIMAL_PDF, "application/pdf")},
    ).json()["id"]
    r2 = client.post(
        f"/api/sessions/{session_code}/resumes",
        files={"file": ("high.pdf", MINIMAL_PDF, "application/pdf")},
    ).json()["id"]

    _full_workflow(client, session_code, r1, {"Alice": 2})
    _full_workflow(client, session_code, r2, {"Alice": 5})

    results = client.get(f"/api/sessions/{session_code}/results").json()
    assert results[0]["name"] == "high.pdf"
    assert results[1]["name"] == "low.pdf"


def test_get_results_excludes_unrevealed(client, session_code, resume_id):
    client.post(f"/api/sessions/{session_code}/resumes/{resume_id}/activate")
    client.post(f"/api/sessions/{session_code}/voting/open")
    client.post(f"/api/sessions/{session_code}/vote", json={"panelist_name": "Alice", "score": 4})
    # No reveal

    rows = client.get(f"/api/sessions/{session_code}/results").json()
    assert rows == []


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def test_export_csv_headers_and_row(client, session_code, resume_id):
    _full_workflow(client, session_code, resume_id, {"Alice": 4, "Bob": 2})

    resp = client.get(f"/api/sessions/{session_code}/export.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]

    rows = list(csv.reader(io.StringIO(resp.text)))
    assert rows[0] == ["Candidate", "Alice", "Bob", "Average"]
    assert rows[1][0] == "alice.pdf"
    assert float(rows[1][3]) == 3.0


def test_export_csv_handles_missing_votes(client, session_code):
    r1 = client.post(
        f"/api/sessions/{session_code}/resumes",
        files={"file": ("alice.pdf", MINIMAL_PDF, "application/pdf")},
    ).json()["id"]
    r2 = client.post(
        f"/api/sessions/{session_code}/resumes",
        files={"file": ("bob.pdf", MINIMAL_PDF, "application/pdf")},
    ).json()["id"]

    # Alice only votes on r1; Bob only votes on r2
    _full_workflow(client, session_code, r1, {"Alice": 5})
    _full_workflow(client, session_code, r2, {"Bob": 3})

    rows = list(csv.reader(io.StringIO(
        client.get(f"/api/sessions/{session_code}/export.csv").text
    )))
    # Header: Candidate, Alice, Bob, Average
    assert rows[0] == ["Candidate", "Alice", "Bob", "Average"]
    # r1 has no Bob vote — cell should be empty
    alice_row = next(r for r in rows[1:] if r[0] == "alice.pdf")
    assert alice_row[2] == ""


def test_export_csv_session_not_found(client):
    assert client.get("/api/sessions/NOPE99/export.csv").status_code == 404
