# your_project_root/Models/FlickrPicture.py

import requests # For checking remote file validity (e.g., HEAD request)
from datetime import datetime
from dateutil.parser import parse
from helpers.Picture import Picture # Assuming direct import path

class FlickrPicture(Picture):
    """
    Represents a photo from Flickr. Extracts and standardizes metadata from the Flickr API.
    """

    def __init__(self, photo_info: dict, size_info: dict, exif_info: dict = None):
        """
        Initializes a FlickrPicture object.

        Args:
            photo_info (dict): The 'info' dictionary from Flickr's photos.getInfo API response.
            size_info (list): The list of size dictionaries from Flickr's photos.getSizes API response.
            exif_info (list, optional): The list of EXIF dictionaries from Flickr's photos.getExif API response.
                                        Defaults to None.
        """
        # Use a unique identifier from photo_info as the source_identifier
        # We'll use the photopage URL as it's a stable identifier and good for validity checks
        photo_page_url = photo_info.get("urls", {}).get("url", [{}])[0].get("_content", f"flickr://{photo_info.get('id')}")
        super().__init__(source_identifier=photo_page_url)

        self.photo_info = photo_info
        self.size_info = size_info # This is directly the list of sizes
        self.exif_info = exif_info or [] # Ensure it's an empty list if None

        # Load all metadata
        self.load_common_metadata() # This now handles Flickr-specific common metadata
        self.load_metadata() # This handles width/height/sizes

    def _check_source_validity(self) -> bool:
        """
        Checks the validity of the Flickr photo's source (e.g., if the image URL is accessible).
        For Flickr, we can attempt a HEAD request on the original image URL.
        """
        original_size = next((s for s in self.size_info if s.get('label') == 'Original'), None)
        if original_size and original_size.get('source'):
            image_url = original_size['source']
            try:
                # Use a HEAD request to avoid downloading the entire image
                response = requests.head(image_url, timeout=5)
                # Success status codes are typically 2xx (e.g., 200 OK)
                # A 404 means not found, a 500 means server error.
                # We're looking for success or a specific error that means "not valid"
                return response.status_code == 200 # More robust than checking for 500 specifically
            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not check Flickr image source validity for {self.source_identifier}: {e}")
                return False # Network error or timeout means invalid for now
        print(f"Warning: No original size URL found for Flickr photo {self.source_identifier}. Cannot check validity.")
        return False # No URL to check

    def load_common_metadata(self):
        """Loads common metadata specific to Flickr photos."""
        p = self.photo_info
        self._metadata.update({
            "flickr_id": p.get("id"),
            "title": p.get("title", {}).get("_content", ""),
            "description": p.get("description", {}).get("_content", "").strip(),
            "owner_username": p.get("owner", {}).get("username"),
            "owner_realname": p.get("owner", {}).get("realname", ""),
            "visibility": p.get("visibility"),
            "views": int(p.get("views", 0)),
            "photo_url": p.get("urls", {}).get("url", [{}])[0].get("_content", ""),
            "license": p.get("license"),
        })

        # Parse EXIF info
        exif_dict = {
            item.get("label"): item.get("raw", {}).get("_content")
            for item in self.exif_info
            if "raw" in item and item.get("label")
        }

        def parse_float(key):
            try:
                val = exif_dict.get(key)
                if val is None: return None
                return float(val.split()[0])
            except (KeyError, ValueError, IndexError, AttributeError):
                return None

        self._metadata.update({
            "make": exif_dict.get("Make"),
            "model": exif_dict.get("Model"),
            "iso_speed": int(exif_dict.get("ISO Speed", 0)) if "ISO Speed" in exif_dict else None,
            "artist": exif_dict.get("Artist") or p.get("owner", {}).get("realname"),
            "exposure_time": exif_dict.get("Exposure Time"),
            "f_number": parse_float("F Number"),
            "focal_length": parse_float("Focal Length"),
            "lens_model": exif_dict.get("Lens Model"),
        })

        # Dates
        taken = p.get("dates", {}).get("taken")
        try:
            self._metadata["DateTimeOriginal"] = parse(taken) if taken else None
        except Exception:
            self._metadata["DateTimeOriginal"] = None

        # Simulate file system metadata if possible (e.g., from dateuploaded)
        # Note: Actual file_size and last_modified from disk are not applicable
        uploaded_ts = p.get("dateuploaded")
        if uploaded_ts:
            self._metadata['created_on_flickr'] = datetime.fromtimestamp(int(uploaded_ts))
            # You could map 'file_size' to the largest available size for reporting
            # For simplicity, we won't add 'file_size' from Flickr here unless directly provided.

    def load_metadata(self):
        """Loads size-related metadata (abstract method implementation)."""
        all_sizes = self.size_info # This is directly the list of sizes from DAO
        sizes = {}

        for size in all_sizes:
            label = size.get("label")
            sizes[label] = {
                "width": int(size.get("width", 0)),
                "height": int(size.get("height", 0)),
                "source": size.get("source"),
                "url": size.get("url"),
                "media": size.get("media")
            }

        self._metadata["sizes"] = sizes

        # Set width/height from a preferred size (e.g., 'Medium' or 'Original')
        preferred = sizes.get("Medium") or sizes.get("Original") or next(iter(sizes.values()), None)
        if preferred:
            self._metadata["width"] = preferred["width"]
            self._metadata["height"] = preferred["height"]

    # --- Properties (overriding base properties where Flickr has specific info) ---
    @property
    def file_name(self):
        # Use Flickr title, fallback to Flickr ID
        return self._metadata.get("title") or f"{self._metadata.get('flickr_id')}.jpg"

    @property
    def folder_path(self):
        # Define based on Flickr account/user
        return f"flickr://{self._metadata.get('owner_username')}/"

    @property
    def file_size(self):
        # If you want to represent file size, you'd pick a specific size source
        # For example, the 'Original' size's actual byte size (if available or calculable)
        # For now, it's safer to leave it as None or get it from a specific size object if needed.
        # This is not directly available from Flickr API output in the same way as local files.
        # You'd need to fetch content-length via HEAD request to get actual size.
        return None # Or implement logic to get size from 'Original' if available

    @property
    def last_modified(self):
        # Flickr's concept of 'last modified' might be 'dateuploaded' or 'dates.taken'
        # Let's map it to 'dateuploaded' for a 'file modification' equivalent
        return self._metadata.get('created_on_flickr') # From load_common_metadata


    @property
    def image_format(self):
        # Can try guessing from file extension in photo_url or return 'jpg'
        url = self._metadata.get("photo_url", "")
        return url.split('.')[-1].lower() if '.' in url else 'jpg'

    @property
    def artist(self):
        return self._metadata.get("artist") or self._metadata.get("owner_username")

    # --- Convenience method ---
    def to_dict(self):
        """Returns a copy of the metadata dictionary."""
        return self._metadata.copy()