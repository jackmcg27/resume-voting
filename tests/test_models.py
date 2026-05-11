"""Unit tests for the model serializers — no HTTP involved."""
from app.models import Panelist, Resume, Session, resume_view, session_view


def make_resume(**kwargs) -> Resume:
    defaults = {"id": "r1", "filename": "r1.pdf", "original_name": "alice.pdf"}
    defaults.update(kwargs)
    return Resume(**defaults)


class TestResumeView:
    def test_pending_when_not_active_and_not_revealed(self):
        view = resume_view(make_resume(), active_id=None)
        assert view["status"] == "pending"

    def test_active_when_id_matches_active_id(self):
        view = resume_view(make_resume(id="r1"), active_id="r1")
        assert view["status"] == "active"

    def test_reviewed_when_revealed(self):
        view = resume_view(make_resume(revealed=True), active_id=None)
        assert view["status"] == "reviewed"

    def test_votes_hidden_before_reveal(self):
        r = make_resume(votes={"Alice": 5, "Bob": 3}, revealed=False)
        view = resume_view(r, active_id=None)
        assert view["votes"] == {}
        assert view["average"] is None

    def test_votes_exposed_after_reveal(self):
        r = make_resume(votes={"Alice": 4, "Bob": 2}, revealed=True)
        view = resume_view(r, active_id=None)
        assert view["votes"] == {"Alice": 4, "Bob": 2}
        assert view["average"] == 3.0

    def test_vote_count_visible_before_reveal(self):
        r = make_resume(votes={"Alice": 5, "Bob": 3}, revealed=False)
        view = resume_view(r, active_id=None)
        assert view["vote_count"] == 2

    def test_average_rounds_to_two_decimal_places(self):
        r = make_resume(votes={"A": 1, "B": 2, "C": 2}, revealed=True)
        view = resume_view(r, active_id=None)
        assert view["average"] == 1.67

    def test_average_is_none_with_no_votes(self):
        view = resume_view(make_resume(), active_id=None)
        assert view["average"] is None

    def test_voters_list_is_sorted(self):
        r = make_resume(votes={"Zara": 5, "Alice": 3}, revealed=True)
        view = resume_view(r, active_id=None)
        assert view["voters"] == ["Alice", "Zara"]


class TestSessionView:
    def test_panelists_sorted_alphabetically(self):
        session = Session(code="ABC123")
        session.panelists["Zara"] = Panelist(name="Zara", client_id="c1")
        session.panelists["Alice"] = Panelist(name="Alice", client_id="c2")
        view = session_view(session)
        assert view["panelists"] == ["Alice", "Zara"]

    def test_includes_session_name(self):
        session = Session(code="ABC123", name="Backend Eng - May 2026")
        view = session_view(session)
        assert view["name"] == "Backend Eng - May 2026"

    def test_includes_expected_keys(self):
        view = session_view(Session(code="ABC123"))
        assert set(view.keys()) >= {"code", "name", "resumes", "panelists", "active_resume_id", "voting_open"}

    def test_resumes_serialized_in_order(self):
        session = Session(code="ABC123")
        session.resumes = [
            make_resume(id="r1", filename="r1.pdf", original_name="first.pdf"),
            make_resume(id="r2", filename="r2.pdf", original_name="second.pdf"),
        ]
        view = session_view(session)
        assert [r["id"] for r in view["resumes"]] == ["r1", "r2"]
