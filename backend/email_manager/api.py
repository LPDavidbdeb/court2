from typing import List
from ninja import Router
from django.db.models import Min
from django.shortcuts import get_object_or_404
from .models import EmailThread, Email, Quote
from .schemas import EmailThreadSchema, EmailThreadDetailSchema, EmailSchema, EmailQuoteSchema

router = Router(tags=["Emails"])

@router.get("/threads", response=List[EmailThreadSchema])
def list_threads(request):
    """
    List all email threads, ordered by the date of the first email in the thread.
    """
    return EmailThread.objects.annotate(
        start_date=Min('emails__date_sent')
    ).order_by('-start_date')

@router.get("/threads/{thread_id}", response=EmailThreadDetailSchema)
def get_thread(request, thread_id: int):
    """
    Retrieve details of a specific email thread, including all emails.
    """
    thread = get_object_or_404(EmailThread, pk=thread_id)
    return thread

@router.get("/emails/{email_id}", response=EmailSchema)
def get_email(request, email_id: int):
    """
    Retrieve details of a specific email.
    """
    email = get_object_or_404(Email, pk=email_id)
    return email

@router.get("/emails/{email_id}/quotes", response=List[EmailQuoteSchema])
def list_email_quotes(request, email_id: int):
    """
    List all quotes for a specific email.
    """
    return Quote.objects.filter(email_id=email_id)
