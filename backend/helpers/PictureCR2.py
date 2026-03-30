# your_project_root/Models/CR2.py

import os
from datetime import datetime
import rawpy # Make sure to install rawpy: pip install rawpy

from helpers.Picture import Picture # Assuming direct import path

class CR2(Picture):
    """
    Represents a Canon CR2 raw image and extracts its metadata using rawpy.
    This class handles local CR2 files.
    """

    def __init__(self, file_path: str):
        # Call the base class __init__ with the file_path as source_identifier
        super().__init__(source_identifier=file_path)

        # Check validity immediately for local files
        if not self._check_source_validity():
            raise FileNotFoundError(f"CR2 file not found: {self.source_identifier}")

        # Ensure rawpy is available
        if rawpy is None: # This check is actually redundant if rawpy is installed or it would error on import
            raise RuntimeError("rawpy library not installed. Cannot process CR2 files.")

        # Load common file-system metadata first
        self.load_common_metadata()
        # Then load CR2-specific metadata
        self.load_metadata()

    def _check_source_validity(self) -> bool:
        """
        Verifies if the local CR2 file exists on disk.
        """
        return os.path.exists(self.source_identifier)

    def load_common_metadata(self):
        """
        Loads common file system metadata for local CR2 files.
        Populates file_path, file_name, folder_path, file_size, last_modified, created_on_disk.
        """
        try:
            stat_info = os.stat(self.source_identifier)
            self._metadata['file_size'] = stat_info.st_size
            self._metadata['last_modified'] = datetime.fromtimestamp(stat_info.st_mtime)
            self._metadata['created_on_disk'] = datetime.fromtimestamp(stat_info.st_ctime)
            self._metadata['file_name'] = os.path.basename(self.source_identifier)
            self._metadata['folder_path'] = os.path.dirname(self.source_identifier)
        except Exception as e:
            print(f"Error loading common metadata for {self.source_identifier}: {e}")

    def load_metadata(self):
        """Loads metadata specific to CR2 files using rawpy."""
        try:
            with rawpy.imread(self.source_identifier) as raw:
                # Basic image dimensions - rawpy usually has 'sizes' attributes directly
                # Note: rawpy's output is often more direct, so no need for 'raw.sizes' object usually
                self._metadata['width'] = getattr(raw.sizes, 'width', None) # Standard width
                self._metadata['height'] = getattr(raw.sizes, 'height', None) # Standard height
                self._metadata['raw_width'] = getattr(raw.sizes, 'raw_width', None) # Raw sensor width
                self._metadata['raw_height'] = getattr(raw.sizes, 'raw_height', None) # Raw sensor height

                self._metadata['color_depth'] = getattr(raw, 'color_depth', None)
                self._metadata['num_colors'] = getattr(raw, 'num_colors', None)

                cfa_pattern_val = getattr(raw.sizes, 'cfa_pattern', None)
                self._metadata['cfa_pattern'] = cfa_pattern_val.tolist() if cfa_pattern_val is not None else None

                self._metadata['iso_speed'] = getattr(raw, 'iso_speed', None)

                # EXIF data (rawpy directly parses some common fields)
                self._metadata['make'] = getattr(raw, 'make', None)
                self._metadata['model'] = getattr(raw, 'model', None)
                self._metadata['artist'] = getattr(raw, 'artist', None)

                # Date Time Original
                # rawpy.date_times is an object, access its 'original' attribute
                original_dt = getattr(getattr(raw, 'date_times', None), 'original', None)
                if isinstance(original_dt, datetime): # rawpy often returns datetime object directly
                     self._metadata['DateTimeOriginal'] = original_dt
                elif original_dt: # If it's a timestamp string/number
                    try:
                        self._metadata['DateTimeOriginal'] = datetime.fromtimestamp(original_dt)
                    except (ValueError, TypeError):
                        self._metadata['DateTimeOriginal'] = None # Set to None if parsing fails
                else:
                    self._metadata['DateTimeOriginal'] = None


                # GPS info (if available)
                gps_obj = getattr(raw, 'gps', None)
                if gps_obj:
                    # rawpy.gps attributes
                    self._metadata['gps_data'] = {
                        'latitude': getattr(gps_obj, 'latitude', None),
                        'longitude': getattr(gps_obj, 'longitude', None),
                        'altitude': getattr(gps_obj, 'altitude', None),
                        'timestamp': getattr(gps_obj, 'timestamp', None) # rawpy often gives datetime for timestamp here
                    }
                else:
                    self._metadata['gps_data'] = {} # Ensure gps_data is an empty dict if no GPS info

                # Clean up empty values (optional, but good practice for smaller dict)
                self._metadata = {k: v for k, v in self._metadata.items() if v is not None}

        except Exception as e:
            print(f"Error loading CR2 metadata for {self.source_identifier}: {e}")
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
        return "CR2" # Hardcode for CR2 files