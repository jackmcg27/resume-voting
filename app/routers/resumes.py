import json
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..config import UPLOAD_DIR
from ..models import Resume
from ..store import sessions, broadcast_state

router = APIRouter(tags=["resumes"])


def _read_meta(stem: str) -> str:
    meta_path = UPLOAD_DIR / f"{stem}.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text()).get("original_name", f"{stem}.pdf")
        except Exception:
            pass
    return f"{stem}.pdf"


def _write_meta(stem: str, original_name: str) -> None:
    (UPLOAD_DIR / f"{stem}.json").write_text(json.dumps({"original_name": original_name}))


@router.get("/api/uploads")
async def list_uploads():
    files = []
    for pdf in sorted(UPLOAD_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = pdf.stat()
        files.append({
            "filename": pdf.name,
            "original_name": _read_meta(pdf.stem),
            "size": stat.st_size,
            "uploaded_at": stat.st_mtime,
        })
    return files


@router.post("/api/sessions/{code}/resumes")
async def upload_resume(code: str, file: UploadFile = File(...)):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    resume_id = str(uuid.uuid4())
    filename = f"{resume_id}.pdf"
    original_name = file.filename or "resume.pdf"

    (UPLOAD_DIR / filename).write_bytes(await file.read())
    _write_meta(resume_id, original_name)

    session.resumes.append(Resume(id=resume_id, filename=filename, original_name=original_name))
    await broadcast_state(code)
    return {"id": resume_id}


class AddFromServerBody(BaseModel):
    filename: str


@router.post("/api/sessions/{code}/resumes/from-server")
async def add_from_server(code: str, body: AddFromServerBody):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    path = UPLOAD_DIR / body.filename
    if not path.exists():
        raise HTTPException(404, "File not found on server")

    if any(r.filename == body.filename for r in session.resumes):
        raise HTTPException(400, "Already in session queue")

    resume_id = path.stem
    original_name = _read_meta(resume_id)

    session.resumes.append(Resume(id=resume_id, filename=body.filename, original_name=original_name))
    await broadcast_state(code)
    return {"id": resume_id}


@router.delete("/api/sessions/{code}/resumes/{resume_id}")
async def delete_resume(code: str, resume_id: str):
    session = sessions.get(code)
    if not session:
        raise HTTPException(404, "Session not found")

    session.resumes = [r for r in session.resumes if r.id != resume_id]
    if session.active_resume_id == resume_id:
        session.active_resume_id = None
        session.voting_open = False

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
