# your_project_root/Models/JPEG.py

import os
from datetime import datetime
from dateutil import parser
from PIL import Image, ExifTags # Make sure to install Pillow: pip install Pillow

from helpers.Picture import Picture # Assuming direct import path

class JPEG(Picture):
    """
    Represents a JPEG image and extracts its metadata using Pillow.
    This class handles local JPEG files.
    """

    def __init__(self, file_path: str):
        # Call the base class __init__ with the file_path as source_identifier
        super().__init__(source_identifier=file_path)

        # Check validity immediately for local files
        if not self._check_source_validity():
            raise FileNotFoundError(f"JPEG file not found: {self.source_identifier}")

        # Ensure Pillow is available
        if Image is None: # This check is actually redundant if Pillow is installed or it would error on import
            raise RuntimeError("Pillow library not installed. Cannot process JPEG files.")

        # Load common file-system metadata first
        self.load_common_metadata()
        # Then load JPEG/EXIF specific metadata
        self.load_metadata()

    def _check_source_validity(self) -> bool:
        """
        Verifies if the local JPEG file exists on disk.
        """
        return os.path.exists(self.source_identifier)

    def load_common_metadata(self):
        """
        Loads common file system metadata for local JPEG files.
        Populates file_path, file_name, folder_path, file_size, last_modified, created_on_disk.
        """
        try:
            stat_info = os.stat(self.source_identifier)
            self._metadata['file_size'] = stat_info.st_size
            self._metadata['last_modified'] = datetime.fromtimestamp(stat_info.st_mtime)
            self._metadata['created_on_disk'] = datetime.fromtimestamp(stat_info.st_ctime)
            # These are also properties of the base Picture class, but storing them in _metadata
            # makes them consistent with the get_metadata() dict.
            self._metadata['file_name'] = os.path.basename(self.source_identifier)
            self._metadata['folder_path'] = os.path.dirname(self.source_identifier)
        except Exception as e:
            print(f"Error loading common metadata for {self.source_identifier}: {e}")

    def load_metadata(self):
        """Loads metadata specific to JPEG files, including EXIF data using Pillow."""
        try:
            with Image.open(self.source_identifier) as img:
                # Basic image dimensions from Pillow
                self._metadata['width'] = img.width
                self._metadata['height'] = img.height
                self._metadata['format'] = img.format
                self._metadata['mode'] = img.mode

                # Extract EXIF data
                exif_data = img._getexif()
                if exif_data:
                    # Reverse mapping for easier lookup of EXIF tag names
                    # This maps integer tag IDs to human-readable names
                    exif_tags_map = {v: k for k, v in ExifTags.TAGS.items()}
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        # Store raw EXIF values, or process specific ones
                        self._metadata[f"exif_{tag_name.replace(' ', '_').lower()}"] = value # Prefix to avoid conflicts

                    # Map common EXIF fields to generic property names
                    self._metadata['make'] = self._metadata.get(ExifTags.TAGS.get(271)) # 271: Make
                    self._metadata['model'] = self._metadata.get(ExifTags.TAGS.get(272)) # 272: Model
                    # DateTimeOriginal - often 36867
                    datetime_original_raw = self._metadata.get(ExifTags.TAGS.get(36867))
                    if datetime_original_raw:
                        try:
                            # EXIF date format is "YYYY:MM:DD HH:MM:SS"
                            # Replace first two colons with hyphens for dateutil.parser to handle
                            self._metadata['DateTimeOriginal'] = parser.parse(datetime_original_raw.replace(":", "-", 2))
                        except ValueError:
                            # Fallback to raw string if parsing fails
                            self._metadata['DateTimeOriginal'] = datetime_original_raw
                    else:
                         self._metadata['DateTimeOriginal'] = None # Ensure it's None if not found

                # Clean up empty values (optional, but good practice for smaller dict)
                self._metadata = {k: v for k, v in self._metadata.items() if v is not None}

        except Exception as e:
            print(f"Error loading JPEG metadata for {self.source_identifier}: {e}")
            self._metadata = {'error': str(e)} # Store error to signal issue with this file

    # Override base properties if the specific local loading is preferred
    @property
    def file_name(self):
        return self._metadata.get('file_name')

    @property
    def folder_path(self):
        return self._metadata.get('folder_path')

    @property
    def file_size(self):
        return self._metadata.get('file_size')

    @property
    def last_modified(self):
        return self._metadata.get('last_modified')

    @property
    def image_format(self):
        return self._metadata.get('format') # From Pillow's img.format