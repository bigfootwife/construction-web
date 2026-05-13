"""Authentication routes."""
import uuid
import logging
import asyncio
from datetime import datetime, timezone, timedelta

import requests
from fastapi import APIRouter, HTTPException, Request, Response, Depends

from ..config import (
    MAX_FAILED_LOGINS, LOCKOUT_MINUTES, ADMIN_EMAIL, ADMIN_PASSWORD,
)
from ..db import db
from ..models import RegisterIn, LoginIn, GoogleSessionIn, UserOut
from ..security import (
    hash_password, verify_password, create_access_token,
    set_auth_cookie, clear_auth_cookies, get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("stonebridge.auth")


# ----- Rate limiting -----
async def _check_lockout(identifier: str) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_MINUTES)
    recent = await db.login_attempts.count_documents({
        "identifier": identifier,
        "failed_at": {"$gte": cutoff},
    })
    if recent >= MAX_FAILED_LOGINS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed login attempts. Try again in {LOCKOUT_MINUTES} minutes.",
        )


async def _record_failed(identifier: str) -> None:
    await db.login_attempts.insert_one({
        "identifier": identifier,
        "failed_at": datetime.now(timezone.utc),
    })


async def _clear_failed(identifier: str) -> None:
    await db.login_attempts.delete_many({"identifier": identifier})


@router.post("/register", response_model=UserOut)
async def register(payload: RegisterIn, response: Response):
    email = payload.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    await db.users.insert_one({
        "user_id": user_id,
        "email": email,
        "name": payload.name.strip(),
        "password_hash": hash_password(payload.password),
        "role": "client",
        "picture": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    token = create_access_token(user_id, email, "client")
    set_auth_cookie(response, token)
    return UserOut(user_id=user_id, email=email, name=payload.name, role="client")


@router.post("/login", response_model=UserOut)
async def login(payload: LoginIn, request: Request, response: Response):
    email = payload.email.lower().strip()
    xff = request.headers.get("x-forwarded-for", "")
    client_ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "unknown")
    ip_id = f"{client_ip}:{email}"
    email_id = f"email:{email}"
    await _check_lockout(ip_id)
    await _check_lockout(email_id)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        await _record_failed(ip_id)
        await _record_failed(email_id)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await _clear_failed(ip_id)
    await _clear_failed(email_id)
    token = create_access_token(user["user_id"], user["email"], user.get("role", "client"))
    set_auth_cookie(response, token)
    return UserOut(
        user_id=user["user_id"], email=user["email"],
        name=user["name"], role=user.get("role", "client"),
        picture=user.get("picture"),
    )


@router.post("/logout")
async def logout(response: Response, request: Request):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.sessions.delete_one({"session_token": session_token})
    clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return UserOut(**user)


@router.post("/google-session", response_model=UserOut)
async def google_session(payload: GoogleSessionIn, response: Response):
    try:
        r = await asyncio.to_thread(
            requests.get,
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
