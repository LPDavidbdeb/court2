from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from core.schemas import ExhibitableBaseSchema
from protagonist_manager.schemas import ProtagonistSchema

class EmailThreadSchema(BaseModel):
    id: int
    thread_id: str
    subject: Optional[str] = None
    protagonist: Optional[ProtagonistSchema] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailSchema(ExhibitableBaseSchema):
    thread_id: int
    message_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    date_sent: Optional[datetime] = None
    body_plain_text: Optional[str] = None
    sender_protagonist: Optional[ProtagonistSchema] = None
    recipient_protagonists: List[ProtagonistSchema] = []

    class Config:
        from_attributes = True

class EmailCreateSchema(BaseModel):
    thread_id: int
    message_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    date_sent: Optional[datetime] = None
    body_plain_text: Optional[str] = None
    sender_protagonist_id: Optional[int] = None
    recipient_protagonists_ids: List[int] = []

class EmailQuoteSchema(ExhibitableBaseSchema):
    email_id: int
    quote_text: str
    full_sentence: str
    
    class Config:
        from_attributes = True

class EmailThreadDetailSchema(EmailThreadSchema):
    emails: List[EmailSchema] = []
