from django import forms
from ...models import Quote
from argument_manager.models import TrameNarrative


class QuoteForm(forms.ModelForm):
    """
    A form for creating a Quote and associating it with TrameNarrative objects.
    """
    # This field is for handling the reverse ManyToMany relationship.
    # It is not a direct field on the Quote model, so it is handled manually in the view.
    trames_narratives = forms.ModelMultipleChoiceField(
        queryset=TrameNarrative.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label="Associer à une ou plusieurs trames narratives",
        help_text="Sélectionnez les trames narratives que cette citation supporte ou contredit."
    )

    class Meta:
        model = Quote
        # 'trames_narratives' is removed from here because it is not a direct field.
        fields = ['quote_text']
        widgets = {
            'quote_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'quote_text': "Citation Extraite de l'Email",
        }
