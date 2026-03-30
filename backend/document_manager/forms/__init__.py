from django import forms
from django.contrib.auth import get_user_model
from ..models import Document

User = get_user_model()

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'author', 'document_original_date', 'solemn_declaration', 'source_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.Select(attrs={'class': 'form-control', 'id': 'author-select'}),
            'document_original_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'solemn_declaration': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'source_type': forms.Select(attrs={'class': 'form-control'}),
        }
