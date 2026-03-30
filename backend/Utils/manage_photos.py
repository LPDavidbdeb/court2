# your_project_root/Utils/manage_photos.py

import os
import sys
import glob
from datetime import datetime
import json
from django.utils import timezone
#from PIL.ExifTags import IFDRational # <--- ADDED IMPORT for IFDRational handling
from fractions import Fraction # <--- ADDED IMPORT for general fraction handling

# --- IMPORTANT: Configure Django environment ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

# Now you can import your Django models
from photos.models import Photo

# --- Import your custom image models ---
try:
    from helpers.Picture import Picture
    from helpers.PictureJPEG import JPEG
    from helpers.PictureCR2 import CR2
    #from PIL import ExifTags # Used in your JPEG class
except ImportError as e:
    print(f"ERROR: Could not import custom image models from 'helpers' directory. Please check your Python path and file locations. Error: {e}")
    print(f"Attempted to add '{project_root}' to sys.path.")
    print("Current sys.path:", sys.path)
    sys.exit(1)


# --- Configuration ---
PARENT_DIR = os.path.join(project_root, 'DL', 'photos')
PARENT_DIR = os.path.join(project_root, 'DL/photos', 'set_D')

SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.cr2')

# --- Helper function to convert complex types for JSON serialization ---
def prepare_for_json_serialization(obj):
    if isinstance(obj, datetime):
        # Convert to aware datetime if naive, then to ISO format string
        if obj.tzinfo is None:
            obj = timezone.make_aware(obj)
        return obj.isoformat()
    elif isinstance(obj, bytes):
        # Decode bytes to string, ignoring errors for robust handling
        return obj.decode('utf-8', errors='ignore')

    elif isinstance(obj, dict):
        return {k: prepare_for_json_serialization(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [prepare_for_json_serialization(elem) for elem in obj]
    else:
        # For any other non-serializable type, try to convert to string
        # Or you could raise an error, but string conversion is more robust for general metadata
        try:
            json.dumps(obj) # Test if it's serializable by default
            return obj
        except TypeError:
            return str(obj) # Convert to string as a last resort


def get_picture_model_instance(file_path: str) -> Picture | None:
    """
    Instantiates the correct Picture subclass based on file extension.
    """
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in ('.jpg', '.jpeg'):
            return JPEG(file_path)
        elif ext == '.cr2':
            return CR2(file_path)
        else:
            print(f"Skipping unsupported file type: {file_path}")
            return None
    except RuntimeError as e:
        print(f"Dependency error for {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error instantiating model for {file_path}: {e}")
        return None


def crawl_and_store_photos(base_dir: str):
    """
    Crawls the specified base directory, extracts photo metadata,
    and stores it in the Django database.
    """
    if not os.path.isdir(base_dir):
        print(f"Error: Base directory '{base_dir}' not found. Please set PARENT_DIR correctly.")
        return

    print(f"Starting photo metadata crawl in: {os.path.abspath(base_dir)}")
    processed_count = 0
    skipped_count = 0
    error_count = 0

    for root, dirs, files in os.walk(base_dir):
        files.sort()
        dirs.sort()

        folder_name = os.path.basename(root)
        date_from_folder = None
        try:
            date_from_folder = datetime.strptime(folder_name, '%Y-%m-%d').date()
        except ValueError:
            pass

        for file_name in files:
            file_path = os.path.join(root, file_name)
            ext = os.path.splitext(file_name)[1].lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            try:
                if Photo.objects.filter(file_path=file_path).exists():
                    skipped_count += 1
                    continue

                picture_instance = get_picture_model_instance(file_path)

                if picture_instance:
                    metadata = picture_instance.get_metadata()

                    # Extract GPS data separately as it's nested
                    gps_latitude = None
                    gps_longitude = None
                    gps_altitude = None
                    gps_timestamp = None
                    if 'gps_data' in metadata and isinstance(metadata['gps_data'], dict):
                        gps_info = metadata['gps_data']
                        gps_latitude = gps_info.get('latitude')
                        gps_longitude = gps_info.get('longitude')
                        gps_altitude = gps_info.get('altitude')
                        gps_timestamp_val = gps_info.get('timestamp')
                        if isinstance(gps_timestamp_val, datetime):
                            gps_timestamp = timezone.make_aware(gps_timestamp_val) # Make aware

                    # Make all datetimes for direct model fields aware
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path)) if os.path.exists(file_path) else None
                    file_ctime = datetime.fromtimestamp(os.path.getctime(file_path)) if os.path.exists(file_path) else None
                    dt_original = metadata.get('DateTimeOriginal')

                    photo = Photo(
                        file_path=file_path,
                        file_name=file_name,
                        folder_path=root,
                        file_size=os.path.getsize(file_path) if os.path.exists(file_path) else None,
                        last_modified=timezone.make_aware(file_mtime) if file_mtime else None,
                        created_on_disk=timezone.make_aware(file_ctime) if file_ctime else None,

                        width=metadata.get('width') or metadata.get('raw_width'),
                        height=metadata.get('height') or metadata.get('raw_height'),
                        image_format=metadata.get('format', ext.upper().replace('.', '')),
                        image_mode=metadata.get('mode'),

                        make=metadata.get('Make') or metadata.get('make'),
                        model=metadata.get('Model') or metadata.get('model'),
                        datetime_original=timezone.make_aware(dt_original) if isinstance(dt_original, datetime) else None,
                        iso_speed=metadata.get('iso_speed') or metadata.get('ISOSpeedRatings'),
                        artist=metadata.get('Artist') or metadata.get('artist'),

                        exposure_time=metadata.get('ExposureTime'),
                        f_number=metadata.get('FNumber'),
                        focal_length=metadata.get('FocalLength'),
                        lens_model=metadata.get('LensModel'),

                        raw_width=metadata.get('raw_width'),
                        raw_height=metadata.get('raw_height'),
                        color_depth=metadata.get('color_depth'),
                        num_colors=metadata.get('num_colors'),
                        cfa_pattern=metadata.get('cfa_pattern'),

                        gps_latitude=gps_latitude,
                        gps_longitude=gps_longitude,
                        gps_altitude=gps_altitude,
                        gps_timestamp=gps_timestamp,

                        # Convert all metadata types to JSON-serializable types for all_metadata_json
                        all_metadata_json=prepare_for_json_serialization(metadata),
                        date_folder=date_from_folder
                    )
                    photo.save()
                    print(f"  Processed and saved: {file_name}")
                    processed_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"  Error processing {file_name}: {e}")
                error_count += 1

    print("\n--- Crawl Summary ---")
    print(f"Total processed: {processed_count}")
    print(f"Total skipped (already in DB or unsupported type): {skipped_count}")
    print(f"Total errors: {error_count}")
    print("Crawl finished.")

if __name__ == '__main__':
    crawl_and_store_photos(PARENT_DIR)