from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from protagonist_manager.schemas import ProtagonistSchema


# ── Protagonist summary (lightweight, for embedding in thread responses) ──────

class ProtagonistSummarySchema(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


# ── Email within a thread ─────────────────────────────────────────────────────

class EmailSchema(BaseModel):
    id: Optional[int] = None
    thread_id: int           # FK integer (email.thread_id)
    message_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    recipients_to: Optional[str] = None
    recipients_cc: Optional[str] = None
    date_sent: Optional[datetime] = None
    body_plain_text: Optional[str] = None
    sender_protagonist: Optional[ProtagonistSummarySchema] = None

    class Config:
        from_attributes = True


# ── Thread list item ──────────────────────────────────────────────────────────

class EmailThreadSchema(BaseModel):
    id: int
    thread_id: str           # The CharField identifier (e.g. Gmail thread ID)
    subject: Optional[str] = None
    # Annotated by list_threads_service — None on un-annotated instances
    start_date: Optional[datetime] = None
    saved_at: datetime
    updated_at: datetime
    # Nested to avoid a second API call for protagonist name
    protagonist: Optional[ProtagonistSummarySchema] = None

    class Config:
        from_attributes = True


# ── Thread detail (thread + ordered email list) ───────────────────────────────

class EmailThreadDetailSchema(EmailThreadSchema):
    """Full thread with all emails, sorted by date_sent (guaranteed by Email.Meta)."""
    emails: List[EmailSchema] = []


# ── Payloads ──────────────────────────────────────────────────────────────────

class EmailCreateSchema(BaseModel):
    thread_id: int
    message_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    date_sent: Optional[datetime] = None
    body_plain_text: Optional[str] = None
    sender_protagonist_id: Optional[int] = None
    recipient_protagonists_ids: List[int] = []


class EmailQuoteSchema(BaseModel):
    id: Optional[int] = None
    email_id: int
    quote_text: str
    full_sentence: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UploadResponseSchema(BaseModel):
    success: bool
    thread_id: int
    subject: Optional[str] = None
    message: Optional[str] = None
