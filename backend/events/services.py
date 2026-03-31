from .models import Event
from django.db.models import Prefetch

class EventService:
    """
    Service class for fetching, sorting, and linking timeline events to their supporting photo evidence.
    All logic here is decoupled from HTTP request/response context.
    """
    @staticmethod
    def get_all_events_with_photos(order="-date"):
        """
        Fetch all events, prefetching linked photos, ordered by the given field (default: newest first).
        """
        return Event.objects.prefetch_related('linked_photos').order_by(order)

    @staticmethod
    def get_event_with_photos(event_id):
        """
        Fetch a single event by ID, including its linked photos.
        """
        return Event.objects.prefetch_related('linked_photos').get(pk=event_id)

    @staticmethod
    def get_next_event(current_event):
        """
        Get the next event in timeline order (by date, then pk).
        """
        next_event = Event.objects.filter(date__gt=current_event.date).order_by('date', 'pk').first()
        if not next_event:
            next_event = Event.objects.filter(date=current_event.date, pk__gt=current_event.pk).order_by('pk').first()
        return next_event

    @staticmethod
    def get_prev_event(current_event):
        """
        Get the previous event in timeline order (by date, then pk).
        """
        prev_event = Event.objects.filter(date__lt=current_event.date).order_by('-date', '-pk').first()
        if not prev_event:
            prev_event = Event.objects.filter(date=current_event.date, pk__lt=current_event.pk).order_by('-pk').first()
        return prev_event

    @staticmethod
    def link_photo_to_event(event, photo):
        """
        Link a photo to an event (if not already linked).
        """
        event.linked_photos.add(photo)
        event.save(update_fields=["linked_photos"])

    @staticmethod
    def unlink_photo_from_event(event, photo):
        """
        Unlink a photo from an event.
        """
        event.linked_photos.remove(photo)
        event.save(update_fields=["linked_photos"])

