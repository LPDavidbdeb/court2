import os
import re
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import sys
import json
from django.core.files import File
from django.conf import settings

# --- IMPORTANT: Configure Django environment ---
# Find the project root dynamically
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

# Now you can import your Django models and custom Picture classes
from photos.models import Photo
from Utils.manage_photos import get_picture_model_instance, prepare_for_json_serialization


class Command(BaseCommand):
    help = 'Resets the Photo table and populates it with rich metadata from the consolidated directory.'

    def handle(self, *args, **options):
        consolidated_dir = '/Users/louis-philippedavid/Sites/Court/DL/photos/consolidated_pictures'
        BATCH_SIZE = 500  # Process files in batches of this size

        if not os.path.isdir(consolidated_dir):
            self.stdout.write(self.style.ERROR(f"Consolidated directory not found at: {consolidated_dir}"))
            return

        self.stdout.write(self.style.WARNING("Deleting all existing Photo objects..."))

        with transaction.atomic():
            Photo.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("All existing Photo objects deleted."))

        file_list = [os.path.join(consolidated_dir, f) for f in os.listdir(consolidated_dir) if
                     os.path.isfile(os.path.join(consolidated_dir, f))]
        total_files = len(file_list)
        self.stdout.write(self.style.SUCCESS(f"Found {total_files} files to process."))

        processed_count = 0

        for i in range(0, total_files, BATCH_SIZE):
            batch_files = file_list[i:i + BATCH_SIZE]
            self.stdout.write(f"\nProcessing batch {int(i / BATCH_SIZE) + 1} of {int(total_files / BATCH_SIZE) + 1}...")

            with transaction.atomic():
                for file_path in batch_files:
                    filename = os.path.basename(file_path)
                    try:
                        picture_instance = get_picture_model_instance(file_path)
                        if not picture_instance:
                            self.stdout.write(self.style.WARNING(f"Skipping unsupported file: {filename}"))
                            continue

                        metadata = picture_instance.get_metadata()

                        match = re.match(r'(\d{8}_\d{6})_(\d{4})(.+\..+)', filename)
                        filename_date = None
                        if match:
                            date_string = match.group(1)
                            try:
                                naive_datetime = datetime.strptime(date_string, "%Y%m%d_%H%M%S")
                                # Make naive filename datetime timezone-aware
                                filename_date = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
                            except ValueError:
                                pass

                        # Make all potential dates timezone-aware before comparison
                        all_dates = []
                        if metadata.get('DateTimeOriginal'):
                            all_dates.append(timezone.make_aware(metadata.get('DateTimeOriginal')))
                        if filename_date:
                            all_dates.append(filename_date)
                        if os.path.exists(file_path):
                            all_dates.append(timezone.make_aware(datetime.fromtimestamp(os.path.getmtime(file_path))))

                        smallest_date = min(all_dates, default=None)

                        gps_info = metadata.pop('gps_data', {})

                        photo = Photo(
                            file_name=filename,
                            folder_path=os.path.dirname(file_path),
                            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else None,
                            last_modified=timezone.make_aware(datetime.fromtimestamp(os.path.getmtime(file_path))),
                            created_on_disk=timezone.make_aware(datetime.fromtimestamp(os.path.getctime(file_path))),
                            width=metadata.get('width') or metadata.get('raw_width'),
                            height=metadata.get('height') or metadata.get('raw_height'),
                            image_format=metadata.get('format', os.path.splitext(filename)[1].lower().replace('.', '')),
                            image_mode=metadata.get('mode'),
                            make=metadata.get('make'),
                            model=metadata.get('model'),
                            datetime_original=smallest_date,
                            iso_speed=metadata.get('iso_speed'),
                            artist=metadata.get('artist'),
                            exposure_time=metadata.get('exposure_time'),
                            f_number=metadata.get('f_number'),
                            focal_length=metadata.get('focal_length'),
                            lens_model=metadata.get('lens_model'),
                            raw_width=metadata.get('raw_width'),
                            raw_height=metadata.get('raw_height'),
                            color_depth=metadata.get('color_depth'),
                            num_colors=metadata.get('num_colors'),
                            cfa_pattern=metadata.get('cfa_pattern'),
                            gps_latitude=gps_info.get('latitude'),
                            gps_longitude=gps_info.get('longitude'),
                            gps_altitude=gps_info.get('altitude'),
                            gps_timestamp=gps_info.get('timestamp'),
                            all_metadata_json=prepare_for_json_serialization(metadata),
                        )

                        with open(file_path, 'rb') as f:
                            photo.file.save(filename, File(f), save=False)

                        # Update the file_path with the new, final location
                        photo.file_path = photo.file.path
                        photo.save()

                        # Delete the original file to ensure only one copy exists
                        os.remove(file_path)

                        processed_count += 1

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Failed to create Photo object for {filename}: {e}"))

            self.stdout.write(
                self.style.SUCCESS(f"Batch {int(i / BATCH_SIZE) + 1} completed. Processed {len(batch_files)} photos."))

        self.stdout.write(
            self.style.SUCCESS(f"\nCompleted! {processed_count} photos were successfully added to the database."))
