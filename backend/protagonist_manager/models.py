from django.db import models


class Protagonist(models.Model):
    """
    Django model to store information about story protagonists.
    """
    first_name = models.CharField(max_length=100, help_text="The protagonist's first name.")
    last_name = models.CharField(max_length=100, blank=True, null=True,
                                 help_text="The protagonist's last name (optional).")
    role = models.CharField(max_length=200,
                            help_text="The role of the protagonist in the story (e.g., 'Hero', 'Villain', 'Sidekick').")
    linkedin_url = models.URLField(blank=True, null=True, help_text="Link to the protagonist's LinkedIn profile.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']  # Order by last name, then first name
        verbose_name = "Protagonist"
        verbose_name_plural = "Protagonists"

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name or ''}".strip()
        return f"{full_name} ({self.role})" if full_name else f"Protagonist ({self.role})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name or ''}".strip()

    def get_full_name_with_role(self):
        """Returns the full name followed by the role in brackets."""
        full_name = self.get_full_name()
        return f"{full_name} [{self.role}]"

    def get_absolute_url(self):
        """
        Returns the URL to access a particular instance of Protagonist.
        """
        from django.urls import reverse
        return reverse('protagonist_manager:protagonist_detail', args=[str(self.id)])


class ProtagonistEmail(models.Model):
    """
    Model to store email addresses for a Protagonist.
    A Protagonist can have multiple email addresses.
    """
    protagonist = models.ForeignKey(Protagonist, on_delete=models.CASCADE, related_name='emails')
    email_address = models.EmailField(max_length=255, unique=True, help_text="An email address for the protagonist.")
    description = models.CharField(max_length=255, blank=True, null=True, help_text="e.g., 'Work', 'Personal', 'Old'")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['email_address']
        verbose_name = "Protagonist Email"
        verbose_name_plural = "Protagonist Emails"

    def __str__(self):
        return f"{self.email_address} ({self.protagonist.get_full_name()})"
