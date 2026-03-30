import os
import re
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils import timezone
from photos.models import Photo
from PIL import Image, ExifTags

# Pre-compile regex for performance
date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}_\d{2}_\d{2})')

# Helper to get EXIF data
def get_exif_datetime(image_path):
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    if ExifTags.TAGS.get(tag) == 'DateTimeOriginal':
                        return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
    except Exception:
        return None
    return None

class Command(BaseCommand):
    help = 'Links files and updates datetime_original from EXIF, with filename verification.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting photo file processing..."))
        all_photos = Photo.objects.all()
        self.stdout.write(f"Found {all_photos.count()} total photos to check.")

        for photo in all_photos:
            updated = False
            try:
                # --- Part 1: Link file if missing ---
                if not photo.file and photo.file_path and os.path.exists(photo.file_path):
                    with open(photo.file_path, 'rb') as f:
                        photo.file = File(f, name=os.path.basename(photo.file_path))
                        updated = True
                        self.stdout.write(self.style.SUCCESS(f"[File Linked] PK {photo.pk}"))

                # --- Part 2: Process datetime ---
                if not photo.datetime_original and photo.file_path and os.path.exists(photo.file_path):
                    exif_dt = get_exif_datetime(photo.file_path)
                    filename_dt = None
                    match = date_pattern.search(photo.file_name)
                    if match:
                        filename_dt = datetime.strptime(match.group(1), '%Y-%m-%d %H_%M_%S')

                    # Prioritize EXIF data
                    if exif_dt:
                        photo.datetime_original = timezone.make_aware(exif_dt)
                        updated = True
                        self.stdout.write(self.style.SUCCESS(f"[EXIF Date] PK {photo.pk}: Set to {photo.datetime_original}"))
                        # Verification step
                        if filename_dt and abs((exif_dt - filename_dt).total_seconds()) > 1:
                            self.stdout.write(self.style.WARNING(f"  - WARNING: PK {photo.pk} - EXIF date ({exif_dt}) and filename date ({filename_dt}) do not match."))
                    # Fallback to filename if no EXIF date
                    elif filename_dt:
                        photo.datetime_original = timezone.make_aware(filename_dt)
                        updated = True
                        self.stdout.write(self.style.SUCCESS(f"[Filename Date] PK {photo.pk}: Set to {photo.datetime_original} (no EXIF date found)."))

                if updated:
                    photo.save()

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An error occurred processing Photo PK {photo.pk}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nProcessing finished."))
