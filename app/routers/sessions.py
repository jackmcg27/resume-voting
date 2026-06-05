from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import Session, session_view
from ..store import sessions, generate_session_code

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


VOTING_STYLES = {"stars", "thumbs", "numeric"}


class CreateSessionBody(BaseModel):
    name: str = ""
    voting_style: str = "stars"


@router.post("")
async def create_session(body: CreateSessionBody):
    if body.voting_style not in VOTING_STYLES:
        raise HTTPException(400, f"voting_style must be one of: {', '.join(sorted(VOTING_STYLES))}")
    code = generate_session_code()
    while code in sessions:
        code = generate_session_code()
    sessions[code] = Session(code=code, name=body.name.strip(), voting_style=body.voting_style)
    return {"code": code}


@router.get("/{code}")
async def get_session(code: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")
    return session_view(session)
