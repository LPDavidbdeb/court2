from django.db import models
from pgvector.django import VectorField
from django.core.validators import FileExtensionValidator
from django.urls import reverse

class PDFDocumentType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the document type (e.g., 'Mémoire de Marie-Josée')."
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "PDF Document Type"
        verbose_name_plural = "PDF Document Types"
        ordering = ['name']

class PDFDocument(models.Model):
    title = models.CharField(
        max_length=255,
        help_text="The title of the PDF document."
    )
    author = models.ForeignKey(
        'protagonist_manager.Protagonist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_pdfs',
        help_text="The author of the document, if applicable."
    )
    file = models.FileField(
        upload_to='pdf_documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="The uploaded PDF file."
    )
    document_date = models.DateField(
        null=True,
        blank=True,
        help_text="The date of the document, if applicable."
    )
    document_type = models.ForeignKey(
        PDFDocumentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The type or category of this PDF document."
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time the document was uploaded."
    )
    ai_analysis = models.TextField(
        blank=True, null=True,
        help_text="Analyse forensique et résumé généré par l'IA pour économiser les tokens multimodaux."
    )
    embedding = VectorField(dimensions=768, null=True, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('pdf_manager:pdf_detail', kwargs={'pk': self.pk})

    def get_public_url(self):
        return reverse('core:pdf_document_public', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "PDF Document"
        verbose_name_plural = "PDF Documents"
        ordering = ['-document_date']

class Quote(models.Model):
    embedding = VectorField(dimensions=768, null=True, blank=True)
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='quotes')
    quote_text = models.TextField()
    page_number = models.PositiveIntegerField(
        help_text="The page number where the quote can be found."
    )
    quote_location_details = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional details to locate the quote, e.g., 'Paragraph 3' or 'Header'."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('pdf_manager:quote_detail', kwargs={'pk': self.pk})

    @property
    def full_sentence(self):
        """
        Dynamically generates a full descriptive sentence for the quote,
        pulling metadata from the parent PDFDocument object.
        """
        if not self.pdf_document:
            return self.quote_text

        doc_title = self.pdf_document.title or "(Untitled Document)"
        return f'In the document "{doc_title}", on page {self.page_number}, it says: "{self.quote_text}"'

    def __str__(self):
        return f'Quote from "{self.pdf_document.title}" on page {self.page_number}'

    class Meta:
        verbose_name = "PDF Quote"
        verbose_name_plural = "PDF Quotes"
        ordering = ['-created_at']
