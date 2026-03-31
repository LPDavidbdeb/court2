from typing import List
from django.shortcuts import get_object_or_404
from django.db.models import Count
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from .models import Event
from .schemas import EventSchema, EventDetailSchema

router = Router(tags=["Events"])

def _event_to_dict(e: Event) -> dict:
    """Helper to materialize Event and its nested related managers for Pydantic."""
    return {
        "id": e.id,
        "date": e.date,
        "explanation": e.explanation,
        "email_quote": e.email_quote,
        "linked_email_id": e.linked_email_id,
        "parent_id": e.parent_id,
        "photo_count": e.linked_photos.count(),
        "created_at": getattr(e, 'created_at', None),
        "updated_at": getattr(e, 'updated_at', None),
        "public_url": e.get_public_url(),
        "linked_photos": list(e.linked_photos.all()),
        "linked_email": e.linked_email,
        "children": list(e.children.all())
    }

@router.get("/", response=List[EventSchema], auth=JWTAuth())
def list_events(request):
    """
    List all events, ordered by date.
    """
    return Event.objects.annotate(photo_count=Count('linked_photos')).order_by('date').all()

@router.get("/{event_id}/", response=EventDetailSchema, auth=JWTAuth())
def get_event(request, event_id: int):
    """
    Retrieve details of a specific event, including linked evidence.
    """
    e = get_object_or_404(
        Event.objects.select_related("linked_email").prefetch_related("linked_photos", "children"),
        pk=event_id
    )
    return _event_to_dict(e)

@router.delete("/{event_id}/", auth=JWTAuth())
def delete_event(request, event_id: int):
    """Delete an event."""
    e = get_object_or_404(Event, pk=event_id)
    e.delete()
    return {"success": True}
