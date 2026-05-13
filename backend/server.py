from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

import bcrypt
import jwt
import requests
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

# ---------- Config ----------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@stonebridge.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@1234")
TEST_CLIENT_EMAIL = "client@stonebridge.com"
TEST_CLIENT_PASSWORD = "Client@1234"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="Stonebridge Construction API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stonebridge")

# ---------- Utils ----------
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token", value=token, httponly=True,
        secure=True, samesite="none", max_age=7 * 24 * 3600, path="/",
    )

def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("session_token", path="/")

async def get_user_from_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        return user
    except Exception:
        return None

async def get_user_from_session(session_token: str) -> Optional[dict]:
    sess = await db.sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not sess:
        return None
    expires = sess.get("expires_at")
    if isinstance(expires, str):
        expires = datetime.fromisoformat(expires)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        return None
    user = await db.users.find_one({"user_id": sess["user_id"]}, {"_id": 0, "password_hash": 0})
    return user

async def get_current_user(request: Request) -> dict:
    # Cookies first
    token = request.cookies.get("access_token")
    if token:
        user = await get_user_from_token(token)
        if user:
            return user
    session_token = request.cookies.get("session_token")
    if session_token:
        user = await get_user_from_session(session_token)
        if user:
            return user
    # Bearer fallback
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        bearer = auth[7:]
        user = await get_user_from_token(bearer)
        if user:
            return user
        user = await get_user_from_session(bearer)
        if user:
            return user
    raise HTTPException(status_code=401, detail="Not authenticated")

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ---------- Models ----------
class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class GoogleSessionIn(BaseModel):
    session_id: str

class UserOut(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    picture: Optional[str] = None

class InquiryIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    project_type: str
    budget: Optional[str] = None
    message: str

class InquiryOut(InquiryIn):
    inquiry_id: str
    status: str
    created_at: str

class ProjectIn(BaseModel):
    title: str
    category: str
    location: str
    year: int
    description: str
    cover_image: str
    images: List[str] = []
    featured: bool = False

class ProjectOut(ProjectIn):
    project_id: str

class ClientProjectIn(BaseModel):
    client_email: EmailStr
    title: str
    project_type: str
    progress: int = 0
    status: str = "Planning"
    next_milestone: Optional[str] = None
    next_milestone_date: Optional[str] = None
    notes: Optional[str] = None

class ClientProjectOut(ClientProjectIn):
    cp_id: str
    created_at: str

# ---------- Auth Endpoints ----------
@api.post("/auth/register", response_model=UserOut)
async def register(payload: RegisterIn, response: Response):
    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": email,
        "name": payload.name.strip(),
        "password_hash": hash_password(payload.password),
        "role": "client",
        "picture": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user_doc)
    token = create_access_token(user_id, email, "client")
    set_auth_cookie(response, token)
    return UserOut(user_id=user_id, email=email, name=payload.name, role="client")

@api.post("/auth/login", response_model=UserOut)
async def login(payload: LoginIn, response: Response):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["user_id"], user["email"], user.get("role", "client"))
    set_auth_cookie(response, token)
    return UserOut(
        user_id=user["user_id"], email=user["email"],
        name=user["name"], role=user.get("role", "client"),
        picture=user.get("picture"),
    )

@api.post("/auth/logout")
async def logout(response: Response, request: Request):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.sessions.delete_one({"session_token": session_token})
    clear_auth_cookies(response)
    return {"ok": True}

@api.get("/auth/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return UserOut(**user)

@api.post("/auth/google-session", response_model=UserOut)
async def google_session(payload: GoogleSessionIn, response: Response):
    # Exchange session_id with Emergent Auth
    try:
        r = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": payload.session_id},
            timeout=10,
        )
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google session")
        data = r.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Emergent auth failed: %s", e)
        raise HTTPException(status_code=500, detail="Auth service error")

    email = data["email"].lower()
    name = data.get("name", email.split("@")[0])
    picture = data.get("picture")
    session_token = data["session_token"]

    existing = await db.users.find_one({"email": email})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture}},
        )
        role = existing.get("role", "client")
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        role = "client"
        await db.users.insert_one({
            "user_id": user_id, "email": email, "name": name,
            "role": role, "picture": picture,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Store session
    await db.sessions.insert_one({
        "session_token": session_token, "user_id": user_id,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    response.set_cookie(
        key="session_token", value=session_token, httponly=True,
        secure=True, samesite="none", max_age=7 * 24 * 3600, path="/",
    )
    return UserOut(user_id=user_id, email=email, name=name, role=role, picture=picture)

# ---------- Inquiries ----------
@api.post("/inquiries", response_model=InquiryOut)
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
    return InquiryOut(**doc)

@api.get("/inquiries", response_model=List[InquiryOut])
async def list_inquiries(user: dict = Depends(require_admin)):
    rows = await db.inquiries.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [InquiryOut(**r) for r in rows]

# ---------- Projects (Portfolio) ----------
@api.get("/projects", response_model=List[ProjectOut])
async def list_projects(category: Optional[str] = None, featured: Optional[bool] = None):
    query = {}
    if category and category != "all":
        query["category"] = category
    if featured is not None:
        query["featured"] = featured
    rows = await db.projects.find(query, {"_id": 0}).sort("year", -1).to_list(200)
    return [ProjectOut(**r) for r in rows]

@api.post("/projects", response_model=ProjectOut)
async def create_project(payload: ProjectIn, user: dict = Depends(require_admin)):
    pid = f"prj_{uuid.uuid4().hex[:12]}"
    doc = payload.model_dump()
    doc["project_id"] = pid
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    return ProjectOut(**doc)

# ---------- Client Projects (Dashboard) ----------
@api.get("/client/projects", response_model=List[ClientProjectOut])
async def my_projects(user: dict = Depends(get_current_user)):
    if user.get("role") == "admin":
        rows = await db.client_projects.find({}, {"_id": 0}).to_list(500)
    else:
        rows = await db.client_projects.find({"client_email": user["email"]}, {"_id": 0}).to_list(500)
    return [ClientProjectOut(**r) for r in rows]

@api.post("/client/projects", response_model=ClientProjectOut)
async def create_client_project(payload: ClientProjectIn, user: dict = Depends(require_admin)):
    cp_id = f"cp_{uuid.uuid4().hex[:12]}"
    doc = payload.model_dump()
    doc["cp_id"] = cp_id
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.client_projects.insert_one(doc)
    doc.pop("_id", None)
    return ClientProjectOut(**doc)

@api.get("/")
async def root():
    return {"service": "Stonebridge Construction API", "status": "ok"}

app.include_router(api)

# ---------- CORS ----------
frontend_url = os.environ.get("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url] if frontend_url != "*" else ["*"],
    allow_credentials=frontend_url != "*",
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Seed ----------
SEED_PROJECTS = [
    {
        "title": "Maple Ridge Residence",
        "category": "residential",
        "location": "Aspen, CO",
        "year": 2024,
        "description": "A four-bedroom mountain residence built on a sloped granite site, featuring exposed timber framing and floor-to-ceiling glazing.",
        "cover_image": "https://images.unsplash.com/photo-1710701455648-e85f21bf3a79?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
        "images": [],
        "featured": True,
    },
    {
        "title": "Northgate Commercial Tower",
        "category": "commercial",
        "location": "Denver, CO",
        "year": 2023,
        "description": "Twelve-story mixed-use commercial tower delivered three months ahead of schedule, with a focus on LEED Gold certification.",
        "cover_image": "https://images.unsplash.com/photo-1695067439143-81a61a8c904a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHw0fHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
        "images": [],
        "featured": True,
    },
    {
        "title": "The Linden Loft Renovation",
        "category": "renovation",
        "location": "Boulder, CO",
        "year": 2024,
        "description": "Full gut renovation of a 1920s warehouse loft. Restored original brickwork paired with a custom-fabricated steel mezzanine.",
        "cover_image": "https://images.unsplash.com/photo-1681216868987-b7268753b81c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
        "images": [],
        "featured": True,
    },
    {
        "title": "Glasshouse on Cedar",
        "category": "residential",
        "location": "Portland, OR",
        "year": 2023,
        "description": "Single-family home defined by its dark steel frame and minimalist glass envelope nested into a forested lot.",
        "cover_image": "https://images.unsplash.com/photo-1756227584303-f1400daaa69d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwyfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
        "images": [],
        "featured": False,
    },
    {
        "title": "Steelyard Offices",
        "category": "commercial",
        "location": "Salt Lake City, UT",
        "year": 2022,
        "description": "Adaptive reuse of a former steel manufacturing plant into creative-class office headquarters across 48,000 sq ft.",
        "cover_image": "https://images.pexels.com/photos/946310/pexels-photo-946310.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "images": [],
        "featured": False,
    },
    {
        "title": "Terracotta Courtyard Home",
        "category": "renovation",
        "location": "Santa Fe, NM",
        "year": 2024,
        "description": "Adobe restoration with terracotta-tiled courtyard, hand-troweled lime plaster walls, and reclaimed vigas.",
        "cover_image": "https://images.pexels.com/photos/29895597/pexels-photo-29895597.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "images": [],
        "featured": False,
    },
]

SEED_CLIENT_PROJECTS = [
    {
        "client_email": TEST_CLIENT_EMAIL,
        "title": "Linden Loft Phase II",
        "project_type": "Renovation",
        "progress": 62,
        "status": "Framing",
        "next_milestone": "Mechanical rough-in inspection",
        "next_milestone_date": "2026-03-14",
        "notes": "Custom steel mezzanine fabricated off-site, install slated for next week.",
    },
    {
        "client_email": TEST_CLIENT_EMAIL,
        "title": "Cedar Ridge Garage Studio",
        "project_type": "Residential",
        "progress": 18,
        "status": "Planning",
        "next_milestone": "Permit submission",
        "next_milestone_date": "2026-02-28",
        "notes": "Drawings under review by structural engineer.",
    },
]

@app.on_event("startup")
async def on_startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.projects.create_index("project_id", unique=True)
    await db.inquiries.create_index("inquiry_id", unique=True)
    await db.sessions.create_index("session_token", unique=True)
    await db.client_projects.create_index("cp_id", unique=True)

    # Seed admin
    admin = await db.users.find_one({"email": ADMIN_EMAIL})
    if not admin:
        await db.users.insert_one({
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": ADMIN_EMAIL,
            "name": "Stonebridge Admin",
            "password_hash": hash_password(ADMIN_PASSWORD),
            "role": "admin",
            "picture": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    elif not verify_password(ADMIN_PASSWORD, admin.get("password_hash", "")):
        await db.users.update_one(
            {"email": ADMIN_EMAIL},
            {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}},
        )

    # Seed test client
    test_client = await db.users.find_one({"email": TEST_CLIENT_EMAIL})
    if not test_client:
        await db.users.insert_one({
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": TEST_CLIENT_EMAIL,
            "name": "Sarah Chen",
            "password_hash": hash_password(TEST_CLIENT_PASSWORD),
            "role": "client",
            "picture": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Seed projects
    if await db.projects.count_documents({}) == 0:
        seeded = []
        for p in SEED_PROJECTS:
            seeded.append({**p, "project_id": f"prj_{uuid.uuid4().hex[:12]}"})
        await db.projects.insert_many(seeded)

    # Seed client projects
    if await db.client_projects.count_documents({}) == 0:
        cps = []
        for cp in SEED_CLIENT_PROJECTS:
            cps.append({
                **cp,
                "cp_id": f"cp_{uuid.uuid4().hex[:12]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        await db.client_projects.insert_many(cps)

@app.on_event("shutdown")
async def on_shutdown():
    client.close()
