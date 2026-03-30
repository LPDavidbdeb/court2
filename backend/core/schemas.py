from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExhibitableMixin(BaseModel):
    """
    Common serialization baseline for any object that can be 
    displayed as an exhibit in the registry.
    """
    label: Optional[str] = None
    exhibit_type: Optional[str] = None
    date_display: Optional[str] = None
    description: Optional[str] = None
    parties: Optional[str] = None
    public_url: Optional[str] = None

class ProducedExhibitSchema(ExhibitableMixin):
    id: int
    sort_order: int
    content_type_model: Optional[str] = None
    object_id: Optional[int] = None

    class Config:
        from_attributes = True
