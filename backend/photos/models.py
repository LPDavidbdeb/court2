# your_project_root/photos/models.py

from django.db import models
from pgvector.django import VectorField
from django.urls import reverse
from django.utils import timezone
import os

def get_photo_upload_path(instance, filename):
    """
    Dynamically creates a file path for a new photo upload that mimics the old structure.
    It will be stored in GCS under a path like: 'photos/2010-03-09 3/web_versions/file.webp'
    This uses the folder_path stored on the model instance during the migration.
    """

    if instance.folder_path:
        # Recreate the relative path from the old folder_path
        # This assumes folder_path is something like '/path/to/DL/photos/2010-03-09 3/web_versions'
        # We want to extract the part after 'DL/'
        try:
            base_path = instance.folder_path.split('/DL/')[1]
            return os.path.join(base_path, filename)
        except IndexError:
            # Fallback if the path format is unexpected
            return os.path.join('uploads', filename)
    # Fallback for new uploads that don't have a folder_path
    return os.path.join('photos', timezone.now().strftime('%Y/%m/%d'), filename)

class PhotoType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Photo(models.Model):
    # This is now the primary field for the file.
    # The upload_to function gives us control over the GCS path.
    file = models.ImageField(upload_to=get_photo_upload_path, blank=True, null=True)
    
    photo_type = models.ForeignKey(PhotoType, on_delete=models.SET_NULL, null=True, blank=True)
    
    # These fields will be deprecated after the migration but are needed for now.
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    folder_path = models.CharField(max_length=500)
    
    file_size = models.BigIntegerField(null=True, blank=True)
    last_modified = models.DateTimeField(null=True, blank=True)
    created_on_disk = models.DateTimeField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    image_format = models.CharField(max_length=10, null=True, blank=True)
    image_mode = models.CharField(max_length=20, null=True, blank=True)
    make = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    datetime_original = models.DateTimeField(null=True, blank=True, help_text="The naive datetime from the camera's EXIF data.")
    datetime_utc = models.DateTimeField(null=True, blank=True, help_text="The timezone-aware UTC datetime, typically from an XMP sidecar file.")
    iso_speed = models.IntegerField(null=True, blank=True)
    artist = models.CharField(max_length=255, null=True, blank=True)
    exposure_time = models.CharField(max_length=50, null=True, blank=True)
    f_number = models.FloatField(null=True, blank=True)
    focal_length = models.FloatField(null=True, blank=True)
    lens_model = models.CharField(max_length=255, null=True, blank=True)
    raw_width = models.IntegerField(null=True, blank=True)
    raw_height = models.IntegerField(null=True, blank=True)
    color_depth = models.IntegerField(null=True, blank=True)
    num_colors = models.IntegerField(null=True, blank=True)
    cfa_pattern = models.CharField(max_length=50, null=True, blank=True)
    gps_latitude = models.FloatField(null=True, blank=True)
    gps_longitude = models.FloatField(null=True, blank=True)
    gps_altitude = models.FloatField(null=True, blank=True)
    gps_timestamp = models.DateTimeField(null=True, blank=True)
    all_metadata_json = models.JSONField(default=dict, blank=True, null=True)
    date_folder = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['datetime_original']
        verbose_name = "Photo"
        verbose_name_plural = "Photos"

    def __str__(self):
        if self.file:
            return os.path.basename(self.file.name)
        return f"{self.file_name} (Legacy)"

    def get_absolute_url(self):
        return reverse('photos:detail', kwargs={'pk': self.pk})


class PhotoDocument(models.Model):
    """
    Represents a single piece of documentary evidence that is composed of one or more photos.
    e.g., A multi-page letter where each page is a separate photo.
    """
    title = models.CharField(max_length=255, help_text="A descriptive title for the document.")
    author = models.ForeignKey(
        'protagonist_manager.Protagonist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_photo_documents',
        help_text="The author of the document, if applicable."
    )
    description = models.TextField(blank=True, help_text="Optional notes or a summary of the document's content.")
    photos = models.ManyToManyField(
        Photo,
        related_name='photo_documents',
        help_text="The photos that make up this document."
    )
    created_at = models.DateTimeField(default=timezone.now, help_text="The date and time the document was created.")
    updated_at = models.DateTimeField(auto_now=True)
    ai_analysis = models.TextField(
        blank=True, null=True,
        help_text="Description détaillée du contenu visuel générée par l'IA."
    )
    embedding = VectorField(dimensions=768, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Photo Document"
        verbose_name_plural = "Photo Documents"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('photos:document_detail', kwargs={'pk': self.pk})

    def get_public_url(self):
        return self.get_absolute_url()
