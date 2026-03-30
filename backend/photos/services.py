import os
import io
from datetime import datetime
from django.utils import timezone
from django.core.files.base import ContentFile
from PIL import Image
import exifread
import rawpy
import piexif

from .models import Photo

class PhotoProcessingService:
    """
    A service class containing the end-to-end logic for processing a photo file.
    """
    def __init__(self):
        self.supported_extensions = ('.jpg', '.jpeg', '.cr2')
        self.max_width = 1600
        self.jpeg_quality = 90

    def create_photo_from_upload(self, uploaded_file, photo_type=None, artist=None, datetime_original=None, gps_latitude=None, gps_longitude=None, custom_file_name=None):
        """
        Processes an in-memory uploaded file, combines it with user-provided metadata,
        and creates a new Photo object.
        """
        uploaded_file.seek(0)
        try:
            tags = exifread.process_file(uploaded_file, details=False)
        except Exception:
            tags = {}
        uploaded_file.seek(0)

        img = Image.open(uploaded_file)
        w, h = img.size

        if w > self.max_width:
            new_h = int(h * self.max_width / w)
            img = img.resize((self.max_width, new_h), Image.Resampling.LANCZOS)

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}}
        if artist:
            exif_dict["0th"][piexif.ImageIFD.Artist] = artist.encode('utf-8')
        if datetime_original:
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = datetime_original.strftime("%Y:%m:%d %H:%M:%S").encode()
        
        try:
            exif_bytes = piexif.dump(exif_dict)
        except Exception:
            exif_bytes = b''

        buffer = io.BytesIO()
        img.save(buffer, "JPEG", quality=self.jpeg_quality, exif=exif_bytes)
        processed_image_bytes = buffer.getvalue()

        # Use the custom file name if provided, otherwise fall back to the uploaded file's name
        file_name_to_use = custom_file_name or uploaded_file.name

        photo = Photo(
            photo_type=photo_type,
            artist=artist,
            datetime_original=datetime_original,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            file_name=file_name_to_use,
            file_size=uploaded_file.size,
            width=w,
            height=h,
            image_format=img.format,
            image_mode=img.mode,
            make=str(tags.get('Image Make', '')),
            model=str(tags.get('Image Model', '')),
            iso_speed=self._to_int(tags.get('EXIF ISOSpeedRatings')),
            exposure_time=str(tags.get('EXIF ExposureTime', '')),
            f_number=self._to_float(tags.get('EXIF FNumber')),
            focal_length=self._to_float(tags.get('EXIF FocalLength')),
            lens_model=str(tags.get('EXIF LensModel', '')),
        )

        new_filename = f"{os.path.splitext(file_name_to_use)[0]}.jpg"
        photo.file.save(new_filename, ContentFile(processed_image_bytes), save=False)
        photo.save()
        
        return photo

    def _parse_date(self, tags):
        for key in ('EXIF DateTimeOriginal', 'Image DateTime', 'EXIF DateTimeDigitized'):
            if key in tags:
                try:
                    dt_str = str(tags[key].values)
                    dt_naive = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                    return timezone.make_aware(dt_naive)
                except (ValueError, TypeError, AttributeError):
                    continue
        return None

    def _to_float(self, val):
        if val is None: return None
        try:
            if hasattr(val, 'values') and isinstance(val.values, list) and len(val.values) > 0:
                ratio = val.values[0]
                if hasattr(ratio, 'num'):
                    return float(ratio.num) / float(ratio.den)
                return float(ratio)
            val_str = str(val)
            if '/' in val_str:
                num, den = val_str.split('/')
                return float(num) / float(den)
            return float(val_str)
        except (ValueError, TypeError, ZeroDivisionError, AttributeError): return None

    def _to_int(self, val):
        if val is None: return None
        try: 
            if hasattr(val, 'values') and isinstance(val.values, list) and len(val.values) > 0:
                return int(val.values[0])
            float_val = self._to_float(val)
            if float_val is None:
                return None
            return int(float_val)
        except (ValueError, TypeError, AttributeError): return None

    def create_and_process_photo(self, source_path: str, datetime_original: datetime, photo_type=None):
        """
        Creates a Photo record and processes the associated image file,
        using a manually provided datetime.
        """
        if not os.path.exists(source_path):
            return None

        original_filename = os.path.basename(source_path)

        try:
            with open(source_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
        except Exception:
            tags = {}

        if original_filename.lower().endswith('.cr2'):
            with rawpy.imread(source_path) as raw:
                rgb = raw.postprocess()
            img = Image.fromarray(rgb)
        else:
            img = Image.open(source_path)

        w, h = img.size
        if w > self.max_width:
            new_h = int(h * self.max_width / w)
            img = img.resize((self.max_width, new_h), Image.Resampling.LANCZOS)

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        exif_dict = {"Exif": {piexif.ExifIFD.DateTimeOriginal: datetime_original.strftime("%Y:%m:%d %H:%M:%S").encode()}}
        try:
            exif_bytes = piexif.dump(exif_dict)
        except Exception:
            exif_bytes = b''

        buffer = io.BytesIO()
        img.save(buffer, "JPEG", quality=self.jpeg_quality, exif=exif_bytes)
        processed_image_bytes = buffer.getvalue()

        photo = Photo(
            file_path=source_path,
            file_name=original_filename,
            datetime_original=datetime_original,
            photo_type=photo_type,
            make=str(tags.get('Image Make', '')),
            model=str(tags.get('Image Model', '')),
            iso_speed=self._to_int(tags.get('EXIF ISOSpeedRatings')),
            exposure_time=str(tags.get('EXIF ExposureTime', '')),
            f_number=self._to_float(tags.get('EXIF FNumber')),
            focal_length=self._to_float(tags.get('EXIF FocalLength')),
            lens_model=str(tags.get('EXIF LensModel', '')),
        )
        
        new_filename = f"{os.path.splitext(original_filename)[0]}.jpg"
        photo.file.save(new_filename, ContentFile(processed_image_bytes), save=False)
        photo.save()
        
        return photo

    def process_photo_file(self, source_path: str, date_from_folder=None, photo_type=None):
        """
        Legacy method. Processes a photo where EXIF data is assumed to be present.
        """
        try:
            with open(source_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
        except Exception:
            return None

        datetime_original = self._parse_date(tags)
        if not datetime_original:
            return None

        return self.create_and_process_photo(source_path, datetime_original, photo_type)
