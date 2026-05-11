from fastapi import APIRouter

from ..store import sessions

router = APIRouter(tags=["admin"])


@router.get("/api/admin/sessions")
async def list_sessions():
    result = []
    for session in sessions.values():
        reviewed = [r for r in session.resumes if r.revealed]
        pending = [r for r in session.resumes if not r.revealed]
        result.append({
            "code": session.code,
            "name": session.name,
            "panelist_count": len(session.panelists),
            "resume_count": len(session.resumes),
            "reviewed_count": len(reviewed),
            "pending_count": len(pending),
            "voting_open": session.voting_open,
            "active_resume_id": session.active_resume_id,
        })
    result.sort(key=lambda s: s["reviewed_count"], reverse=True)
    return result
