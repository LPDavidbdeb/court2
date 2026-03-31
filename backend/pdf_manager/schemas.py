from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from core.schemas import ExhibitableBaseSchema

class PDFTableDataSchema(BaseModel):
    table_index: int
    columns: List[str]
    data: List[Dict[str, Any]]

class PDFDocumentSchema(ExhibitableBaseSchema):
    title: str
    author_id: Optional[int] = None
    document_date: Optional[datetime] = None
    ai_analysis: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True
