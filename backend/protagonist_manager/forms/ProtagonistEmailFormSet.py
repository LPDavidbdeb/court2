from django import forms
from django.forms import inlineformset_factory
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

# Define the inline formset for Protagonist Emails
# This will allow creating/editing multiple ProtagonistEmail instances for a single Protagonist
ProtagonistEmailFormSet = inlineformset_factory(
    Protagonist,          # Parent model
    ProtagonistEmail,     # Child model
    form=ProtagonistEmailForm, # Form to use for each child instance
    extra=5,              # Display 5 empty forms by default for new emails
    max_num=5,            # Allow a maximum of 5 email forms
    can_delete=True,      # Allow marking existing emails for deletion (useful for update, but good to have)
    fields=['email_address', 'description'] # Fields to include in the formset forms
)
