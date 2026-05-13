"""Stonebridge Construction API — entry point."""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import logging
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL
from app.db import client
from app.seed import run_startup
from app.routers import auth, inquiries, projects, files, client as client_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("stonebridge")

app = FastAPI(title="Stonebridge Construction API")
api = APIRouter(prefix="/api")
api.include_router(auth.router)
api.include_router(inquiries.router)
api.include_router(projects.router)
api.include_router(files.router)
api.include_router(client_router.router)


@api.get("/")
async def root():
    return {"service": "Stonebridge Construction API", "status": "ok"}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    allow_credentials=FRONTEND_URL != "*",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await run_startup()


@app.on_event("shutdown")
async def on_shutdown():
    client.close()
