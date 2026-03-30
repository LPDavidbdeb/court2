from django import forms
from .models import Event
from photos.models import Photo, PhotoType

class EventForm(forms.ModelForm):
    """
    A form for creating and editing Events, with a visual photo selector.
    """
    # Use a CheckboxSelectMultiple widget for a more user-friendly interface
    linked_photos = forms.ModelMultipleChoiceField(
        queryset=Photo.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Event
        fields = [
            'parent',
            'allegation',
            'date',
            'explanation',
            'linked_photos',
            'linked_email',
            'email_quote',
        ]

# This is the form for the server-side batch processing page.
class PhotoProcessingForm(forms.Form):
    PROCESSING_CHOICES = [
        ('add_by_path', 'Add New Photos (by File Path, Non-Destructive)'),
        ('add_by_timestamp', 'Add New Photos (Check for Timestamp Duplicates)'),
        ('clean', 'Clean Install (Deletes All Existing Photos)'),
    ]

    processing_mode = forms.ChoiceField(
        choices=PROCESSING_CHOICES,
        initial='add_by_path',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Processing Mode"
    )
    source_directory = forms.CharField(
        label="Source Directory Path",
        max_length=500,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/path/to/your/photos'}),
        help_text="Enter the full, absolute path to the directory on the server containing the photos to process."
    )
    photo_type = forms.ModelChoiceField(
        queryset=PhotoType.objects.all(),
        required=False,
        label="Assign Photo Type (Optional)",
        help_text="Select a type to assign to all imported photos."
    )
