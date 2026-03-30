import os
import sys
from datetime import datetime
import os
from PIL import Image, ExifTags
import rawpy
import django
django.setup()

try:
    from helpers.Picture import Picture
    from helpers.JPEG import JPEG
    from photos.models import Photo
    # from helpers.CR2 import CR2 # If you create one
except ImportError as e:
    print(f"Could not import your custom image models. Please check your Python path and file locations. Error: {e}")
    sys.exit(1)


def is_valid_date(date_string, date_format='%Y-%m-%d'):
    """Helper function to check if a string is a valid date."""
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False

def rename_directories(base_path):
    """
    Renames directories from '{number} {YYYY-mm-dd}' to '{YYYY-mm-dd} {number}'.
    It uses datetime parsing to determine the format of the directory name.
    """
    if not os.path.isdir(base_path):
        print(f"Error: The base path '{base_path}' does not exist or is not a directory.")
        return

    print(f"Scanning directories in '{base_path}'...")
    try:
        directories = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    except FileNotFoundError:
        print(f"Error: The directory '{base_path}' was not found.")
        return

    for dir_name in directories:
        try:
            # Split the name into two parts at the first space
            part1, part2 = dir_name.split(' ', 1)
        except ValueError:
            # If there's no space, it can't match our formats, so we skip it.
            print(f"--> Skipping '{dir_name}': Name does not contain a space.")
            continue

        # YOUR LOGIC: Check if it's already in the new format (YYYY-MM-DD NUMBER)
        if is_valid_date(part1) and part2.isdigit():
            print(f"--> Skipping '{dir_name}': Already in the correct format.")
            continue

        # Check if it's in the old format (NUMBER YYYY-MM-DD)
        if part1.isdigit() and is_valid_date(part2):
            new_name = f"{part2} {part1}"
            old_path = os.path.join(base_path, dir_name)
            new_path = os.path.join(base_path, new_name)

            print(f"    Renaming '{dir_name}' to '{new_name}'...")
            try:
                os.rename(old_path, new_path)
            except OSError as e:
                print(f"    Error renaming '{dir_name}': {e}")
            continue

        # If neither of the above conditions were met, the format is unrecognized.
        print(f"--> Skipping '{dir_name}': Does not match a recognized format.")

# --- Configuration ---
# The name of the folder to save converted images in
OUTPUT_SUBDIR = 'web_versions'
# The maximum width for the output images. Aspect ratio will be maintained.
MAX_WIDTH = 1920
# The quality for the output WebP images (1-100). 85 is a great balance.
WEBP_QUALITY = 85


def process_images_in_directory(base_path):
    """
    Recursively finds and converts images for web usage.
    """
    print(f"Starting image processing in '{base_path}'...")

    # os.walk is perfect for traversing a directory tree
    for dirpath, dirnames, filenames in os.walk(base_path):
        # --- OPTIMIZATION: Don't walk into the output directory ---
        if OUTPUT_SUBDIR in dirnames:
            dirnames.remove(OUTPUT_SUBDIR)

        # Filter for the image files we want to process
        image_files = [f for f in filenames if f.lower().endswith(('.jpg', '.jpeg', '.cr2'))]

        if not image_files:
            continue  # Skip directories with no images

        print(f"\nFound {len(image_files)} images in '{dirpath}'")

        # Create the output subdirectory if it doesn't exist
        output_dir = os.path.join(dirpath, OUTPUT_SUBDIR)
        os.makedirs(output_dir, exist_ok=True)

        for filename in image_files:
            input_path = os.path.join(dirpath, filename)
            # Create the new filename with a .webp extension
            output_filename = f"{os.path.splitext(filename)[0]}.webp"
            output_path = os.path.join(output_dir, output_filename)

            # --- Safety Check: Skip if the file has already been converted ---
            if os.path.exists(output_path):
                print(f"  -> Skipping '{filename}', already converted.")
                continue

            try:
                print(f"  -> Processing '{filename}'...")

                # --- Open the image based on its type ---
                if filename.lower().endswith(('.jpg', '.jpeg')):
                    # Open standard JPEG files with Pillow
                    img = Image.open(input_path)
                else:  # It's a .cr2 file
                    # Use rawpy to decode the RAW file
                    with rawpy.imread(input_path) as raw:
                        # postprocess() returns a numpy array of RGB data
                        rgb_array = raw.postprocess()
                    # Create a Pillow Image from the RGB data
                    img = Image.fromarray(rgb_array)

                # --- Resize while maintaining aspect ratio ---
                width, height = img.size
                if width > MAX_WIDTH:
                    # Calculate the new height to maintain the aspect ratio
                    new_height = int(MAX_WIDTH * (height / width))
                    # Resize using a high-quality downsampling filter
                    print(f"     Resizing from {width}x{height} to {MAX_WIDTH}x{new_height}")
                    img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

                # --- Save in the modern, efficient WebP format ---
                img.save(output_path, 'WEBP', quality=WEBP_QUALITY)

            except Exception as e:
                print(f"  !! ERROR processing '{filename}': {e}")

    print("\nImage processing complete!")

# --- IMPORTANT: Configure Django environment ---
# This is crucial for running stand-alone scripts that interact with Django models.
# Adjust the project name to your actual Django project name.
# Replace 'your_django_project' with the actual name of your Django project.
# For example, if your manage.py is in 'my_project_root/my_project/', then 'my_project' is the project name.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')


# Import your custom image models
# You might need to adjust the Python path or place your Models directory
# so that Python can find 'Models.Picture' and 'Models.JPEG'.
# Example: If 'Models' is at the same level as your Django project root:
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Or, if 'Models' is inside your Django app (e.g., 'your_django_project/photos/Models'):
# Just `from .Models.Picture import Picture` etc.
# For simplicity, assuming Models is directly importable from your script's execution context:



# --- Configuration ---
PARENT_DIR = './my_pictures' # Adjust this to your actual photo collection root
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.cr2') # Add other extensions like .tiff if needed

def get_picture_model_instance(file_path: str) -> Picture | None:
    """
    Instantiates the correct Picture subclass based on file extension.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        return JPEG(file_path)
    # elif ext == '.cr2':
    #     # return CR2(file_path) # Uncomment and implement CR2 model if you have it
    else:
        print(f"Skipping unsupported file type: {file_path}")
        return None

import os
import sys
import glob
from datetime import datetime
import json

# --- IMPORTANT: Configure Django environment ---
# This is crucial for running stand-alone scripts that interact with Django models.
# The value 'mysite.settings' refers to the 'settings.py' file inside your 'mysite' directory.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings') # <--- CONFIRM THIS IS 'mysite.settings'
import django
django.setup()

# Now you can import your Django models
# Django's setup ensures that 'photos' app (at the root) is discoverable.
from photos.models import Photo

# --- Adjust Python path for your custom image models ---
# The script is in 'your_project_root/Utils/'. To reach 'your_project_root/',
# we go up one directory from the script's location.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

try:
    # Now import from the 'helpers' package (e.g., helpers/__init__.py, helpers/Picture.py)
    from helpers.Picture import Picture
    from helpers.JPEG import JPEG
    from helpers.CR2 import CR2
    # Also import ExifTags from PIL as it's used in your JPEG class for metadata parsing
    from PIL import ExifTags
except ImportError as e:
    print(f"ERROR: Could not import custom image models from 'helpers' directory. Please check your Python path and file locations. Error: {e}")
    print(f"Attempted to add '{project_root}' to sys.path.")
    print("Current sys.path:", sys.path) # Helpful for debugging import issues
    sys.exit(1)


# --- Configuration ---
# Set the parent directory where your date folders are located.
# Relative to 'manage_photos.py' (which is in 'Utils/'), 'DL/photos/' is '../DL/photos/'.
PARENT_DIR = os.path.join(project_root, 'DL', 'photos') # More robust absolute path construction

SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.cr2')

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
        # Sort files and directories for consistent order
        files.sort()
        dirs.sort()

        # Try to parse date from directory name for the 'date_folder' field
        folder_name = os.path.basename(root)
        date_from_folder = None
        try:
            date_from_folder = datetime.strptime(folder_name, '%Y-%m-%d').date()
        except ValueError:
            pass # Not a date-named folder, continue

        for file_name in files:
            file_path = os.path.join(root, file_name)
            ext = os.path.splitext(file_name)[1].lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue # Handled by get_picture_model_instance's default skip msg if it returns None

            try:
                # Check if file already exists in the database to prevent duplicates
                if Photo.objects.filter(file_path=file_path).exists():
                    # print(f"  Already in DB, skipping: {file_name}") # Uncomment for more verbosity
                    skipped_count += 1
                    continue

                # Instantiate your custom model (JPEG or CR2)
                picture_instance = get_picture_model_instance(file_path)

                if picture_instance:
                    # Get all metadata via the consistent interface
                    metadata = picture_instance.get_metadata()

                    # Handle GPS data separately from the nested 'gps_data' dict
                    gps_latitude = None
                    gps_longitude = None
                    gps_altitude = None
                    gps_timestamp = None
                    if 'gps_data' in metadata and isinstance(metadata['gps_data'], dict):
                        gps_info = metadata['gps_data']
                        gps_latitude = gps_info.get('latitude')
                        gps_longitude = gps_info.get('longitude')
                        gps_altitude = gps_info.get('altitude')
                        gps_timestamp = gps_info.get('timestamp')
                        # You can pop 'gps_data' from metadata if you don't want it duplicated in all_metadata_json
                        # metadata.pop('gps_data', None)

                    # Create a new Photo object and populate its fields
                    photo = Photo(
                        file_path=file_path,
                        file_name=file_name,
                        folder_path=root,
                        # Common file system metadata (ensure your Picture class or the script populates these)
                        file_size=os.path.getsize(file_path) if os.path.exists(file_path) else None,
                        last_modified=datetime.fromtimestamp(os.path.getmtime(file_path)) if os.path.exists(file_path) else None,
                        created_on_disk=datetime.fromtimestamp(os.path.getctime(file_path)) if os.path.exists(file_path) else None,

                        # Common image properties (standardized names)
                        width=metadata.get('width') or metadata.get('raw_width'),
                        height=metadata.get('height') or metadata.get('raw_height'),
                        image_format=metadata.get('format', ext.upper().replace('.', '')),
                        image_mode=metadata.get('mode'),

                        # Camera/EXIF data (standardized names, handling both JPEG and CR2 variations)
                        make=metadata.get('Make') or metadata.get('make'),
                        model=metadata.get('Model') or metadata.get('model'),
                        datetime_original=metadata.get('DateTimeOriginal'),
                        iso_speed=metadata.get('iso_speed') or metadata.get('ISOSpeedRatings'),
                        artist=metadata.get('Artist') or metadata.get('artist'),

                        # JPEG-specific EXIF fields (if present in metadata)
                        exposure_time=metadata.get('ExposureTime'),
                        f_number=metadata.get('FNumber'),
                        focal_length=metadata.get('FocalLength'),

                        # CR2-specific RAW data fields (if present in metadata)
                        raw_width=metadata.get('raw_width'),
                        raw_height=metadata.get('raw_height'),
                        color_depth=metadata.get('color_depth'),
                        num_colors=metadata.get('num_colors'),
                        cfa_pattern=metadata.get('cfa_pattern'),

                        # GPS Data
                        gps_latitude=gps_latitude,
                        gps_longitude=gps_longitude,
                        gps_altitude=gps_altitude,
                        gps_timestamp=gps_timestamp,

                        # Store all remaining metadata in JSONField for full detail
                        all_metadata_json=metadata,
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