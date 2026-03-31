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
    saved_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailSchema(ExhibitableBaseSchema):
    thread_id: int
    message_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    recipients_to: Optional[str] = None
    recipients_cc: Optional[str] = None
    recipients_bcc: Optional[str] = None
    date_sent: Optional[datetime] = None
    body_plain_text: Optional[str] = None
    eml_file: Optional[str] = None
    sender_protagonist: Optional[ProtagonistSchema] = None
    recipient_protagonists: List[ProtagonistSchema] = []

    class Config:
        from_attributes = True

class EmailQuoteSchema(ExhibitableBaseSchema):
    email_id: int
    quote_text: str
    full_sentence: str
    
    class Config:
        from_attributes = True

class EmailThreadDetailSchema(EmailThreadSchema):
    emails: List[EmailSchema]
