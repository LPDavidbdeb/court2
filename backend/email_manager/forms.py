from django import forms
from .models import Quote
from trame_narrative.models import TrameNarrative

class EmlUploadForm(forms.Form):
    eml_file = forms.FileField(label="Select an EML file")
    protagonist = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        label="Link to Protagonist (Optional)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set queryset for Protagonist to avoid circular imports
        from protagonist_manager.models import Protagonist
        self.fields['protagonist'].queryset = Protagonist.objects.all()

class QuoteForm(forms.ModelForm):
    trames_narratives = forms.ModelMultipleChoiceField(
        queryset=TrameNarrative.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Associated Narrative Frames"
    )

    class Meta:
        model = Quote
        fields = ['quote_text', 'trames_narratives']
        widgets = {
            'quote_text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter quote text'}),
        }
