from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from core.schemas import ExhibitableBaseSchema
from protagonist_manager.schemas import ProtagonistSchema

class PDFDocumentTypeSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class PDFQuoteSchema(BaseModel):
    id: int
    pdf_document_id: int
    quote_text: str
    page_number: int
    quote_location_details: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuoteCreateSchema(BaseModel):
    quote_text: str
    page_number: int
    quote_location_details: Optional[str] = None

class PDFDocumentSchema(ExhibitableBaseSchema):
    title: str
    author: Optional[ProtagonistSchema] = None
    document_date: Optional[date] = None
    document_type: Optional[PDFDocumentTypeSchema] = None
    file: str
    ai_analysis: Optional[str] = None
    uploaded_at: datetime
    quotes: List[PDFQuoteSchema] = []

    @validator("file", pre=True)
    def validate_file_url(cls, v):
        if hasattr(v, 'url'):
            return v.url
        return v

    class Config:
        from_attributes = True

class PDFDocumentCreateSchema(BaseModel):
    title: str
    author_id: Optional[int] = None
    document_date: Optional[date] = None
    document_type_id: Optional[int] = None
    ai_analysis: Optional[str] = ""
