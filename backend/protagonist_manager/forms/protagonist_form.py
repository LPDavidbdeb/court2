from django import forms
from ..models import Protagonist, ProtagonistEmail

class ProtagonistForm(forms.ModelForm):
    """
    Form for creating and updating Protagonist instances.
    'email' field is removed as it's now handled by ProtagonistEmail model.
    """
    class Meta:
        model = Protagonist
        fields = ['first_name', 'last_name', 'role'] # 'email' field removed
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'role': 'Role in Story',
        }

class ProtagonistEmailForm(forms.ModelForm):
    """
    Form for adding and updating ProtagonistEmail instances.
    """
    class Meta:
        model = ProtagonistEmail
        fields = ['email_address', 'description']
        widgets = {
            'email_address': forms.EmailInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'email_address': 'Email Address',
            'description': 'Description (e.g., Personal, Work)',
        }

