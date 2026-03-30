# your_project_root/utils/image_processing.py

import os
from PIL import Image
import rawpy
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

def compress_image_for_web(input_path, output_max_dimension=1920, quality=85):
    """
    Compresses an image (JPG or CR2) for web publishing, maintaining aspect ratio.

    Args:
        input_path (str): Absolute path to the original image file (JPG or CR2).
        output_max_dimension (int): The maximum dimension (width or height) for the
                                    output image. The other dimension will be scaled
                                    proportionally. Default is 1920px.
        quality (int): JPEG compression quality (0-100). Default is 85.

    Returns:
        tuple: (InMemoryUploadedFile, filename) if successful, None otherwise.
               The InMemoryUploadedFile can be directly assigned to a Django ImageField.
    """
    file_name = os.path.basename(input_path)
    base_name, ext = os.path.splitext(file_name)
    ext = ext.lower()

    img = None
    try:
        if ext in ['.jpg', '.jpeg']:
            img = Image.open(input_path)
        elif ext == '.cr2':
            with rawpy.imread(input_path) as raw:
                # Demosaic and get a PIL Image from the raw data
                img = Image.fromarray(raw.postprocess(use_camera_wb=True, no_auto_bright=True))
        else:
            print(f"Unsupported file type: {ext}")
            return None, None

        # Convert to RGB if not already (important for saving as JPEG)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Calculate new dimensions while maintaining aspect ratio
        width, height = img.size
        if width > output_max_dimension or height > output_max_dimension:
            if width > height:
                new_width = output_max_dimension
                new_height = int(height * (new_width / width))
            else:
                new_height = output_max_dimension
                new_width = int(width * (new_height / height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save to a BytesIO object (in-memory file)
        output_io = BytesIO()
        img.save(output_io, format='JPEG', quality=quality, optimize=True)
        output_io.seek(0)

        # Create a Django InMemoryUploadedFile
        # The filename for the compressed image will be base_name + '_web.jpg'
        new_file_name = f"{base_name}_web.jpg" # This filename will be used by Django's ImageField
        django_file = InMemoryUploadedFile(
            output_io,
            'ImageField',
            new_file_name,
            'image/jpeg',
            output_io.getbuffer().nbytes,
            None
        )
        return django_file, new_file_name

    except FileNotFoundError:
        print(f"Error: File not found at {input_path}")
        return None, None
    except Exception as e:
        print(f"An error occurred while processing {input_path}: {e}")
        return None, None