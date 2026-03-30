from django.db import models
from pgvector.django import VectorField
from django.urls import reverse
from protagonist_manager.models import Protagonist
import locale
import os

class EmailThread(models.Model):
    """
    Represents a single conversation thread, grouping multiple emails.
    """
    thread_id = models.CharField(max_length=255, unique=True, db_index=True,
                                 help_text="The unique ID for the email thread (e.g., from Gmail).")
    protagonist = models.ForeignKey(Protagonist, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='email_threads',
                                    help_text="The protagonist associated with this email thread.")
    subject = models.CharField(max_length=500, blank=True, null=True,
                               help_text="The subject of the conversation, typically from the first email.")
    saved_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Thread for '{self.subject}'"

    class Meta:
        verbose_name = "Email Thread"
        verbose_name_plural = "Email Threads"
        ordering = ['-updated_at']

class Email(models.Model):
    """
    Represents a single email message within a thread.
    """
    thread = models.ForeignKey(EmailThread, on_delete=models.CASCADE, related_name='emails')
    message_id = models.CharField(max_length=255, unique=True, db_index=True)
    dao_source = models.CharField(max_length=50,
                                  help_text="The source used to acquire this email (e.g., Gmail).")
    subject = models.CharField(max_length=500, blank=True, null=True)
    sender = models.CharField(max_length=255, blank=True, null=True)
    recipients_to = models.TextField(blank=True, null=True, help_text="Comma-separated 'To' recipients")
    recipients_cc = models.TextField(blank=True, null=True, help_text="Comma-separated 'Cc' recipients")
    recipients_bcc = models.TextField(blank=True, null=True, help_text="Comma-separated 'Bcc' recipients")
    date_sent = models.DateTimeField(blank=True, null=True)
    body_plain_text = models.TextField(blank=True, null=True)
    embedding = VectorField(dimensions=768, null=True, blank=True)
    eml_file_path = models.CharField(max_length=1024)
    saved_at = models.DateTimeField(auto_now_add=True)
    eml_file = models.FileField(upload_to='emails/', blank=True, null=True)

    sender_protagonist = models.ForeignKey(
        Protagonist, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sent_emails',
        help_text="The protagonist who sent this email."
    )
    recipient_protagonists = models.ManyToManyField(
        Protagonist, 
        related_name='received_emails',
        blank=True,
        help_text="The protagonists who received this email."
    )

    def get_absolute_url(self):
        return reverse('email_manager:email_detail', kwargs={'pk': self.pk})

    def get_public_url(self):
        return reverse('core:email_public', kwargs={'pk': self.pk})

    @property
    def eml_filename(self):
        """Returns the base name of the EML file path."""
        if self.eml_file_path:
            return os.path.basename(self.eml_file_path)
        return None

    def __str__(self):
        return f"Email: '{self.subject}' from {self.sender}"

    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ['date_sent']

class Quote(models.Model):
    embedding = VectorField(dimensions=768, null=True, blank=True)
    """
    A specific quote extracted from an email.
    """
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='quotes')
    quote_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('email_manager:quote_detail', kwargs={'pk': self.pk})

    @property
    def full_sentence(self):
        """
        Dynamically generates a full descriptive sentence for the quote,
        pulling metadata from the parent Email object.
        """
        if not self.email:
            return self.quote_text

        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        except locale.Error:
            locale.setlocale(locale.LC_TIME, '')  # Fallback to system default

        date_str = self.email.date_sent.strftime("%d %B %Y à %Hh%M") if self.email.date_sent else "date inconnue"
        
        if self.email.sender_protagonist:
            sender_name = self.email.sender_protagonist.get_full_name()
        else:
            sender_name = self.email.sender

        email_subject = self.email.subject or "(Sans objet)"

        return (
            f'Dans le courriel intitulé "{email_subject}", '
            f'{sender_name} a écrit, le {date_str} : '
            f'"{self.quote_text}"'
        )
    def __str__(self):
        if self.email and self.email.date_sent:
            return f'Quote from {self.email.subject} on {self.email.date_sent.strftime("%Y-%m-%d")}'
        return f'Quote from {self.email.subject} (date unknown)'

    class Meta:
        verbose_name = "Quote"
        verbose_name_plural = "Quotes"
        ordering = ['-created_at']
