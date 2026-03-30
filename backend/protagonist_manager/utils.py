import re
from .models import Protagonist, ProtagonistEmail

def get_or_create_protagonist_from_email_string(email_string: str):
    """
    Parses a raw email string (e.g., '"First Last" <email@example.com>') to find or create
    a Protagonist.

    Args:
        email_string (str): The raw email string from the email header.

    Returns:
        Protagonist: The found or newly created Protagonist instance, or None if the
                     email_string is invalid.
    """
    if not email_string or not isinstance(email_string, str):
        return None

    # Regex to extract name and email. Handles cases with and without a name.
    match = re.match(r'\s*"?([^"<]+)"?\s*<([^>]+)>|([^<@\s]+@[^>@\s]+)', email_string)
    if not match:
        return None

    if match.group(1) and match.group(2):
        # Format '"Name" <email@addr>'
        name = match.group(1).strip()
        email_address = match.group(2).strip()
    elif match.group(3):
        # Format 'email@addr'
        name = email_address = match.group(3).strip()
    else:
        return None

    # Now, find or create the protagonist
    try:
        # 1. Check if the email address is already registered
        protagonist_email = ProtagonistEmail.objects.select_related('protagonist').get(email_address__iexact=email_address)
        return protagonist_email.protagonist
    except ProtagonistEmail.DoesNotExist:
        # 2. If not, create a new Protagonist and their email
        # A simple heuristic for splitting name into first and last
        name_parts = name.split()
        first_name = name_parts[0] if name_parts else email_address
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        # Create the new protagonist
        new_protagonist = Protagonist.objects.create(
            first_name=first_name,
            last_name=last_name,
            role='Auto-Generated'  # A default role to indicate it was auto-created
        )

        # Create the associated email address
        ProtagonistEmail.objects.create(
            protagonist=new_protagonist,
            email_address=email_address
        )

        return new_protagonist
