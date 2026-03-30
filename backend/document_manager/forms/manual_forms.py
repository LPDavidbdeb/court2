from django import forms
from ..models import Document, Statement, LibraryNode, DocumentSource
from django.contrib.contenttypes.models import ContentType

class ProducedDocumentForm(forms.ModelForm):
    """Form to create the top-level 'Produced' Document."""
    class Meta:
        model = Document
        fields = ['title', 'author']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.Select(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        # Force the source_type to 'PRODUCED' on save
        instance = super().save(commit=False)
        instance.source_type = DocumentSource.PRODUCED
        if commit:
            instance.save()
        return instance

class NodeForm(forms.Form):
    """A form for adding or editing a node (item + statement) in the tree."""
    item = forms.CharField(
        label="Title / Item", 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    text = forms.CharField(
        label="Content / Statement Text", 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        required=False
    )

# REVISED FORM
class LibraryNodeCreateForm(forms.ModelForm):
    """
    Form for creating a new LibraryNode.
    It validates the node's own fields and passes text for a potential new statement.
    The view is responsible for the logic of creating/linking the content_object.
    """
    # This field corresponds to the 'Create New Statement' tab's textarea.
    # It's not a model field, just a way to pass the text to the view.
    text = forms.CharField(
        label="New Statement Text",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )

    class Meta:
        model = LibraryNode
        fields = ['item'] # The only direct field on the node we're editing from the form
        widgets = {
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Node Title/Short Name'}),
        }
