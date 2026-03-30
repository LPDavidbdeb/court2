from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class LibraryNodeSchema(BaseModel):
    id: int
    item: str
    document_id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    content_type_id: Optional[int] = None
    object_id: Optional[int] = None
    # We'll use a separate field for children to avoid infinite recursion in some cases,
    # or use forward references.
    children: List['LibraryNodeSchema'] = []

    class Config:
        from_attributes = True

LibraryNodeSchema.update_forward_refs()

class DocumentSchema(BaseModel):
    id: int
    title: str
    author_id: Optional[int] = None
    document_original_date: Optional[datetime] = None
    source_type: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
