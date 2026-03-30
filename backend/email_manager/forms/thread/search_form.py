from django import forms

class EmailAjaxSearchForm(forms.Form):
    """
    Form for searching emails, now linked to Protagonist model.
    """
    # This field will be the AJAX-powered search input in the template.
    # Its value will be used to search for protagonists, but not directly submitted as sender_email.
    # The actual email for the Gmail API query will come from the selected protagonist's emails.
    # We'll use a hidden field to store the selected protagonist's ID.
    protagonist_search_input = forms.CharField(
        label="Search Protagonist (Name or Email)",
        max_length=255,
        required=False, # Make it optional, as user might just enter a date and excerpt
        help_text="Type to search for an existing protagonist, or leave blank to search by specific email below."
    )

    # Hidden field to store the selected Protagonist's ID
    # This will be populated by JavaScript when a suggestion is selected.
    protagonist_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    # This field is for direct email input if no protagonist is selected/found.
    # It will be used as a fallback if protagonist_id is empty.
    manual_participant_email = forms.EmailField(
        label="Or Enter Specific Email (if no protagonist selected)",
        max_length=255,
        required=False,
        help_text="e.g., specific.person@example.com. Used if no protagonist is selected above."
    )

    date_sent = forms.DateField(
        label="Date Sent",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True,
        help_text="e.g., YYYY-MM-DD"
    )
    email_excerpt = forms.CharField(
        label="Email Excerpt (optional, for content search)",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text="A phrase or keyword from the email body/subject."
    )

    def clean(self):
        cleaned_data = super().clean()
        protagonist_id = cleaned_data.get('protagonist_id')
        manual_email = cleaned_data.get('manual_participant_email')

        # Ensure at least one way of identifying the participant is provided
        if not protagonist_id and not manual_email:
            raise forms.ValidationError(
                "Please select a protagonist or enter a specific email address to search."
            )
        return cleaned_data

