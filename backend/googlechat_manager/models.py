from django.db import models
from django.db.models import JSONField, Min, Max
from protagonist_manager.models import Protagonist
from django.urls import reverse

class ChatParticipant(models.Model):
    original_id = models.CharField(max_length=255, unique=True, help_text="The unique ID from Google export")
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    protagonist = models.ForeignKey(
        Protagonist, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='chat_identities',
        help_text="Link this chat user to a real protagonist in your story."
    )
    def __str__(self):
        return self.name or self.email or self.original_id

class ChatThread(models.Model):
    original_thread_id = models.CharField(max_length=255, unique=True)
    space_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Thread {self.original_thread_id}"

class ChatMessage(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(ChatParticipant, on_delete=models.SET_NULL, null=True, related_name='messages')
    timestamp = models.DateTimeField(db_index=True)
    text_content = models.TextField(blank=True, null=True)
    raw_data = JSONField(blank=True, null=True)
    is_processed_by_ai = models.BooleanField(default=False)
    class Meta:
        ordering = ['timestamp']
    def __str__(self):
        sender_name = self.sender.name if self.sender else "Unknown"
        return f"[{self.timestamp}] {sender_name}: {self.text_content[:50]}..."

class ChatSubject(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Gemini's summary of this subject.")
    keywords = JSONField(default=list, blank=True, help_text="List of keywords associated with this subject")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

class SubjectGroup(models.Model):
    subject = models.ForeignKey(ChatSubject, on_delete=models.CASCADE, related_name='groups')
    messages = models.ManyToManyField(ChatMessage, related_name='subject_groups')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    reasoning = models.TextField(blank=True, help_text="Why Gemini grouped these messages together.")
    class Meta:
        ordering = ['start_date']
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class ChatSequence(models.Model):
    title = models.CharField(max_length=255)
    messages = models.ManyToManyField(ChatMessage, related_name='sequences')
    created_at = models.DateTimeField(auto_now_add=True)
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def update_dates(self):
        """
        Efficiently calculates and saves the start and end dates 
        for the sequence using database aggregation.
        """
        if self.messages.exists():
            aggregates = self.messages.aggregate(
                start=Min('timestamp'),
                end=Max('timestamp')
            )
            self.start_date = aggregates.get('start')
            self.end_date = aggregates.get('end')
            self.save(update_fields=['start_date', 'end_date'])

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('googlechat_manager:sequence_detail', kwargs={'pk': self.pk})

    def get_public_url(self):
        return self.get_absolute_url()
    
    class Meta:
        ordering = ['-created_at']
