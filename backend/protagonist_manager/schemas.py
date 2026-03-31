from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class ProtagonistEmailSchema(BaseModel):
    id: Optional[int] = None
    email_address: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ProtagonistCreateSchema(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    role: str
    linkedin_url: Optional[str] = None
    emails: List[ProtagonistEmailSchema] = []

class ProtagonistSchema(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    role: str
    linkedin_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    emails: List[ProtagonistEmailSchema] = []

    class Config:
        from_attributes = True
