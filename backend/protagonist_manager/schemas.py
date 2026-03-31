from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


# ── Protagonist contact email ──────────────────────────────────────────────────

class ProtagonistEmailSchema(BaseModel):
    id: Optional[int] = None
    email_address: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ── Create / update payload ────────────────────────────────────────────────────

class ProtagonistCreateSchema(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    role: str
    linkedin_url: Optional[str] = None
    emails: List[ProtagonistEmailSchema] = []


# ── List item (with denormalized evidence counts) ─────────────────────────────

class ProtagonistListSchema(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    role: str
    linkedin_url: Optional[str] = None
    emails: List[ProtagonistEmailSchema] = []
    # Annotated by list_protagonists query
    email_thread_count: int = 0
    photo_document_count: int = 0

    class Config:
        from_attributes = True


# ── Evidence summaries for the detail view ────────────────────────────────────

class EmailThreadSummarySchema(BaseModel):
    id: int
    subject: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class PhotoDocumentSummarySchema(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Full protagonist (used by legacy code + detail endpoint) ──────────────────

class ProtagonistSchema(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    role: str
    linkedin_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    emails: List[ProtagonistEmailSchema] = []

    class Config:
        from_attributes = True


# ── Detail (protagonist + nested evidence) ────────────────────────────────────

class ProtagonistDetailSchema(ProtagonistSchema):
    """Full protagonist profile including all linked evidence."""
    email_thread_count: int = 0
    photo_document_count: int = 0
    email_threads: List[EmailThreadSummarySchema] = []
    authored_photo_documents: List[PhotoDocumentSummarySchema] = []
