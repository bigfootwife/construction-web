"""Inquiry endpoints (public POST, admin GET)."""
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends

from ..db import db
from ..models import InquiryIn, InquiryOut
from ..security import require_admin
from ..mailer import send_inquiry_email

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


@router.post("", response_model=InquiryOut)
async def create_inquiry(payload: InquiryIn):
    inq_id = f"inq_{uuid.uuid4().hex[:12]}"
    doc = payload.model_dump()
    doc.update({
        "inquiry_id": inq_id,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.inquiries.insert_one(doc)
    doc.pop("_id", None)
    asyncio.create_task(send_inquiry_email(doc))
    return InquiryOut(**doc)


@router.get("", response_model=List[InquiryOut])
async def list_inquiries(user: dict = Depends(require_admin)):
    rows = await db.inquiries.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [InquiryOut(**r) for r in rows]
