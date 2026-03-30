# flickr_dao.py

import flickrapi
from datetime import datetime
import pickle
import os
from dateutil.parser import parse
import math # Import math for ceil


class FlickrDAO:
    def __init__(self, account_name, config, cache_dir="DL/photos/Flickrs"):
        self.account_name = account_name
        self.api_key = config[self.account_name]['api_key']
        self.api_secret = config[self.account_name]['api_secret']
        self.user_id = config[self.account_name]['user_id']
        self.token_cache_file = config[self.account_name]['token_cache_file']
        # Ensure cache_dir exists
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        self.flickr = flickrapi.FlickrAPI(
            self.api_key,
            self.api_secret,
            format='parsed-json',
            token_cache_location=self.token_cache_file
        )
        self._authenticate()

    def _authenticate(self):
        if not self.flickr.token_valid():
            # Request token and authorize URL
            self.flickr.get_request_token(oauth_callback='oob')
            authorize_url = self.flickr.auth_url(perms='read')
            print(f"Visit this URL to authorize '{self.account_name}':\n{authorize_url}")
            verifier = input("Verifier code: ").strip()
            # Get access token and save it to token_cache_file
            self.flickr.get_access_token(verifier)
            print(f"Authentication successful for '{self.account_name}'. Token saved to {self.token_cache_file}")

    def list_albums(self):
        """
        Lists all albums (photosets) for the authenticated user.
        """
        response = self.flickr.photosets.getList(user_id=self.user_id)
        if response and 'photosets' in response and 'photoset' in response['photosets']:
            return response['photosets']['photoset']
        return [] # Return an empty list if no photosets found

    def get_album_photos(self, album_title: str) -> list[dict]:
        """
        Retrieves all photos from a specified album, handling pagination.
        For each photo, it also fetches its sizes and detailed info.
        """
        albums = self.list_albums()
        album_id = next((a['id'] for a in albums if a['title']['_content'] == album_title), None)
        if not album_id:
            raise ValueError(f"Album '{album_title}' not found for user_id '{self.user_id}'")

        all_photos_data = []
        page = 1
        per_page = 500  # Flickr's typical maximum per_page value

        while True:
            print(f"Fetching page {page} for album '{album_title}' (ID: {album_id})...")
            response = self.flickr.photosets.getPhotos(
                user_id=self.user_id,
                photoset_id=album_id,
                per_page=per_page,
                page=page
            )

            photoset = response.get('photoset')
            if not photoset:
                print(f"No photoset data found in response for page {page}.")
                break # Exit if no photoset data

            current_page_photos = photoset.get('photo', [])
            total_photos_in_album = int(photoset.get('total', 0)) # Total photos in the album
            total_pages = int(photoset.get('pages', 1)) # Total pages available

            if not current_page_photos:
                print(f"No photos returned on page {page}. Exiting pagination loop.")
                break # No more photos to retrieve

            for photo in current_page_photos:
                photo_id = photo['id']
                secret = photo['secret']

                try:
                    sizes = self.flickr.photos.getSizes(photo_id=photo_id)
                    info = self.flickr.photos.getInfo(photo_id=photo_id, secret=secret)
                    all_photos_data.append({
                        'photo_id': photo_id,
                        'sizes': sizes.get('sizes', {}), # Access 'sizes' key, default to empty dict
                        'info': info.get('photo', {})    # Access 'photo' key, default to empty dict
                    })
                except flickrapi.FlickrError as e:
                    print(f"Error fetching data for photo {photo_id}: {e}")
                    # You might want to log this error or decide to skip this photo
                    continue # Continue to the next photo

            print(f"Retrieved {len(current_page_photos)} photos from page {page}. Total retrieved so far: {len(all_photos_data)}")

            # Check if there are more pages to fetch
            if page >= total_pages or len(all_photos_data) >= total_photos_in_album:
                print(f"Reached end of album photos. Total photos expected: {total_photos_in_album}, retrieved: {len(all_photos_data)}")
                break # All pages retrieved or all photos retrieved

            page += 1

        return all_photos_data

    def save_data(self, data: dict):
        """Save data dictionary as a pickle file named by account and current date."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{self.account_name}_{date_str}.pkl"
        file_path = os.path.join(self.cache_dir, filename)
        try:
            with open(file_path, "wb") as f:
                pickle.dump(data, f)
            print(f"Saved API data to cache file: {file_path}")
            return file_path
        except Exception as e:
            print(f"Error saving data to cache file {file_path}: {e}")
            return None