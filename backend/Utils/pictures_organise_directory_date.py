import os
import shutil
from PIL import Image
import rawpy

SRC_DIR = 'DL/photos/raw'

def get_date_taken(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        try:
            img = Image.open(file_path)
            exif = img._getexif()
            if exif and 36867 in exif:
                return exif[36867].split(' ')[0].replace(':', '-')
        except Exception:
            pass
    elif ext == '.cr2':
        try:
            with rawpy.imread(file_path) as raw:
                date = raw.metadata.timestamp
                if date:
                    return date.strftime('%Y-%m-%d')
        except Exception:
            pass
    return None

def organize_photos(src_dir):
    for filename in os.listdir(src_dir):
        if filename.lower().endswith(('.cr2', '.jpg', '.jpeg')):
            file_path = os.path.join(src_dir, filename)
            date_taken = get_date_taken(file_path)
            if date_taken:
                target_dir = os.path.join(src_dir, date_taken)
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(file_path, os.path.join(target_dir, filename))
                print(f"Moved {filename} to {target_dir}")
            else:
                print(f"Date not found for {filename}")

organize_photos(SRC_DIR)