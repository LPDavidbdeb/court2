from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ExhibitableBaseSchema(BaseModel):
    """
    Base schema mirroring the ExhibitableMixin.
    All models that can be exhibited must inherit from this to ensure a common serialization baseline.
    """
    id: Optional[int] = None
    public_url: Optional[str] = Field(None, description="Publicly accessible URL for the exhibit")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
