import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..config import UPLOAD_DIR
from ..models import Resume
from ..store import sessions, broadcast_state

router = APIRouter(tags=["resumes"])


@router.post("/api/sessions/{code}/resumes")
async def upload_resume(code: str, file: UploadFile = File(...)):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    resume_id = str(uuid.uuid4())
    filename = f"{resume_id}.pdf"
    original_name = file.filename or "resume.pdf"

    (UPLOAD_DIR / filename).write_bytes(await file.read())

    session.resumes.append(Resume(id=resume_id, filename=filename, original_name=original_name))
    await broadcast_state(code)
    return {"id": resume_id}


class UpdateResumeBody(BaseModel):
    candidate_name: str


@router.patch("/api/sessions/{code}/resumes/{resume_id}")
async def update_resume(code: str, resume_id: str, body: UpdateResumeBody):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")
    resume = next((r for r in session.resumes if r.id == resume_id), None)
    if not resume:
        raise HTTPException(404, "Resume not found")
    resume.candidate_name = body.candidate_name
    await broadcast_state(code)
    return {"ok": True}


@router.delete("/api/sessions/{code}/resumes/{resume_id}")
async def delete_resume(code: str, resume_id: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    session.resumes = [r for r in session.resumes if r.id != resume_id]
    if session.active_resume_id == resume_id:
        session.active_resume_id = None
        session.voting_open = False

    pdf_path = UPLOAD_DIR / f"{resume_id}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()

    await broadcast_state(code)
    return {"ok": True}


@router.post("/api/sessions/{code}/resumes/{resume_id}/activate")
async def activate_resume(code: str, resume_id: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")
    if not any(r.id == resume_id for r in session.resumes):
        raise HTTPException(404, "Resume not found")

    session.active_resume_id = resume_id
    session.voting_open = False
    await broadcast_state(code)
    return {"ok": True}


@router.get("/uploads/{filename}")
async def serve_pdf(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(str(path), media_type="application/pdf")
