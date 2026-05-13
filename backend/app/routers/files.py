"""File upload + serve."""
import os
import uuid
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Response

from ..config import MIME_BY_EXT, APP_NAME, FRONTEND_URL
from ..db import db
from ..security import require_admin
from ..storage import storage_put, storage_get

router = APIRouter(tags=["files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    ext = (file.filename or "bin").rsplit(".", 1)[-1].lower()
    if ext not in MIME_BY_EXT:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: images, PDF, DOC/DOCX, XLS/XLSX, DWG, TXT.",
        )
    content_type = MIME_BY_EXT[ext]
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 8MB)")
    file_id = uuid.uuid4().hex
    path = f"{APP_NAME}/uploads/{user['user_id']}/{file_id}.{ext}"
    result = await asyncio.to_thread(storage_put, path, data, content_type)
    canonical_path = result.get("path", path)
    await db.files.insert_one({
        "file_id": file_id,
        "storage_path": canonical_path,
        "original_filename": file.filename,
        "content_type": content_type,
        "size": result.get("size", len(data)),
        "uploaded_by": user["user_id"],
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    base = (FRONTEND_URL if FRONTEND_URL != "*" else os.environ.get("FRONTEND_URL", "")).rstrip("/")
    public_url = f"{base}/api/files/{canonical_path}"
    return {"file_id": file_id, "url": public_url, "path": canonical_path}


@router.get("/files/{path:path}")
async def serve_file(path: str):
    record = await db.files.find_one(
        {"storage_path": path, "is_deleted": False}, {"_id": 0},
    )
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    data, content_type = await asyncio.to_thread(storage_get, path)
    return Response(content=data, media_type=record.get("content_type") or content_type)
