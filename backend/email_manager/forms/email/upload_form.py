from django import forms

from protagonist_manager.models import Protagonist


class EmlUploadForm(forms.Form):
    """
    Form for uploading an .eml file.
    """
    eml_file = forms.FileField(
        label="Select .eml File",
        help_text="Upload an email file in .eml format.",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    # Optional: Allow linking to a protagonist during upload
    protagonist = forms.ModelChoiceField(
        queryset=Protagonist.objects.all().order_by('first_name', 'last_name'),
        required=False,
        label="Link to Protagonist (Optional)",
        help_text="Select an existing protagonist to link this email to.",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

