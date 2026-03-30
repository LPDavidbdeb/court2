from django import forms
from tinymce.widgets import TinyMCE
from .models import TrameNarrative, PerjuryArgument
from document_manager.models import Statement
from django.contrib.contenttypes.models import ContentType

class TrameNarrativeForm(forms.ModelForm):
    """
    This form remains unchanged and manages the 'Evidence Collector'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resume'].widget = TinyMCE(attrs={'cols': 80, 'rows': 30})
        # Filter targeted_statements to only show False and Falsifiable statements
        self.fields['targeted_statements'].queryset = Statement.objects.filter(is_true=False, is_falsifiable=True)

    class Meta:
        model = TrameNarrative
        fields = [
            'titre',
            'resume',
            'type_argument',
            'targeted_statements',
        ]
        widgets = {
            'targeted_statements': forms.CheckboxSelectMultiple,
            'type_argument': forms.Select(choices=TrameNarrative.TypeArgument.choices),
        }

class PerjuryArgumentForm(forms.ModelForm):
    """
    This is the new, correct form for the 'Sidecar' model.
    It only handles the 4 structured text fields.
    """
    class Meta:
        model = PerjuryArgument
        fields = ['text_declaration', 'text_proof', 'text_mens_rea', 'text_legal_consequence']
        
        # Define common MCE attributes to ensure the custom plugin is available
        mce_attrs = {
            'plugins': 'advlist autolink lists link image charmap print preview anchor table custom_inserter',
            'toolbar': 'undo redo | bold italic underline | bullist numlist | custom_inserter | table',
        }

        widgets = {
            'text_declaration': TinyMCE(attrs={'cols': 80, 'rows': 15}, mce_attrs=mce_attrs),
            'text_proof': TinyMCE(attrs={'cols': 80, 'rows': 15}, mce_attrs=mce_attrs),
            'text_mens_rea': TinyMCE(attrs={'cols': 80, 'rows': 15}, mce_attrs=mce_attrs),
            'text_legal_consequence': TinyMCE(attrs={'cols': 80, 'rows': 15}, mce_attrs=mce_attrs),
        }
