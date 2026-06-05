from fastapi import APIRouter, Depends, HTTPException, Request
import httpx

from ..store import sessions

router = APIRouter(tags=["admin"])

_AUTH_SERVER = "http://localhost:3001"


async def require_admin(request: Request) -> dict:
    """Verify the session cookie against the Better Auth server and check GitLab group membership."""
    cookie = request.headers.get("cookie", "")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_AUTH_SERVER}/verify-admin",
                headers={"cookie": cookie},
                timeout=5.0,
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth server unavailable")

    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if resp.status_code == 403:
        raise HTTPException(status_code=403, detail=resp.json().get("reason", "Forbidden"))
    if not resp.is_success:
        raise HTTPException(status_code=500, detail="Auth check failed")

    return resp.json()["user"]


@router.get("/api/admin/sessions")
async def list_sessions(_admin: dict = Depends(require_admin)):
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
