from typing import List
from ninja import Router
from django.shortcuts import get_object_or_404
from .models import Event
from .services import EventService
from .schemas import EventSchema, EventDetailSchema

router = Router(tags=["Events"])

@router.get("/", response=List[EventSchema])
def list_events(request):
    """
    List all events, ordered by date from newest to oldest.
    """
    return EventService.get_all_events_with_photos()

@router.get("/{event_id}", response=EventDetailSchema)
def get_event(request, event_id: int):
    """
    Retrieve details of a specific event, including linked photos.
    """
    return EventService.get_event_with_photos(event_id)
