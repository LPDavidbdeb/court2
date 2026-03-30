import os
from django.core.management.base import BaseCommand
from photos.models import Photo
from django.conf import settings

class Command(BaseCommand):
    help = 'Fixes incorrect photo file paths that contain "/2025/12/04/"'

    def handle(self, *args, **options):
        self.stdout.write("Starting to fix photo paths...")

        incorrect_photos = Photo.objects.filter(file__contains="/2025/12/04/")
        self.stdout.write(f"Found {incorrect_photos.count()} photos with incorrect paths.")

        base_media_path = settings.MEDIA_ROOT

        search_base_dirs = [
            os.path.join(base_media_path, 'photos', '2025', '11', '19'),
            os.path.join(base_media_path, 'photos', '2025', '11', '28'),
            os.path.join(base_media_path, 'photos', '2025', '12', '02'),
        ]

        for photo in incorrect_photos:
            original_path = photo.file.name
            filename_to_find = os.path.basename(original_path)
            found_new_path = False

            for base_dir in search_base_dirs:
                potential_physical_path = os.path.join(base_dir, filename_to_find)
                if os.path.exists(potential_physical_path):
                    new_relative_path = os.path.relpath(potential_physical_path, base_media_path)
                    photo.file.name = new_relative_path
                    photo.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated photo {photo.pk}: '{original_path}' -> '{new_relative_path}'"))
                    found_new_path = True
                    break
            
            if not found_new_path:
                self.stdout.write(self.style.WARNING(f"Could not find a matching file for photo {photo.pk} (filename: '{filename_to_find}') in any search directory."))

        self.stdout.write("Finished fixing photo paths.")
