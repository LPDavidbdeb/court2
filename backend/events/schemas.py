from typing import List, Optional
from core.schemas import ExhibitableBaseSchema
from photos.schemas import PhotoSchema
from email_manager.schemas import EmailSchema
from datetime import date

class EventSchema(ExhibitableBaseSchema):
    date: date
    explanation: str
    email_quote: Optional[str] = None
    linked_email_id: Optional[int] = None
    parent_id: Optional[int] = None
    photo_count: int = 0
    
    class Config:
        from_attributes = True

class EventDetailSchema(EventSchema):
    linked_photos: List[PhotoSchema] = []
    linked_email: Optional[EmailSchema] = None
    # Support children for nested events
    children: List['EventSchema'] = []

    class Config:
        from_attributes = True
