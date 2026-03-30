from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ExhibitableBaseSchema(BaseModel):
    """
    Base schema mirroring the ExhibitableMixin.
    All models that can be exhibited must inherit from this to ensure a common serialization baseline.
    """
    id: int
    public_url: Optional[str] = Field(None, description="Publicly accessible URL for the exhibit")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Add any other core fields from your Django ExhibitableMixin here

    class Config:
        from_attributes = True

class ProducedExhibitSchema(ExhibitableBaseSchema):
    # Additional specific fields for ProducedExhibit
    case_id: int
    exhibit_type: str
    parties: Optional[str] = None
    label: Optional[str] = None
    date_display: Optional[str] = None
    description: Optional[str] = None
