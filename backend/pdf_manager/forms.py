from django import forms
from .models import PDFDocument, Quote
from protagonist_manager.models import Protagonist

class PDFDocumentForm(forms.ModelForm):
    """
    A form for uploading and editing a PDF document.
    """
    author_search = forms.CharField(
        label='Author',
        required=False,
        help_text="Search for an existing protagonist or add a new one.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Start typing to search for an author...',
            'id': 'author-search-input',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = PDFDocument
        fields = ['title', 'author', 'file', 'document_date', 'document_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.HiddenInput(attrs={'id': 'author-hidden-input'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'document_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        """
        - Remove the file field when editing an existing instance.
        - Populate the author_search field if an author is already set.
        """
        super().__init__(*args, **kwargs)
        
        # If the form is for an existing instance, remove the 'file' field.
        if self.instance and self.instance.pk:
            if 'file' in self.fields:
                del self.fields['file']
        
        if self.instance and self.instance.author:
            self.fields['author_search'].initial = self.instance.author.get_full_name()

        # The author field is not required as per the model definition (null=True)
        self.fields['author'].required = False

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['quote_text', 'page_number']
        widgets = {
            'quote_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter quote text'}),
            'page_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter page number'}),
        }
