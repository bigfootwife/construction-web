"""Client dashboard endpoints: projects, documents, comments."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends

from ..db import db
from ..models import (
    ClientProjectIn, ClientProjectOut,
    ClientDocumentIn, ClientDocumentOut,
    CommentIn, CommentOut,
)
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/client", tags=["client"])


# ----- Helpers -----
async def _cp_ids_for_email(email: str) -> List[str]:
    rows = await db.client_projects.find(
        {"client_email": email}, {"_id": 0, "cp_id": 1},
    ).to_list(500)
    return [r["cp_id"] for r in rows]


# ----- Projects -----
@router.get("/projects", response_model=List[ClientProjectOut])
async def my_projects(user: dict = Depends(get_current_user)):
    if user.get("role") == "admin":
        rows = await db.client_projects.find({}, {"_id": 0}).to_list(500)
    else:
        rows = await db.client_projects.find(
            {"client_email": user["email"]}, {"_id": 0},
        ).to_list(500)
    return [ClientProjectOut(**r) for r in rows]


@router.post("/projects", response_model=ClientProjectOut)
async def create_client_project(payload: ClientProjectIn, user: dict = Depends(require_admin)):
    cp_id = f"cp_{uuid.uuid4().hex[:12]}"
    doc = payload.model_dump()
    doc["cp_id"] = cp_id
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.client_projects.insert_one(doc)
    doc.pop("_id", None)
    return ClientProjectOut(**doc)


# ----- Documents -----
@router.get("/documents", response_model=List[ClientDocumentOut])
async def list_documents(cp_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query: dict = {}
    if user.get("role") == "admin":
        if cp_id:
            query["cp_id"] = cp_id
    else:
        allowed = await _cp_ids_for_email(user["email"])
        if cp_id:
            if cp_id not in allowed:
                raise HTTPException(status_code=403, detail="Not your project")
            query["cp_id"] = cp_id
        else:
            query["cp_id"] = {"$in": allowed}
    rows = await db.client_documents.find(query, {"_id": 0}).sort("uploaded_at", -1).to_list(500)
    return [ClientDocumentOut(**r) for r in rows]


@router.post("/documents", response_model=ClientDocumentOut)
async def create_document(payload: ClientDocumentIn, user: dict = Depends(require_admin)):
    cp = await db.client_projects.find_one({"cp_id": payload.cp_id}, {"_id": 0})
    if not cp:
        raise HTTPException(status_code=404, detail="Client project not found")
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    doc = payload.model_dump()
    doc["doc_id"] = doc_id
    doc["uploaded_at"] = datetime.now(timezone.utc).isoformat()
    await db.client_documents.insert_one(doc)
    doc.pop("_id", None)
    return ClientDocumentOut(**doc)


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(require_admin)):
    doc = await db.client_documents.find_one({"doc_id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    # Soft-delete the underlying blob (storage has no hard-delete API)
    file_url = doc.get("file_url") or ""
    if "/api/files/" in file_url:
        path = file_url.split("/api/files/", 1)[1]
        await db.files.update_one(
            {"storage_path": path},
            {"$set": {
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
    await db.client_documents.delete_one({"doc_id": doc_id})
    return {"ok": True, "deleted": doc_id}


# ----- Comments -----
async def _can_access_cp(user: dict, cp_id: str) -> bool:
    if user.get("role") == "admin":
        return True
    cp = await db.client_projects.find_one(
        {"cp_id": cp_id, "client_email": user["email"]}, {"_id": 0, "cp_id": 1},
    )
    return cp is not None


@router.get("/comments", response_model=List[CommentOut])
async def list_comments(cp_id: str, user: dict = Depends(get_current_user)):
    if not await _can_access_cp(user, cp_id):
        raise HTTPException(status_code=403, detail="Not your project")
    rows = await db.comments.find({"cp_id": cp_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return [CommentOut(**r) for r in rows]


@router.post("/comments", response_model=CommentOut)
async def create_comment(payload: CommentIn, user: dict = Depends(get_current_user)):
    if not await _can_access_cp(user, payload.cp_id):
        raise HTTPException(status_code=403, detail="Not your project")
    comment_id = f"cmt_{uuid.uuid4().hex[:12]}"
    doc = {
        "comment_id": comment_id,
        "cp_id": payload.cp_id,
        "author_user_id": user["user_id"],
        "author_name": user.get("name") or user.get("email"),
        "author_role": user.get("role", "client"),
        "body": payload.body.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.comments.insert_one(doc)
    doc.pop("_id", None)
    return CommentOut(**doc)


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user: dict = Depends(get_current_user)):
    cmt = await db.comments.find_one({"comment_id": comment_id}, {"_id": 0})
    if not cmt:
        raise HTTPException(status_code=404, detail="Comment not found")
    if user.get("role") != "admin" and cmt.get("author_user_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.comments.delete_one({"comment_id": comment_id})
    return {"ok": True, "deleted": comment_id}
