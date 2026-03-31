from typing import List
from ninja import Router
from django.shortcuts import get_object_or_404
from .models import Event
from .schemas import EventSchema, EventDetailSchema

router = Router(tags=["Events"])

@router.get("/", response=List[EventSchema])
def list_events(request):
    """
    List all events, ordered by date from newest to oldest.
    """
    return Event.objects.order_by('-date')

@router.get("/{event_id}", response=EventDetailSchema)
def get_event(request, event_id: int):
    """
    Retrieve details of a specific event, including linked photos and children.
    """
    return get_object_or_404(Event, pk=event_id)
