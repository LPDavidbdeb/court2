from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime, date
from core.schemas import ExhibitableBaseSchema
from protagonist_manager.schemas import ProtagonistSchema

class DocumentSchema(ExhibitableBaseSchema):
    title: str
    author: Optional[ProtagonistSchema] = None
    document_original_date: Optional[date] = None
    solemn_declaration: Optional[str] = None
    source_type: str
    file_source: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentCreateSchema(BaseModel):
    title: str
    author_id: Optional[int] = None
    document_original_date: Optional[date] = None
    solemn_declaration: Optional[str] = ""
    source_type: str = "REPRODUCED"

class StatementSchema(BaseModel):
    id: int
    text: Optional[str] = None
    is_true: bool
    is_falsifiable: Optional[bool] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LibraryNodeSchema(BaseModel):
    id: int
    item: str
    depth: int
    document_id: int
    content_type_id: Optional[int] = None
    object_id: Optional[int] = None
    info: Dict[str, Any] # Treebeard info
