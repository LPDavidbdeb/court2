import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.storage import default_storage
from django.conf import settings
from photos.models import Photo


class Command(BaseCommand):
    help = 'Uploads files currently in the local "media" folder to Google Cloud.'

    def handle(self, *args, **options):
        # 1. Safety Check
        is_google_storage = False
        if hasattr(settings, 'STORAGES'):
            backend = settings.STORAGES.get('default', {}).get('BACKEND', '').lower()
            if 'google' in backend or 'gcloud' in backend:
                is_google_storage = True
        elif hasattr(settings, 'DEFAULT_FILE_STORAGE'):
            if 'google' in settings.DEFAULT_FILE_STORAGE.lower():
                is_google_storage = True

        if not is_google_storage:
            self.stdout.write(self.style.ERROR(
                "ERROR: Google Cloud Storage is not active. Run with --settings=mysite.settings.remote"))
            return

        # 2. Define Local Media Root
        # This is where your website is currently finding the images
        local_media_root = os.path.join(settings.BASE_DIR, 'media')
        self.stdout.write(f"Looking for files in: {local_media_root}")

        # 3. Process Photos
        photos = Photo.objects.all().order_by('pk')
        total = photos.count()
        self.stdout.write(f"Checking {total} photos...")

        for i, photo in enumerate(photos):
            # A. Skip if no file is recorded in DB
            if not photo.file or not photo.file.name:
                self.stdout.write(
                    self.style.WARNING(f"[{i + 1}/{total}] SKIPPING: No file associated with Photo {photo.pk}"))
                continue

            # B. Check Cloud (Skip if already uploaded)
            # This asks Google: "Do you have 'photos/my_image.jpg'?"
            if default_storage.exists(photo.file.name):
                self.stdout.write(self.style.SUCCESS(f"[{i + 1}/{total}] SKIPPING (In Cloud): {photo.pk}"))
                continue

            # C. Find the file in the LOCAL 'media' folder
            # We manually build the path because 'photo.file.path' might try to call the Cloud
            full_local_path = os.path.join(local_media_root, photo.file.name)

            if os.path.exists(full_local_path):
                try:
                    # D. Upload
                    with open(full_local_path, 'rb') as f:
                        django_file = File(f)
                        # We re-save the file using its CURRENT name.
                        # This takes the bytes from local disk -> sends to Cloud -> keeps same name in DB
                        current_filename = os.path.basename(photo.file.name)
                        photo.file.save(current_filename, django_file, save=True)

                    self.stdout.write(self.style.SUCCESS(f"[{i + 1}/{total}] UPLOADED: {current_filename}"))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"[{i + 1}/{total}] FAILED Upload: {e}"))
            else:
                # This is a true "Missing File" - DB says it's here, but disk says no.
                self.stdout.write(self.style.ERROR(f"[{i + 1}/{total}] MISSING: {full_local_path}"))

        self.stdout.write(self.style.SUCCESS("Photo verification and upload complete."))