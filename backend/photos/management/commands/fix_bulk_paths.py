import os
from django.core.management.base import BaseCommand
from django.conf import settings
from photos.models import Photo


class Command(BaseCommand):
    help = 'Fixes local DB paths by stripping the incorrect "2025/12/04/" prefix.'

    def handle(self, *args, **options):
        # 1. ROBUST SAFETY CHECK (Fixes the AttributeError crash)
        is_google = False

        # Check new Django 5+ STORAGES setting
        if hasattr(settings, 'STORAGES'):
            default_backend = settings.STORAGES.get('default', {}).get('BACKEND', '')
            if 'google' in default_backend.lower() or 'gcloud' in default_backend.lower():
                is_google = True

        # Fallback check for older setting (using getattr to avoid crash)
        elif getattr(settings, 'DEFAULT_FILE_STORAGE', None):
            if 'google' in settings.DEFAULT_FILE_STORAGE.lower():
                is_google = True

        if is_google:
            self.stdout.write(
                self.style.ERROR("STOP! You are connected to Google Cloud. This script is for LOCAL fixing only."))
            return

        # 2. CONFIGURATION
        # The prefix to strip (from your Jupyter test results)
        PREFIX_TO_STRIP = "2025/12/04/"

        self.stdout.write(f"Fixing paths in Local DB (Media Root: {settings.MEDIA_ROOT})...")

        # 3. EXECUTION
        photos = Photo.objects.all()
        fixed_count = 0
        skipped_count = 0

        for photo in photos:
            if not photo.file:
                continue

            current_path = photo.file.name

            # Only process if it has the bad prefix
            if PREFIX_TO_STRIP in current_path:
                # Calculate the new path
                new_path = current_path.replace(PREFIX_TO_STRIP, "")

                # Verify the file actually exists at the new location locally
                full_local_path = os.path.join(settings.MEDIA_ROOT, new_path)

                if os.path.exists(full_local_path):
                    photo.file.name = new_path
                    photo.save(update_fields=['file'])
                    fixed_count += 1
                    if fixed_count % 100 == 0:
                        self.stdout.write(f"Fixed {fixed_count}...")
                else:
                    skipped_count += 1
            else:
                pass

        self.stdout.write(self.style.SUCCESS(f"✅ DONE! Successfully fixed {fixed_count} records."))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Skipped {skipped_count} files because they weren't found at the expected local path."))