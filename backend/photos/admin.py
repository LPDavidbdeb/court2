from django.contrib import admin
from .models import Photo, PhotoType

@admin.register(PhotoType)
class PhotoTypeAdmin(admin.ModelAdmin):
    """
    Admin view for Photo Types.
    """
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """
    Admin view for Photos.
    """
    list_display = ('file_name', 'photo_type', 'datetime_original', 'make', 'model')
    list_filter = ('photo_type', 'make', 'model', 'date_folder')
    search_fields = ('file_name', 'file_path')
    date_hierarchy = 'datetime_original'
