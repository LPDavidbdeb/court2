from django.db import models
from pgvector.django import VectorField
from django.urls import reverse
from email_manager.models import Email
from photos.models import Photo

class Event(models.Model):
    embedding = VectorField(dimensions=768, null=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="The parent event for this piece of evidence."
    )
    date = models.DateField(help_text="The date of the event.")
    explanation = models.TextField(
        blank=True,
        help_text="A detailed explanation of the event, auto-filled for photo clusters."
    )
    email_quote = models.TextField(
        blank=True,
        null=True,
        help_text="A specific quote or excerpt from an email."
    )
    linked_email = models.ForeignKey(
        Email, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        help_text="The specific email this quote is from."
    )
    linked_photos = models.ManyToManyField(
        Photo,
        blank=True,
        related_name='events',
        help_text="A collection of photos related to this event.",
        through='SupportingEvidenceLinkedPhotos',
    )

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        db_table = 'SupportingEvidence_supportingevidence' 
        ordering = ['date']

    def get_absolute_url(self):
        """Returns the canonical URL for an event."""
        return reverse('events:detail', kwargs={'pk': self.pk})

    def get_public_url(self):
        return self.get_absolute_url()

    def get_display_id(self):
        return f"E-{self.pk}"

    def __str__(self):
        date_str = self.date.strftime('%Y-%m-%d') if self.date else "[No Date]"
        display_id_str = self.get_display_id() if self.pk else "New Event"
        description = self.explanation[:50] + '...' if self.explanation else "No explanation"

        linked_summary = []
        if self.pk:
            if self.linked_photos.exists():
                linked_summary.append(f"{self.linked_photos.count()} photo(s)")
            if self.linked_email:
                 linked_summary.append("1 email")

        linked_str = f" ({', '.join(linked_summary)})" if linked_summary else ""

        return f"{display_id_str} - {description} ({date_str}){linked_str}"

class SupportingEvidenceLinkedPhotos(models.Model):
    supportingevidence = models.ForeignKey(Event, models.DO_NOTHING, db_column='supportingevidence_id')
    photo = models.ForeignKey(Photo, models.DO_NOTHING)

    class Meta:
        db_table = 'SupportingEvidence_supportingevidence_linked_photos'
        # The 'managed = False' line has been removed. Django will now manage this table.
        unique_together = (('supportingevidence', 'photo'),)
