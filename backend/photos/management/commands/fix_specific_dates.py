import os
from django.core.management.base import BaseCommand
from django.conf import settings
from photos.models import Photo


class Command(BaseCommand):
    help = 'Fixes ALL records containing the incorrect "2025/12/04/" date by checking valid source folders.'

    def handle(self, *args, **options):
        # 1. Safety Check: Ensure we are offline
        is_google = False
        if hasattr(settings, 'STORAGES'):
            default_backend = settings.STORAGES.get('default', {}).get('BACKEND', '')
            if 'google' in default_backend.lower(): is_google = True
        elif getattr(settings, 'DEFAULT_FILE_STORAGE', None):
            if 'google' in settings.DEFAULT_FILE_STORAGE.lower(): is_google = True

        if is_google:
            self.stdout.write(self.style.ERROR("STOP! Switch to Local Settings first."))
            return

        # 2. Configuration
        BROKEN_PATTERN = "2025/12/04/"

        # The folders where you know the files actually live
        # Paths are relative to your MEDIA_ROOT
        TARGET_FOLDERS = [
            "photos/2025/11/19",
            "photos/2025/11/28",
            "photos/2025/12/02",
        ]

        self.stdout.write(f"Searching for ALL records containing '{BROKEN_PATTERN}'...")

        # 3. Get the target list
        # We use 'contains' to find any path with that date string
        broken_photos = Photo.objects.filter(file__contains=BROKEN_PATTERN)
        total_count = broken_photos.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("No broken records found!"))
            return

        self.stdout.write(f"Found {total_count} records to check.")

        fixed_count = 0
        missing_count = 0

        for photo in broken_photos:
            # Extract the filename (e.g. "image.jpg")
            # We prefer the stored file_name, but fallback to the basename of the file path
            filename = photo.file_name or os.path.basename(photo.file.name)
            filename = filename.replace(" ", "_" )

            found = False

            # 4. Hunt for the file
            for folder in TARGET_FOLDERS:
                # Construct the physical path: /Users/.../media/photos/2025/11/19/image.jpg
                potential_path_on_disk = os.path.join(settings.MEDIA_ROOT, folder, filename)

                if os.path.exists(potential_path_on_disk):
                    # Found it!
                    # Django needs the relative path: "photos/2025/11/19/image.jpg"
                    new_db_path = os.path.join(folder, filename)

                    # Update DB
                    old_path = photo.file.name
                    photo.file.name = new_db_path
                    photo.save(update_fields=['file'])

                    self.stdout.write(self.style.SUCCESS(f"✅ FIXED: {filename}"))
                    # self.stdout.write(f"   Old: {old_path}") # Uncomment for detail
                    # self.stdout.write(f"   New: {new_db_path}")

                    fixed_count += 1
                    found = True
                    break  # Stop searching folders for this photo

            if not found:
                missing_count += 1
                self.stdout.write(self.style.ERROR(f"❌ COULD NOT FIND: {filename} in any target folder."))

        # 5. Final Report
        self.stdout.write("\n" + "-" * 30)
        self.stdout.write(self.style.SUCCESS(f"BATCH COMPLETE"))
        self.stdout.write(f"Total Scanned: {total_count}")
        self.stdout.write(f"Fixed:         {fixed_count}")
        self.stdout.write(f"Still Missing: {missing_count}")