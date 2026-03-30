import os
import pickle
from datetime import datetime


class FlickrCachDAO:
    def __init__(self, account_name):
        self.account_name = account_name
        self.cache_base_dir = os.path.join("DL", "photos", "Flickrs", self.account_name)
        os.makedirs(self.cache_base_dir, exist_ok=True)

    def get_cache_filepath(self, album_title: str) -> str:
        """Returns a full path to the cache file, e.g., DL/photos/Flickrs/cchic/albumname_20250711.pkl"""
        safe_title = album_title.replace(" ", "_").lower()
        #date_str = datetime.now().strftime("%Y%m%d")
        #filename = f"{safe_title}_{date_str}.pkl"
        filename = f"{safe_title}.pkl"
        return os.path.join(self.cache_base_dir, filename)

    def save_photos_to_cache(self, data, album_title: str):
        path = self.get_cache_filepath(album_title)
        with open(path, "wb") as f:
            pickle.dump(data, f)
        print(f"✅ Saved data to: {path}")

    def load_photos_from_cache(self, album_title: str):
        path = self.get_cache_filepath(album_title)
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
            print(f"📦 Loaded cached data from: {path}")
            return data
        print(f"⚠️ No cached data at: {path}")
        return None

