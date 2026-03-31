from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from protagonist_manager.schemas import ProtagonistSchema

class ChatParticipantSchema(BaseModel):
    id: int
    original_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    protagonist: Optional[ProtagonistSchema] = None

    class Config:
        from_attributes = True

class ChatThreadSchema(BaseModel):
    id: int
    original_thread_id: str
    space_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageSchema(BaseModel):
    id: int
    thread_id: int
    sender: Optional[ChatParticipantSchema] = None
    timestamp: datetime
    text_content: Optional[str] = None
    is_processed_by_ai: bool

    class Config:
        from_attributes = True

class ChatSequenceSchema(BaseModel):
    id: int
    title: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True

class ChatSequenceDetailSchema(ChatSequenceSchema):
    messages: List[ChatMessageSchema] = []

    class Config:
        from_attributes = True

class ChatSequenceCreateSchema(BaseModel):
    title: str
    message_ids: List[int]
