from django import forms
from ..models import Photo, PhotoType, PhotoDocument

class PhotoDocumentSingleUploadForm(forms.Form):
    """
    A streamlined form to create a PhotoDocument from a single new image upload.
    """
    file = forms.ImageField(
        label="Photo File",
        help_text="Select the image file for the document.",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    title = forms.CharField(
        label="Document Title",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        label="Description (Optional)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    datetime_original = forms.DateTimeField(
        required=True,
        label="Document Date/Time",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        help_text="The date and time the document was created, not when it was scanned."
    )

class PhotoDocumentForm(forms.ModelForm):
    """
    A form for creating and updating PhotoDocument objects by grouping existing photos.
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

    photos = forms.ModelMultipleChoiceField(
        queryset=Photo.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
        required=True,
        help_text="Select one or more photos that have been marked with the 'Document' type."
    )

    class Meta:
        model = PhotoDocument
        fields = ['title', 'author', 'description', 'photos', 'created_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.HiddenInput(attrs={'id': 'author-hidden-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'created_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        """
        - Dynamically set the queryset for the 'photos' field.
        - Populate the author_search field if an author is already set.
        """
        super().__init__(*args, **kwargs)
        
        try:
            document_photo_type = PhotoType.objects.get(name='Document')
            self.fields['photos'].queryset = Photo.objects.filter(photo_type=document_photo_type)
        except PhotoType.DoesNotExist:
            self.fields['photos'].queryset = Photo.objects.none()

        if self.instance and self.instance.author:
            self.fields['author_search'].initial = self.instance.author.get_full_name()

        # The author field is not required as per the model definition (null=True)
        self.fields['author'].required = False
