# your_project_root/utils/process_existing_photos.py

import os
import sys
import argparse
from django.db import transaction

# --- IMPORTANT: Configure Django environment ---
# Add the project root to the Python path
# This assumes this script is in your_project_root/utils/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Set the DJANGO_SETTINGS_MODULE environment variable
# Replace 'your_project_name.settings' with the actual path to your settings file
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Initialize Django
import django

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    print("Please ensure 'your_project_name.settings' is correct and Django is installed.")
    sys.exit(1)

# Now you can import your Django models and utilities
from photos.models import Photo
from photos_optimze_image import compress_image_for_web


def process_photos_script(max_dimension: int, quality: int):
    """
    Processes Photo objects that do not have a web-optimized image saved yet.
    It reads the original file_path, compresses the image, and saves it to
    the Photo.file ImageField.

    Args:
        max_dimension (int): The maximum dimension (width or height) for the
                             output web-optimized image.
        quality (int): JPEG compression quality (0-100).
    """
    print("Starting process to generate web-optimized images for existing photos...")

    # Find Photo objects where the 'file' ImageField is empty
    # ImageField stores an empty string if no file is assigned.
    photos_to_process = Photo.objects.filter(file__isnull=True)

    total_found = photos_to_process.count()
    processed_count = 0
    skipped_count = 0
    error_count = 0

    if total_found == 0:
        print("No Photo objects found requiring web-optimized image generation.")
        return

    print(f"Found {total_found} Photo objects to process.")

    for photo in photos_to_process:
        original_file_path = photo.file_path

        if not original_file_path:
            print(f"Skipping Photo ID {photo.pk} ({photo.file_name}): Original file_path is empty.")
            skipped_count += 1
            continue

        if not os.path.exists(original_file_path):
            print(
                f"Skipping Photo ID {photo.pk} ({photo.file_name}): Original file not found at '{original_file_path}'.")
            skipped_count += 1
            continue

        print(f"Processing photo: {photo.file_name} (ID: {photo.pk}) from '{original_file_path}'")

        # 1. Compress the image for web using the utility function
        compressed_file_django_object, new_file_name = compress_image_for_web(
            original_file_path,
            output_max_dimension=max_dimension,
            quality=quality
        )

        if compressed_file_django_object:
            try:
                # 2. Save the compressed image to the Photo.file ImageField
                # This will handle saving the file to MEDIA_ROOT/photos/
                # and updating the 'file' field in the database.
                with transaction.atomic():  # Ensure database update is atomic
                    photo.file.save(new_file_name, compressed_file_django_object, save=True)

                processed_count += 1
                print(f"  SUCCESS: Web-optimized image saved for {photo.file_name}.")
            except Exception as e:
                error_count += 1
                print(f"  ERROR: Could not save web-optimized image for {photo.file_name} (ID: {photo.pk}): {e}")
        else:
            error_count += 1
            print(f"  ERROR: Compression failed for {photo.file_name} (ID: {photo.pk}). Web image not saved.")

    print("\n--- Processing Summary ---")
    print(f"Total photos found for processing: {total_found}")
    print(f"Successfully processed: {processed_count}")
    print(f"Skipped (missing path/file or already processed): {skipped_count}")
    print(f"Errors during processing/saving: {error_count}")
    print("Script finished.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate web-optimized images for existing Django Photo records.")
    parser.add_argument('--max-dimension', type=int, default=1920,
                        help='Maximum dimension (width or height) for web-optimized images. Default: 1920.')
    parser.add_argument('--quality', type=int, default=85,
                        help='JPEG compression quality (0-100) for web-optimized images. Default: 85.')

    args = parser.parse_args()

    # Call the main processing function
    process_photos_script(args.max_dimension, args.quality)