from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from core.schemas import ExhibitableBaseSchema
from protagonist_manager.schemas import ProtagonistSchema

class PDFDocumentSchema(ExhibitableBaseSchema):
    title: str
    author: Optional[ProtagonistSchema] = None
    document_date: Optional[datetime] = None
    file: Optional[str] = None
    ai_analysis: Optional[str] = None

    class Config:
        from_attributes = True

class PDFDocumentCreateSchema(BaseModel):
    title: str
    author_id: Optional[int] = None
    document_date: Optional[datetime] = None
    ai_analysis: Optional[str] = ""

class PDFQuoteSchema(ExhibitableBaseSchema):
    pdf_document_id: int
    quote_text: str
    page_number: int
    
    class Config:
        from_attributes = True
