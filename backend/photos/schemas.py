from typing import Optional, List
from core.schemas import ExhibitableBaseSchema
from datetime import datetime
from pydantic import BaseModel

class PhotoSchema(ExhibitableBaseSchema):
    file: Optional[str] = None
    file_name: str
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    image_format: Optional[str] = None
    image_mode: Optional[str] = None
    datetime_original: Optional[datetime] = None
    make: Optional[str] = None
    model: Optional[str] = None

    class Config:
        from_attributes = True

class PhotoDocumentSchema(ExhibitableBaseSchema):
    title: str
    description: Optional[str] = None
    ai_analysis: Optional[str] = None
    # We can include a summary of photos or a list of IDs/Schemas if needed
    
    class Config:
        from_attributes = True
