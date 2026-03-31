from typing import List, Optional
from core.schemas import ExhibitableBaseSchema
from photos.schemas import PhotoDocumentSchema
from datetime import date

class EventSchema(ExhibitableBaseSchema):
    date: date
    explanation: str
    email_quote: Optional[str] = None
    linked_email_id: Optional[int] = None
    parent_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class EventDetailSchema(EventSchema):
    linked_photos: List[PhotoDocumentSchema] = []
    # Optionally add children or other nested fields if needed

    class Config:
        from_attributes = True
