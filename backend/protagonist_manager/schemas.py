from pydantic import BaseModel
from typing import Optional

class ProtagonistSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None

    class Config:
        from_attributes = True
