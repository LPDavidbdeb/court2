from typing import Optional
from pydantic import BaseModel

class ProtagonistSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None

    class Config:
        from_attributes = True
