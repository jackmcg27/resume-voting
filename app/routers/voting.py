import csv
import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models import VoteBody
from ..store import sessions, broadcast_state

router = APIRouter(prefix="/api/sessions", tags=["voting"])


@router.post("/{code}/voting/open")
async def open_voting(code: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.active_resume_id:
        raise HTTPException(400, "No active resume")
    session.voting_open = True
    await broadcast_state(code)
    return {"ok": True}


@router.post("/{code}/voting/close")
async def close_voting(code: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")
    session.voting_open = False
    await broadcast_state(code)
    return {"ok": True}


@router.post("/{code}/vote")
async def submit_vote(code: str, body: VoteBody):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.voting_open:
        raise HTTPException(400, "Voting is not open")
    if not 1 <= body.score <= 5:
        raise HTTPException(400, "Score must be between 1 and 5")

    resume = next((r for r in session.resumes if r.id == session.active_resume_id), None)
    if not resume:
        raise HTTPException(404, "Active resume not found")

    resume.votes[body.panelist_name] = body.score
    await broadcast_state(code)
    return {"ok": True}


@router.post("/{code}/reveal")
async def reveal_results(code: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    resume = next((r for r in session.resumes if r.id == session.active_resume_id), None)
    if resume:
        resume.revealed = True

    session.voting_open = False
    await broadcast_state(code)
    return {"ok": True}


@router.post("/{code}/deactivate")
async def deactivate(code: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    session.active_resume_id = None
    session.voting_open = False
    await broadcast_state(code)
    return {"ok": True}


@router.get("/{code}/results")
async def get_results(code: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    rows = []
    for resume in session.resumes:
        if resume.revealed and resume.votes:
            avg = sum(resume.votes.values()) / len(resume.votes)
            rows.append({
                "name": resume.original_name,
                "votes": resume.votes,
                "average": round(avg, 2),
            })

    rows.sort(key=lambda x: x["average"], reverse=True)
    return rows


@router.get("/{code}/export.csv")
async def export_csv(code: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    reviewed = [r for r in session.resumes if r.revealed]
    all_panelists = sorted({name for r in reviewed for name in r.votes})

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Candidate", *all_panelists, "Average"])

    for resume in reviewed:
        scores = [resume.votes.get(p, "") for p in all_panelists]
        voted = [v for v in scores if v != ""]
        avg = round(sum(voted) / len(voted), 2) if voted else ""
        writer.writerow([resume.original_name, *scores, avg])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="results-{code}.csv"'},
    )
