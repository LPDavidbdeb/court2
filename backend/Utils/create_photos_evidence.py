# your_project_root/Utils/create_daily_photo_evidence.py

import os
import sys
from datetime import date
from collections import defaultdict

# --- IMPORTANT: Configure Django environment ---
# This block sets up the Django environment so your script can access models.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

# Now you can import your Django models
from photos.models import Photo
from events.models import Event

def create_daily_photo_evidence():
    print("Starting creation of daily photo supporting evidence...")

    # Fetch all photos that have a 'datetime_original' set, ordered by date
    # Exclude photos where datetime_original is null as they can't be grouped by day
    all_photos = Photo.objects.exclude(datetime_original__isnull=True).order_by('datetime_original')

    if not all_photos.exists():
        print("No photos with 'datetime_original' found. Exiting.")
        return

    # Group photos by their original date
    # defaultdict helps automatically create empty lists for new dates
    photos_by_date = defaultdict(list)
    for photo in all_photos:
        # Extract only the date part from the datetime_original field
        photo_date = photo.datetime_original.date()
        photos_by_date[photo_date].append(photo)

    processed_evidence_count = 0
    skipped_evidence_count = 0
    total_photos_linked_count = 0

    # Iterate through each unique date found
    # Sorting the dates for predictable output
    for photo_date in sorted(photos_by_date.keys()):
        photos_for_day = photos_by_date[photo_date]
        num_photos_on_day = len(photos_for_day)

        # Construct unique description and explanation for this day's evidence
        description_text = f"Photos from {photo_date.strftime('%Y-%m-%d')}"
        explanation_text = (
            f"This supporting evidence links to all {num_photos_on_day} photos "
            f"captured on {photo_date.strftime('%Y-%m-%d')}."
        )

        # --- Idempotency Check: Find existing evidence for this day ---
        # We filter by start_date and description to identify if this specific daily evidence already exists.
        evidence_instance = Event.objects.filter(
            start_date=photo_date,
            end_date=photo_date, # Assuming daily evidence has same start and end date
            description=description_text
        ).first() # .first() gets the object or None if not found

        if evidence_instance:
            # Evidence already exists, so we just link photos to it
            skipped_evidence_count += 1
            print(f"  Skipped creating evidence for {photo_date} (exists as {evidence_instance.get_display_id()}).")
        else:
            # No existing evidence found, so create a new one
            evidence_instance = Event.objects.create(
                start_date=photo_date,
                end_date=photo_date, # For a single day, start and end date are the same
                description=description_text,
                explanation=explanation_text
            )
            processed_evidence_count += 1
            print(f"  Created new evidence {evidence_instance.get_display_id()} for {photo_date}.")

        # --- Link all photos for this day to the evidence instance ---
        # The .add() method for ManyToManyFields automatically handles existing relationships,
        # meaning it will not create duplicate links if a photo is already linked.
        evidence_instance.linked_photos.add(*photos_for_day)
        total_photos_linked_count += num_photos_on_day
        print(f"    Linked {num_photos_on_day} photo(s) to {evidence_instance.get_display_id()}.")


    print("\n--- Script Summary ---")
    print(f"Total unique days with photos processed: {len(photos_by_date)}")
    print(f"Supporting Evidence instances created: {processed_evidence_count}")
    print(f"Supporting Evidence instances skipped (already existed): {skipped_evidence_count}")
    print(f"Total photos linked across all evidence: {total_photos_linked_count}")
    print("Script finished.")

if __name__ == '__main__':
    create_daily_photo_evidence()