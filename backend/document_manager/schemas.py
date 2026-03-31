from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from core.schemas import ExhibitableBaseSchema

class LibraryNodeSchema(BaseModel):
    id: int
    item: str
    document_id: int
    # Treebeard annotated list structure fields
    depth: int
    # Generic info
    content_type_id: Optional[int] = None
    object_id: Optional[int] = None
    
    # Placeholder for the object returned by get_annotated_list
    # treebeard returns (instance, info) tuples or a list of dicts
    # we'll use a wrapper if needed or simplify.

class DocumentSchema(ExhibitableBaseSchema):
    title: str
    author_id: Optional[int] = None
    document_original_date: Optional[datetime] = None
    solemn_declaration: Optional[str] = None
    source_type: str
    
    class Config:
        from_attributes = True
