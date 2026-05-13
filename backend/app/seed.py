"""Database indexes + seed data loaded at startup."""
import uuid
import logging
import asyncio
from datetime import datetime, timezone

from .config import (
    ADMIN_EMAIL, ADMIN_PASSWORD, TEST_CLIENT_EMAIL, TEST_CLIENT_PASSWORD,
    LOGIN_ATTEMPT_TTL_SECONDS,
)
from .db import db
from .security import hash_password, verify_password
from .storage import init_storage

logger = logging.getLogger("stonebridge.seed")

SEED_PROJECTS = [
    {
        "title": "Maple Ridge Residence",
        "category": "residential", "location": "Aspen, CO", "year": 2024,
        "description": "A four-bedroom mountain residence built on a sloped granite site, featuring exposed timber framing and floor-to-ceiling glazing.",
        "cover_image": "https://images.unsplash.com/photo-1710701455648-e85f21bf3a79?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
        "images": [], "featured": True,
    },
    {
        "title": "Northgate Commercial Tower",
        "category": "commercial", "location": "Denver, CO", "year": 2023,
        "description": "Twelve-story mixed-use commercial tower delivered three months ahead of schedule, with a focus on LEED Gold certification.",
        "cover_image": "https://images.unsplash.com/photo-1695067439143-81a61a8c904a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHw0fHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
        "images": [], "featured": True,
    },
    {
        "title": "The Linden Loft Renovation",
        "category": "renovation", "location": "Boulder, CO", "year": 2024,
        "description": "Full gut renovation of a 1920s warehouse loft. Restored original brickwork paired with a custom-fabricated steel mezzanine.",
        "cover_image": "https://images.unsplash.com/photo-1681216868987-b7268753b81c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
        "images": [], "featured": True,
    },
    {
        "title": "Glasshouse on Cedar",
        "category": "residential", "location": "Portland, OR", "year": 2023,
        "description": "Single-family home defined by its dark steel frame and minimalist glass envelope nested into a forested lot.",
        "cover_image": "https://images.unsplash.com/photo-1756227584303-f1400daaa69d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwyfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
        "images": [], "featured": False,
    },
    {
        "title": "Steelyard Offices",
        "category": "commercial", "location": "Salt Lake City, UT", "year": 2022,
        "description": "Adaptive reuse of a former steel manufacturing plant into creative-class office headquarters across 48,000 sq ft.",
        "cover_image": "https://images.pexels.com/photos/946310/pexels-photo-946310.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "images": [], "featured": False,
    },
    {
        "title": "Terracotta Courtyard Home",
        "category": "renovation", "location": "Santa Fe, NM", "year": 2024,
        "description": "Adobe restoration with terracotta-tiled courtyard, hand-troweled lime plaster walls, and reclaimed vigas.",
        "cover_image": "https://images.pexels.com/photos/29895597/pexels-photo-29895597.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "images": [], "featured": False,
    },
]

SEED_CLIENT_PROJECTS = [
    {
        "client_email": TEST_CLIENT_EMAIL,
        "title": "Linden Loft Phase II", "project_type": "Renovation",
        "progress": 62, "status": "Framing",
        "next_milestone": "Mechanical rough-in inspection",
        "next_milestone_date": "2026-03-14",
        "notes": "Custom steel mezzanine fabricated off-site, install slated for next week.",
    },
    {
        "client_email": TEST_CLIENT_EMAIL,
        "title": "Cedar Ridge Garage Studio", "project_type": "Residential",
        "progress": 18, "status": "Planning",
        "next_milestone": "Permit submission",
        "next_milestone_date": "2026-02-28",
        "notes": "Drawings under review by structural engineer.",
    },
]


async def create_indexes():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.projects.create_index("project_id", unique=True)
    await db.inquiries.create_index("inquiry_id", unique=True)
    await db.sessions.create_index("session_token", unique=True)
    await db.client_projects.create_index("cp_id", unique=True)
    await db.files.create_index("file_id", unique=True)
    await db.files.create_index("storage_path", unique=True)
    await db.login_attempts.create_index("identifier")
    try:
        await db.login_attempts.drop_index("failed_at_1")
    except Exception:
        pass
    await db.login_attempts.create_index("failed_at", expireAfterSeconds=LOGIN_ATTEMPT_TTL_SECONDS)
    await db.client_documents.create_index("doc_id", unique=True)
    await db.client_documents.create_index("cp_id")
    await db.comments.create_index("comment_id", unique=True)
    await db.comments.create_index("cp_id")
    try:
        await db.login_attempts.delete_many({"failed_at": {"$type": "string"}})
    except Exception:
        pass


async def seed_users():
    admin = await db.users.find_one({"email": ADMIN_EMAIL})
    if not admin:
        await db.users.insert_one({
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": ADMIN_EMAIL, "name": "Stonebridge Admin",
            "password_hash": hash_password(ADMIN_PASSWORD),
            "role": "admin", "picture": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    elif not verify_password(ADMIN_PASSWORD, admin.get("password_hash", "")):
        await db.users.update_one(
            {"email": ADMIN_EMAIL},
            {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}},
        )
    if not await db.users.find_one({"email": TEST_CLIENT_EMAIL}):
        await db.users.insert_one({
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": TEST_CLIENT_EMAIL, "name": "Sarah Chen",
            "password_hash": hash_password(TEST_CLIENT_PASSWORD),
            "role": "client", "picture": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })


async def seed_data():
    if await db.projects.count_documents({}) == 0:
        await db.projects.insert_many([
            {**p, "project_id": f"prj_{uuid.uuid4().hex[:12]}"} for p in SEED_PROJECTS
        ])
    if await db.client_projects.count_documents({}) == 0:
        await db.client_projects.insert_many([
            {**cp, "cp_id": f"cp_{uuid.uuid4().hex[:12]}",
             "created_at": datetime.now(timezone.utc).isoformat()}
            for cp in SEED_CLIENT_PROJECTS
        ])

    if await db.client_documents.count_documents({}) == 0:
        test_cps = await db.client_projects.find(
            {"client_email": TEST_CLIENT_EMAIL}, {"_id": 0},
        ).to_list(10)
        sample = [
            {"title": "Construction Agreement (signed)", "file_type": "application/pdf"},
            {"title": "Schematic Drawings — Rev C", "file_type": "application/pdf"},
        ]
        docs = []
        for cp in test_cps:
            for sd in sample:
                docs.append({
                    "doc_id": f"doc_{uuid.uuid4().hex[:12]}",
                    "cp_id": cp["cp_id"],
                    "title": sd["title"],
                    "file_url": "https://www.africau.edu/images/default/sample.pdf",
                    "file_type": sd["file_type"],
                    "size": 245312,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                })
        if docs:
            await db.client_documents.insert_many(docs)

    if await db.comments.count_documents({}) == 0:
        test_cps = await db.client_projects.find(
            {"client_email": TEST_CLIENT_EMAIL}, {"_id": 0},
        ).to_list(10)
        admin_doc = await db.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "user_id": 1, "name": 1})
        if test_cps and admin_doc:
            await db.comments.insert_one({
                "comment_id": f"cmt_{uuid.uuid4().hex[:12]}",
                "cp_id": test_cps[0]["cp_id"],
                "author_user_id": admin_doc["user_id"],
                "author_name": admin_doc.get("name", "Stonebridge Admin"),
                "author_role": "admin",
                "body": "Welcome to your project dashboard! Use this thread to ask questions or share feedback — we'll respond within one business day.",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })


async def run_startup():
    await create_indexes()
    await seed_users()
    await seed_data()
    try:
        await asyncio.to_thread(init_storage)
    except Exception as e:
        logger.warning("Storage init at startup failed: %s", e)
