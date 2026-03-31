from typing import List, Optional
from django.shortcuts import get_object_or_404
from .models import EmailThread, Email, Quote
from django.db.models import Min

# --- Thread Services ---
def list_threads_service() -> List[EmailThread]:
    return EmailThread.objects.annotate(
        start_date=Min('emails__date_sent')
    ).select_related('protagonist').order_by('-start_date')

def get_thread_service(thread_id: int) -> EmailThread:
    return get_object_or_404(
        EmailThread.objects.prefetch_related('emails', 'emails__sender_protagonist'), 
        pk=thread_id
    )

def delete_thread_service(thread_id: int) -> None:
    thread = get_object_or_404(EmailThread, pk=thread_id)
    thread.delete()

# --- Email Services ---
def list_emails_service() -> List[Email]:
    return Email.objects.select_related('sender_protagonist').all()

def get_email_service(email_id: int) -> Email:
    return get_object_or_404(Email.objects.prefetch_related('recipient_protagonists'), pk=email_id)

def create_email_service(data: dict) -> Email:
    recipients = data.pop('recipient_protagonists_ids', [])
    email = Email.objects.create(**data)
    if recipients:
        email.recipient_protagonists.set(recipients)
    return email

def update_email_service(email_id: int, data: dict) -> Email:
    email = get_email_service(email_id)
    recipients = data.pop('recipient_protagonists_ids', None)
    for attr, value in data.items():
        setattr(email, attr, value)
    email.save()
    if recipients is not None:
        email.recipient_protagonists.set(recipients)
    return email

def delete_email_service(email_id: int) -> None:
    email = get_email_service(email_id)
    email.delete()

# --- Quote Services ---
def list_quotes_service(email_id: Optional[int] = None) -> List[Quote]:
    qs = Quote.objects.all()
    if email_id:
        qs = qs.filter(email_id=email_id)
    return qs
