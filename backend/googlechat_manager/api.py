from typing import List
from django.shortcuts import get_object_or_404
from django.db.models import Count
from ninja import Router, Query
from ninja_jwt.authentication import JWTAuth
from .models import ChatMessage, ChatSequence
from .schemas import (
    ChatMessageSchema,
    ChatSequenceSchema,
    ChatSequenceDetailSchema,
    ChatSequenceCreateSchema
)

router = Router(tags=["GoogleChat"])

@router.get("/sequences/", response=List[ChatSequenceSchema], auth=JWTAuth())
def list_sequences(request):
    """List all chat sequences with message counts."""
    return ChatSequence.objects.annotate(message_count=Count('messages')).all()

@router.get("/sequences/{sequence_id}/", response=ChatSequenceDetailSchema, auth=JWTAuth())
def get_sequence(request, sequence_id: int):
    """Get detailed chat sequence with nested messages."""
    seq = get_object_or_404(
        ChatSequence.objects.prefetch_related('messages', 'messages__sender'), 
        pk=sequence_id
    )
    # Materialize the messages for Pydantic
    return {
        "id": seq.id,
        "title": seq.title,
        "start_date": seq.start_date,
        "end_date": seq.end_date,
        "created_at": seq.created_at,
        "message_count": seq.messages.count(),
        "messages": list(seq.messages.all())
    }

@router.post("/sequences/", response=ChatSequenceSchema, auth=JWTAuth())
def create_sequence(request, data: ChatSequenceCreateSchema):
    """Create a new chat sequence from selected message IDs."""
    seq = ChatSequence.objects.create(title=data.title)
    messages = ChatMessage.objects.filter(id__in=data.message_ids)
    seq.messages.set(messages)
    seq.update_dates()
    return seq

@router.get("/messages/", response=List[ChatMessageSchema], auth=JWTAuth())
def list_messages(request, page: int = 1, page_size: int = 50):
    """
    Paginated stream of all chat messages, ordered by timestamp.
    Used for the Conversation Stream view.
    """
    offset = (page - 1) * page_size
    return ChatMessage.objects.select_related('sender').all().order_by('timestamp')[offset:offset+page_size]
