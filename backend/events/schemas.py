from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from core.schemas import ExhibitableBaseSchema

class PhotoSchema(BaseModel):
    id: int
    title: Optional[str] = None
    file: Optional[str] = None
    
    class Config:
        from_attributes = True

class EventSchema(ExhibitableBaseSchema):
    date: date
    explanation: str
    email_quote: Optional[str] = None
    linked_email_id: Optional[int] = None
    parent_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class EventDetailSchema(EventSchema):
    linked_photos: List[PhotoSchema] = []
    children: List['EventSchema'] = []

EventDetailSchema.update_forward_refs()
