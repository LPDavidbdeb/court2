from typing import List
from ninja import Router
from .services import EventService
from .schemas import EventSchema, EventDetailSchema

router = Router(tags=["Events"])

@router.get("/", response=List[EventSchema])
def list_events(request):
    """
    List all events, ordered by date from newest to oldest, with linked photos prefetched.
    """
    return EventService.get_all_events_with_photos()

@router.get("/{event_id}", response=EventDetailSchema)
def get_event(request, event_id: int):
    """
    Retrieve details of a specific event, including linked photos.
    """
    event = EventService.get_event_with_photos(event_id)
    return EventDetailSchema(
        id=event.id,
        date=event.date,
        explanation=event.explanation,
        email_quote=event.email_quote,
        linked_email=event.linked_email.id if event.linked_email else None,
        parent=event.parent.id if event.parent else None,
        linked_photos=[photo for photo in event.linked_photos.all()]
    )
