# your_project_root/Models/Picture.py

import os
from datetime import datetime
from abc import ABC, abstractmethod

class Picture(ABC):
    """
    Base class for representing a picture.
    Handles common metadata (file system for local, or general for abstract sources).
    Defines abstract methods for source-specific validity and metadata loading.
    """
    def __init__(self, source_identifier: str):
        """
        Initializes the Picture base class.

        Args:
            source_identifier (str): A string that uniquely identifies the picture's source.
                                     For local files, this would be the file path.
                                     For remote files, it could be a URL or an ID.
        """
        self.source_identifier = source_identifier
        self._metadata = {} # Initialize metadata dictionary

        # We defer specific validation and common metadata loading to subclasses
        # or dedicated methods. The base class itself doesn't assume local file existence.

        # Note: We do NOT call load_metadata() here directly in the base class,
        # as it's abstract. Subclasses should call it.
        # We also do NOT call _check_source_validity() here, as it might
        # involve network calls that are better managed by the subclass
        # when it has all necessary info (e.g., after init with API data).

    @abstractmethod
    def _check_source_validity(self) -> bool:
        """
        Abstract method to verify the existence or validity of the picture's source.
        For local files, this might check os.path.exists.
        For remote files, this might involve an API call to confirm existence/status.
        Returns True if the source is valid, False otherwise.
        """
        pass

    @abstractmethod
    def load_metadata(self):
        """
        Abstract method to be implemented by subclasses for specific metadata extraction.
        This method should populate self._metadata.
        """
        pass

    # New method to standardize common metadata loading based on source type
    @abstractmethod
    def load_common_metadata(self):
        """
        Abstract method to load metadata common across all Picture types,
        but whose source depends on the concrete implementation (e.g., file system, API).
        This should populate self._metadata with general attributes like
        'file_size', 'last_modified', 'created_on_disk' (for local) or their equivalents.
        """
        pass

    def get_metadata(self) -> dict:
        """
        Returns all loaded metadata as a dictionary.
        Ensures specific metadata is loaded if not already present.
        """
        # This check is now more robust as load_metadata is always called by concrete __init__
        return self._metadata

    # --- Properties ---
    # These properties now safely access the _metadata dictionary populated by load_metadata
    @property
    def width(self):
        return self._metadata.get('width')

    @property
    def height(self):
        return self._metadata.get('height')

    @property
    def datetime_original(self):
        return self._metadata.get('DateTimeOriginal')

    @property
    def make(self):
        return self._metadata.get('make') # Changed from 'Make' for consistency with FlickrPicture

    @property
    def model(self):
        return self._metadata.get('model')

    # New properties that concrete classes should ensure are populated
    @property
    def file_name(self):
        # Default implementation, concrete classes should override if they have a better name
        return os.path.basename(self.source_identifier)

    @property
    def folder_path(self):
        # Default implementation, concrete classes should override
        return os.path.dirname(self.source_identifier)

    @property
    def file_size(self):
        return self._metadata.get('file_size')

    @property
    def last_modified(self):
        return self._metadata.get('last_modified')