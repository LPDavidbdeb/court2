from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


# ── Raw Photo (unchanged from original) ──────────────────────────────────────

class PhotoSchema(BaseModel):
    id: Optional[int] = None
    file: Optional[str] = None
    file_name: str
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    image_format: Optional[str] = None
    image_mode: Optional[str] = None
    datetime_original: Optional[datetime] = None
    make: Optional[str] = None
    model: Optional[str] = None

    class Config:
        from_attributes = True


# ── Photo nested inside a document ───────────────────────────────────────────

class PhotoInDocumentSchema(BaseModel):
    """Minimal photo representation used when nested in PhotoDocumentDetailSchema."""
    id: int
    file_name: str
    file_url: Optional[str] = None   # Absolute URL, built by the API view
    width: Optional[int] = None
    height: Optional[int] = None

    class Config:
        from_attributes = True


# ── PhotoDocument list item ───────────────────────────────────────────────────

class PhotoDocumentListSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    photo_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── PhotoDocument detail ──────────────────────────────────────────────────────

class PhotoDocumentDetailSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    ai_analysis: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    photos: List[PhotoInDocumentSchema] = []

    class Config:
        from_attributes = True


# ── Request / Response payloads ───────────────────────────────────────────────

class DescriptionUpdateSchema(BaseModel):
    description: str


# The three personas shown in the legacy UI select element.
VALID_PERSONAS = {'forensic_clerk', 'official_scribe', 'summary_clerk'}


class AnalyzeRequestSchema(BaseModel):
    persona: str = 'forensic_clerk'

    def effective_persona(self) -> str:
        """Return the persona key, falling back to the default if unknown."""
        return self.persona if self.persona in VALID_PERSONAS else 'forensic_clerk'


class AnalysisResponseSchema(BaseModel):
    status: str
    analysis: Optional[str] = None
    message: Optional[str] = None


# Kept for any existing code that imports PhotoDocumentSchema by name
class PhotoDocumentSchema(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    ai_analysis: Optional[str] = None

    class Config:
        from_attributes = True
