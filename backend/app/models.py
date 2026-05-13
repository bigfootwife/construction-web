"""Pydantic models."""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


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


class CommentIn(BaseModel):
    cp_id: str
    body: str = Field(min_length=1, max_length=4000)


class CommentOut(BaseModel):
    comment_id: str
    cp_id: str
    author_user_id: str
    author_name: str
    author_role: str
    body: str
    created_at: str
