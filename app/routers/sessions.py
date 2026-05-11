from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import Session, session_view
from ..store import sessions, generate_session_code

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class CreateSessionBody(BaseModel):
    name: str = ""


@router.post("")
async def create_session(body: CreateSessionBody):
    code = generate_session_code()
    while code in sessions:
        code = generate_session_code()
    sessions[code] = Session(code=code, name=body.name.strip())
    return {"code": code}


@router.get("/{code}")
async def get_session(code: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")
    return session_view(session)
