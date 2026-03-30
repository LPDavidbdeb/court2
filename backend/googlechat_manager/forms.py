from django import forms
from .models import ChatSequence

class ChatSequenceForm(forms.ModelForm):
    class Meta:
        model = ChatSequence
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Discussion about the Sofa Repayment'})
        }