from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

import bcrypt
import jwt
import requests
import resend
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File
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
TEST_CLIENT_EMAIL = os.environ.get("TEST_CLIENT_EMAIL", "client@stonebridge.com")
TEST_CLIENT_PASSWORD = os.environ.get("TEST_CLIENT_PASSWORD", "Client@1234")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
INQUIRY_NOTIFICATION_EMAIL = os.environ.get("INQUIRY_NOTIFICATION_EMAIL")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = os.environ.get("APP_NAME", "stonebridge")
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
storage_key: Optional[str] = None

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

class ProjectPatch(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    images: Optional[List[str]] = None
    featured: Optional[bool] = None

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

class ClientDocumentIn(BaseModel):
    cp_id: str
    title: str
    file_url: str
    file_type: Optional[str] = None
    size: Optional[int] = None

class ClientDocumentOut(ClientDocumentIn):
    doc_id: str
    uploaded_at: str

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

# ---------- Rate limiting (brute-force protection) ----------
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15

async def _check_lockout(identifier: str) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_MINUTES)
    recent_fails = await db.login_attempts.count_documents({
        "identifier": identifier,
        "failed_at": {"$gte": cutoff},
    })
    if recent_fails >= MAX_FAILED_LOGINS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed login attempts. Try again in {LOCKOUT_MINUTES} minutes.",
        )

async def _record_failed_login(identifier: str) -> None:
    await db.login_attempts.insert_one({
        "identifier": identifier,
        "failed_at": datetime.now(timezone.utc),
    })

async def _clear_failed_logins(identifier: str) -> None:
    await db.login_attempts.delete_many({"identifier": identifier})

@api.post("/auth/login", response_model=UserOut)
async def login(payload: LoginIn, request: Request, response: Response):
    email = payload.email.lower().strip()
    # Prefer real client IP from X-Forwarded-For (Kubernetes ingress); else direct .host
    xff = request.headers.get("x-forwarded-for", "")
    client_ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "unknown")
    identifier = f"{client_ip}:{email}"
    # Also check email-only identifier so distributed brute force across IPs is still caught
    email_identifier = f"email:{email}"
    await _check_lockout(identifier)
    await _check_lockout(email_identifier)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        await _record_failed_login(identifier)
        await _record_failed_login(email_identifier)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await _clear_failed_logins(identifier)
    await _clear_failed_logins(email_identifier)
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
def _build_inquiry_email_html(inq: dict) -> str:
    return f"""
    <table style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #E5E2DA;border-collapse:collapse;">
      <tr><td style="background:#A85A3F;color:#fff;padding:20px;font-size:18px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">New Inquiry · Stonebridge</td></tr>
      <tr><td style="padding:24px;">
        <p style="margin:0 0 16px;color:#1C1C1A;font-size:16px;">A new project inquiry has been received.</p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr><td style="padding:8px 0;color:#6E6D69;width:140px;">Name</td><td style="padding:8px 0;color:#1C1C1A;font-weight:600;">{inq.get('name','')}</td></tr>
          <tr><td style="padding:8px 0;color:#6E6D69;">Email</td><td style="padding:8px 0;color:#1C1C1A;"><a href="mailto:{inq.get('email','')}" style="color:#A85A3F;">{inq.get('email','')}</a></td></tr>
          <tr><td style="padding:8px 0;color:#6E6D69;">Phone</td><td style="padding:8px 0;color:#1C1C1A;">{inq.get('phone') or '—'}</td></tr>
          <tr><td style="padding:8px 0;color:#6E6D69;">Project Type</td><td style="padding:8px 0;color:#1C1C1A;">{inq.get('project_type','')}</td></tr>
          <tr><td style="padding:8px 0;color:#6E6D69;">Budget</td><td style="padding:8px 0;color:#1C1C1A;">{inq.get('budget') or '—'}</td></tr>
        </table>
        <hr style="border:none;border-top:1px solid #E5E2DA;margin:20px 0;">
        <p style="margin:0 0 8px;color:#6E6D69;font-size:12px;text-transform:uppercase;letter-spacing:2px;">Message</p>
        <p style="margin:0;color:#1C1C1A;font-size:14px;line-height:1.6;white-space:pre-wrap;">{inq.get('message','')}</p>
      </td></tr>
      <tr><td style="background:#F5F3EF;color:#6E6D69;padding:14px 24px;font-size:12px;">Sent {inq.get('created_at','')} · Inquiry ID: {inq.get('inquiry_id','')}</td></tr>
    </table>
    """

async def _send_inquiry_email(inq: dict) -> None:
    if not RESEND_API_KEY or not INQUIRY_NOTIFICATION_EMAIL:
        logger.info("Resend not configured; skipping email")
        return
    params = {
        "from": SENDER_EMAIL,
        "to": [INQUIRY_NOTIFICATION_EMAIL],
        "reply_to": inq.get("email"),
        "subject": f"New Inquiry · {inq.get('name','')} · {inq.get('project_type','')}",
        "html": _build_inquiry_email_html(inq),
    }
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info("Inquiry email sent: %s", result.get("id"))
    except Exception as e:
        logger.error("Inquiry email send failed: %s", e)

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
    # Fire-and-forget email
    asyncio.create_task(_send_inquiry_email(doc))
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

@api.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str):
    doc = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**doc)

@api.post("/projects", response_model=ProjectOut)
async def create_project(payload: ProjectIn, user: dict = Depends(require_admin)):
    pid = f"prj_{uuid.uuid4().hex[:12]}"
    doc = payload.model_dump()
    doc["project_id"] = pid
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    return ProjectOut(**doc)

@api.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, payload: ProjectPatch, user: dict = Depends(require_admin)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.projects.update_one({"project_id": project_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    doc = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    return ProjectOut(**doc)

@api.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(require_admin)):
    result = await db.projects.delete_one({"project_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True, "deleted": project_id}

# ---------- File Upload (Object Storage) ----------
MIME_BY_EXT = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "dwg": "application/acad",
    "txt": "text/plain",
}

def init_storage() -> Optional[str]:
    global storage_key
    if storage_key:
        return storage_key
    if not EMERGENT_LLM_KEY:
        return None
    try:
        resp = requests.post(
            f"{STORAGE_URL}/init",
            json={"emergent_key": EMERGENT_LLM_KEY},
            timeout=30,
        )
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        logger.info("Object storage initialized")
        return storage_key
    except Exception as e:
        logger.error("Storage init failed: %s", e)
        return None

def storage_put(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    if not key:
        raise HTTPException(status_code=503, detail="Storage unavailable")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120,
    )
    if resp.status_code == 403:
        # refresh key once
        global storage_key
        storage_key = None
        key = init_storage()
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data, timeout=120,
        )
    resp.raise_for_status()
    return resp.json()

def storage_get(path: str) -> tuple[bytes, str]:
    key = init_storage()
    if not key:
        raise HTTPException(status_code=503, detail="Storage unavailable")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60,
    )
    if resp.status_code == 403:
        global storage_key
        storage_key = None
        key = init_storage()
        resp = requests.get(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key}, timeout=60,
        )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

@api.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(require_admin),
):
    ext = (file.filename or "bin").rsplit(".", 1)[-1].lower()
    if ext not in MIME_BY_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: images, PDF, DOC/DOCX, XLS/XLSX, DWG, TXT.")
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
    # Public URL the frontend can use directly in <img src>
    public_url = f"{os.environ.get('FRONTEND_URL','').rstrip('/')}/api/files/{canonical_path}"
    return {"file_id": file_id, "url": public_url, "path": canonical_path}

@api.get("/files/{path:path}")
async def serve_file(path: str):
    record = await db.files.find_one({"storage_path": path, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    data, content_type = await asyncio.to_thread(storage_get, path)
    return Response(content=data, media_type=record.get("content_type") or content_type)

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

# ---------- Client Documents ----------
@api.get("/client/documents", response_model=List[ClientDocumentOut])
async def list_documents(cp_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query: dict = {}
    if cp_id:
        query["cp_id"] = cp_id
    if user.get("role") != "admin":
        # Restrict to documents belonging to the client's own projects
        my_cps = await db.client_projects.find(
            {"client_email": user["email"]}, {"_id": 0, "cp_id": 1}
        ).to_list(500)
        allowed = [cp["cp_id"] for cp in my_cps]
        if cp_id and cp_id not in allowed:
            raise HTTPException(status_code=403, detail="Not your project")
        query["cp_id"] = {"$in": allowed} if not cp_id else cp_id
    rows = await db.client_documents.find(query, {"_id": 0}).sort("uploaded_at", -1).to_list(500)
    return [ClientDocumentOut(**r) for r in rows]

@api.post("/client/documents", response_model=ClientDocumentOut)
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

@api.delete("/client/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(require_admin)):
    result = await db.client_documents.delete_one({"doc_id": doc_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True, "deleted": doc_id}

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
    await db.files.create_index("file_id", unique=True)
    await db.files.create_index("storage_path", unique=True)
    await db.login_attempts.create_index("identifier")
    # TTL: auto-prune login_attempts older than 24h
    try:
        await db.login_attempts.drop_index("failed_at_1")
    except Exception:
        pass
    await db.login_attempts.create_index("failed_at", expireAfterSeconds=24 * 3600)
    await db.client_documents.create_index("doc_id", unique=True)
    await db.client_documents.create_index("cp_id")

    # Drop any pre-existing string-typed failed_at rows so the new datetime field is consistent
    try:
        await db.login_attempts.delete_many({"failed_at": {"$type": "string"}})
    except Exception:
        pass

    # Initialize object storage (non-fatal)
    try:
        await asyncio.to_thread(init_storage)
    except Exception as e:
        logger.warning("Storage init at startup failed: %s", e)

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

    # Seed sample documents for the test client's projects
    if await db.client_documents.count_documents({}) == 0:
        test_cps = await db.client_projects.find(
            {"client_email": TEST_CLIENT_EMAIL}, {"_id": 0}
        ).to_list(10)
        sample_docs = [
            {"title": "Construction Agreement (signed)", "file_type": "application/pdf"},
            {"title": "Schematic Drawings — Rev C", "file_type": "application/pdf"},
            {"title": "Material Schedule — Q1 2026", "file_type": "application/vnd.ms-excel"},
        ]
        docs_to_insert = []
        for cp in test_cps:
            for sd in sample_docs[:2]:
                docs_to_insert.append({
                    "doc_id": f"doc_{uuid.uuid4().hex[:12]}",
                    "cp_id": cp["cp_id"],
                    "title": sd["title"],
                    "file_url": "https://www.africau.edu/images/default/sample.pdf",
                    "file_type": sd["file_type"],
                    "size": 245312,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                })
        if docs_to_insert:
            await db.client_documents.insert_many(docs_to_insert)

@app.on_event("shutdown")
async def on_shutdown():
    client.close()
