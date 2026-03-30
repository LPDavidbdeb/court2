from django.core.management.base import BaseCommand
from django.db import transaction
from photos.models import Photo, PhotoType
from events.models import Event
from datetime import timedelta

class Command(BaseCommand):
    help = 'Deletes all existing events and re-clusters photos of type \'Life Event\' into new Event objects.'

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Perform a "Clean Install" by deleting all existing events
        self.stdout.write(self.style.WARNING("Deleting all existing Event objects..."))
        count, _ = Event.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {count} old event objects."))

        # 2. Re-cluster photos
        self.stdout.write("Starting photo clustering to create new events...")
        
        # MODIFIED: Only select photos of type 'Life Event' for clustering.
        try:
            life_event_type = PhotoType.objects.get(name='Life Event')
        except PhotoType.DoesNotExist:
            self.stdout.write(self.style.ERROR("The PhotoType 'Life Event' does not exist. Please create it before running this command."))
            return

        photos_to_cluster = Photo.objects.filter(
            datetime_original__isnull=False,
            photo_type=life_event_type
        ).order_by('datetime_original')

        if not photos_to_cluster.exists():
            self.stdout.write(self.style.SUCCESS("No 'Life Event' photos with dates found to cluster."))
            return

        event_break_threshold = timedelta(hours=2)
        current_cluster = []
        
        for photo in photos_to_cluster:
            if not current_cluster:
                current_cluster.append(photo)
                continue

            last_photo_time = current_cluster[-1].datetime_original
            current_photo_time = photo.datetime_original

            if (current_photo_time - last_photo_time) > event_break_threshold:
                self.create_event_from_cluster(current_cluster)
                current_cluster = [photo]
            else:
                current_cluster.append(photo)
        
        if current_cluster:
            self.create_event_from_cluster(current_cluster)

        self.stdout.write(self.style.SUCCESS("Photo clustering complete."))

    def create_event_from_cluster(self, photos):
        if not photos:
            return

        photos.sort(key=lambda p: p.datetime_original)
        start_time = photos[0].datetime_original
        end_time = photos[-1].datetime_original

        # Create the explanation text in the desired format
        explanation_template = (
            f"On {start_time.strftime('%Y-%m-%d')} between "
            f"{start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}: "
        )
        
        # Create the new event object with the correct data
        event = Event.objects.create(
            date=start_time.date(),
            explanation=explanation_template
        )
        
        event.linked_photos.add(*photos)
        
        self.stdout.write(f"  Created event for cluster of {len(photos)} photos from {start_time.date()}.")
