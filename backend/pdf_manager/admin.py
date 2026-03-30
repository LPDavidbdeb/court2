from django.contrib import admin
from .models import PDFDocument, PDFDocumentType

@admin.register(PDFDocumentType)
class PDFDocumentTypeAdmin(admin.ModelAdmin):
    """
    Admin view for PDF Document Types.
    """
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PDFDocument)
class PDFDocumentAdmin(admin.ModelAdmin):
    """
    Admin view for PDF Documents.
    """
    list_display = ('title', 'document_type', 'document_date', 'uploaded_at')
    list_filter = ('document_type', 'document_date')
    search_fields = ('title',)
    date_hierarchy = 'document_date'
