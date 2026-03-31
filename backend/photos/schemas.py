from typing import Optional
from core.schemas import ExhibitableBaseSchema
from datetime import datetime

class PhotoDocumentSchema(ExhibitableBaseSchema):
    file_name: str
    file_size: Optional[int]
    width: Optional[int]
    height: Optional[int]
    image_format: Optional[str]
    image_mode: Optional[str]
    artist: Optional[str]
    datetime_original: Optional[datetime]
    gps_latitude: Optional[float]
    gps_longitude: Optional[float]
    make: Optional[str]
    model: Optional[str]
    iso_speed: Optional[int]
    exposure_time: Optional[str]
    f_number: Optional[float]
    focal_length: Optional[float]
    lens_model: Optional[str]

    class Config:
        from_attributes = True
