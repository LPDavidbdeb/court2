import os
import sys
import pandas as pd
import json
from datetime import datetime
from django.utils import timezone
from django.core.files import File
from django.db import connection, transaction
from PIL import Image, ExifTags
import exifread

# --- Configure Django Environment ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()

# --- Model Imports ---
from photos.models import Photo

class PhotoProcessor:
    """
    A class to handle the discovery and import of photos using both Pillow and exifread.
    """
    def __init__(self):
        self.supported_extensions = ('.jpg', '.jpeg')

    def _get_pil_metadata(self, file_path):
        """Extracts metadata using Pillow, safely converting all values to strings and prefixing keys."""
        metadata = {}
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, f"unknown_tag_{tag_id}")
                        key = f"pil_{tag_name}"
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore')
                        metadata[key] = str(value)
        except Exception as e:
            metadata['pil_error'] = str(e)
        return metadata

    def _get_exifread_metadata(self, file_path):
        """Extracts metadata using exifread, safely converting all values to strings and prefixing keys."""
        metadata = {}
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
            for tag, value in tags.items():
                clean_tag = str(tag).replace(" ", "_")
                key = f"exifread_{clean_tag}"
                metadata[key] = str(value)
        except Exception as e:
            metadata['exifread_error'] = str(e)
        return metadata

    def discover_photos(self, source_directory: str) -> pd.DataFrame:
        """
        Crawls a source directory and extracts all metadata using both Pillow and exifread.
        """
        print(f"--- Starting Discovery in '{source_directory}' ---")
        records = []
        error_count = 0

        if not os.path.isdir(source_directory):
            print(f"[Error] Source directory not found: {source_directory}")
            return pd.DataFrame()

        for root, _, files in os.walk(source_directory):
            for file_name in sorted(files):
                if not file_name.lower().endswith(self.supported_extensions):
                    continue

                file_path = os.path.join(root, file_name)
                try:
                    pil_data = self._get_pil_metadata(file_path)
                    exifread_data = self._get_exifread_metadata(file_path)
                    
                    combined_data = {**pil_data, **exifread_data}
                    combined_data['source_file_path'] = file_path
                    combined_data['file_name'] = file_name
                    records.append(combined_data)

                except Exception as e:
                    print(f"  - [FATAL ERROR] Could not process {file_path}: {e}")
                    error_count += 1
                    continue

        df = pd.DataFrame(records)
        print(f"--- Discovery Complete ---")
        print(f"Found and processed metadata for {len(df)} photos.")
        print(f"{error_count} files were skipped due to fatal errors.")
        return df

    def _to_aware_datetime(self, dt_str):
        if not dt_str or pd.isna(dt_str): return None
        try:
            dt = datetime.strptime(str(dt_str), '%Y:%m:%d %H:%M:%S')
            return timezone.make_aware(dt)
        except (ValueError, TypeError): return None

    def _to_float(self, val):
        if val is None or pd.isna(val): return None
        try:
            val_str = str(val)
            if '/' in val_str:
                num, den = val_str.split('/')
                return float(num) / float(den)
            return float(val_str)
        except (ValueError, TypeError, ZeroDivisionError): return None

    def _to_int(self, val):
        if val is None or pd.isna(val): return None
        try: return int(self._to_float(val))
        except (ValueError, TypeError): return None

    def _clean_for_json(self, data_row):
        """Converts a Pandas row to a JSON-serializable dictionary."""
        clean_dict = {}
        for key, value in data_row.items():
            if pd.isna(value):
                continue
            if isinstance(value, datetime):
                clean_dict[key] = value.isoformat()
            else:
                clean_dict[key] = str(value)
        return clean_dict

    @transaction.atomic
    def commit_to_database(self, photo_dataframe: pd.DataFrame):
        print("\n--- Starting Database Commit ---")
        
        print("  - Deleting existing photo files...")
        for photo in Photo.objects.all():
            if photo.file and hasattr(photo.file, 'path') and os.path.exists(photo.file.path):
                try:
                    os.remove(photo.file.path)
                except OSError as e:
                    print(f"  - [Error] Could not delete file {photo.file.path}: {e}")
        print(f"  - Deleted existing files.")

        print("  - Truncating Photo table...")
        with connection.cursor() as cursor:
            cursor.execute(f"SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute(f"TRUNCATE TABLE {Photo._meta.db_table};")
            cursor.execute(f"SET FOREIGN_KEY_CHECKS = 1;")
        print("  - Table truncated.")

        print(f"  - Starting import of {len(photo_dataframe)} photos...")
        for index, row in photo_dataframe.iterrows():
            source_path = row['source_file_path']
            dt_original = self._to_aware_datetime(row.get('pil_DateTimeOriginal') or row.get('exifread_EXIF_DateTimeOriginal'))
            if not dt_original:
                continue

            photo = Photo(
                file_path=source_path,
                file_name=row.get('file_name'),
                datetime_original=dt_original,
                make=row.get('pil_Make') or row.get('exifread_Image_Make'),
                model=row.get('pil_Model') or row.get('exifread_Image_Model'),
                iso_speed=self._to_int(row.get('pil_ISOSpeedRatings') or row.get('exifread_EXIF_ISOSpeedRatings')),
                exposure_time=str(row.get('pil_ExposureTime') or row.get('exifread_EXIF_ExposureTime', '')),
                f_number=self._to_float(row.get('pil_FNumber') or row.get('exifread_EXIF_FNumber')),
                focal_length=self._to_float(row.get('pil_FocalLength') or row.get('exifread_EXIF_FocalLength')),
                lens_model=row.get('exifread_EXIF_LensModel'),
                artist=row.get('pil_Artist') or row.get('exifread_Image_Artist'),
                all_metadata_json=self._clean_for_json(row),
            )

            with open(source_path, 'rb') as f:
                photo.file.save(row['file_name'], File(f), save=True)

        print(f"--- Database Commit Complete: Imported {photo_dataframe.index.size} photos. ---")
