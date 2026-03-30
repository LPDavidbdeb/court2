from django.db import models
from pgvector.django import VectorField
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from protagonist_manager.models import Protagonist
from django.utils import timezone
from django.urls import reverse


# NEW: Add choices for the document source
class DocumentSource(models.TextChoices):
    REPRODUCED = 'REPRODUCED', 'Reproduced (from external file)'
    PRODUCED = 'PRODUCED', 'Produced (created manually)'

class Document(models.Model):
    """
    Represents a single, complete document with its own metadata.
    This table acts as the "library" of all documents.
    """
    title = models.CharField(max_length=555, help_text="The official title of the document.")
    author = models.ForeignKey(
        Protagonist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_documents"
    )
    document_original_date = models.DateField(default=timezone.now, null=True, blank=True)
    solemn_declaration = models.TextField(blank=True, help_text="The solemn declaration text for this document.")
    
    # NEW: Add this field
    source_type = models.CharField(
        max_length=20,
        choices=DocumentSource.choices,
        default=DocumentSource.REPRODUCED, # Default to the existing behavior
        help_text="Indicates if the document was imported or created manually."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    embedding = VectorField(dimensions=768, null=True, blank=True)
    file_source = models.FileField(
        upload_to='evidence_files/',  # Changed to 'evidence_files/' for clarity
        null=True,
        blank=True,
        help_text="The original source file (PDF) if this is a REPRODUCED document."
    )

    def get_absolute_url(self):
        return reverse('document_manager:document_detail', kwargs={'pk': self.pk})

    def get_public_url(self):
        return reverse('core:document_public', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"

class Statement(models.Model):
    embedding = VectorField(dimensions=768, null=True, blank=True)
    """
    Represents a single, reusable block of content (an assertion, fact, or paragraph).
    """
    text = models.TextField(blank=True, null=True)
    is_true = models.BooleanField(default=True)
    is_falsifiable = models.BooleanField(null=True, blank=True, default=None)
    is_user_created = models.BooleanField(default=False, help_text="True if this statement was created by a user through the editor, False if imported.") # NEW FIELD
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (self.text or "")[:80]

    class Meta:
        verbose_name = "Statement"
        verbose_name_plural = "Statements"

class LibraryNode(MPTTModel):
    """
    New tree structure model. Each tree within this model corresponds to a single Document.
    This model connects the Document (metadata) and Statement (content) in a hierarchy.
    """
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="nodes",
        help_text="The document this node belongs to."
    )
    item = models.CharField(
        max_length=555,
        help_text="Short name or title for this node in the tree."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- ADDED: Generic Relation Fields (nullable for transition) ---
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, # Allow null for existing rows
        help_text="The model class that this node points to (e.g., Statement or TrameNarrative)."
    )
    object_id = models.PositiveIntegerField(
        null=True, # Allow null for existing rows
        help_text="The primary key of the object this node points to."
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    class MPTTMeta:
        order_insertion_by = ['item']

    class Meta:
        verbose_name = "Library Node"
        verbose_name_plural = "Library Nodes"

    def __str__(self):
        return f"Node in '{self.document.title}'"
