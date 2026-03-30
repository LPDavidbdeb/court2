from django import forms
from .models import Protagonist

class ProtagonistForm(forms.ModelForm):
    class Meta:
        model = Protagonist
        fields = ['first_name', 'last_name', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Role'}),
        }
