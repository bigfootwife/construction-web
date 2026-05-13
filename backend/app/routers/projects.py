"""Portfolio project endpoints."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from ..db import db
from ..models import ProjectIn, ProjectOut, ProjectPatch
from ..security import require_admin

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectOut])
async def list_projects(category: Optional[str] = None, featured: Optional[bool] = None):
    query: dict = {}
    if category and category != "all":
        query["category"] = category
    if featured is not None:
        query["featured"] = featured
    rows = await db.projects.find(query, {"_id": 0}).sort("year", -1).to_list(200)
    return [ProjectOut(**r) for r in rows]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str):
    doc = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**doc)


@router.post("", response_model=ProjectOut)
async def create_project(payload: ProjectIn, user: dict = Depends(require_admin)):
    pid = f"prj_{uuid.uuid4().hex[:12]}"
    doc = payload.model_dump()
    doc["project_id"] = pid
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    return ProjectOut(**doc)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, payload: ProjectPatch, user: dict = Depends(require_admin)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.projects.update_one({"project_id": project_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    doc = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    return ProjectOut(**doc)


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(require_admin)):
    result = await db.projects.delete_one({"project_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True, "deleted": project_id}
