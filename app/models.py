from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pydantic import BaseModel


@dataclass
class Panelist:
    name: str
    client_id: str


@dataclass
class Resume:
    id: str
    filename: str
    original_name: str
    votes: Dict[str, int] = field(default_factory=dict)
    revealed: bool = False


@dataclass
class Session:
    code: str
    name: str = ""
    resumes: List[Resume] = field(default_factory=list)
    panelists: Dict[str, Panelist] = field(default_factory=dict)
    active_resume_id: Optional[str] = None
    voting_open: bool = False


class VoteBody(BaseModel):
    panelist_name: str
    score: int


def resume_view(resume: Resume, active_id: Optional[str]) -> dict:
    if resume.revealed:
        status = "reviewed"
    elif resume.id == active_id:
        status = "active"
    else:
        status = "pending"

    votes = resume.votes if resume.revealed else {}
    average = (
        round(sum(resume.votes.values()) / len(resume.votes), 2)
        if resume.votes and resume.revealed
        else None
    )

    return {
        "id": resume.id,
        "filename": resume.filename,
        "original_name": resume.original_name,
        "status": status,
        "voters": sorted(resume.votes.keys()),
        "votes": votes,
        "vote_count": len(resume.votes),
        "revealed": resume.revealed,
        "average": average,
    }


def session_view(session: Session) -> dict:
    return {
        "code": session.code,
        "name": session.name,
        "resumes": [resume_view(r, session.active_resume_id) for r in session.resumes],
        "panelists": sorted(session.panelists.keys()),
        "active_resume_id": session.active_resume_id,
        "voting_open": session.voting_open,
    }
