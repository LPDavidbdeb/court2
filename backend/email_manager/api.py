from typing import List, Optional

from django.db.models import Min
from django.shortcuts import get_object_or_404
from ninja import File, Form, Router
from ninja.files import UploadedFile
from ninja_jwt.authentication import JWTAuth

from protagonist_manager.models import Protagonist

from .models import Email, EmailThread, Quote
from .schemas import (
    EmailCreateSchema,
    EmailQuoteSchema,
    EmailSchema,
    EmailThreadDetailSchema,
    EmailThreadSchema,
    UploadResponseSchema,
)
from .utils import import_eml_file

router = Router(tags=["Emails"])


# ── Thread — List ─────────────────────────────────────────────────────────────

@router.get("/threads/", response=List[EmailThreadSchema], auth=JWTAuth())
def list_threads(request):
    """
    Returns all saved email threads, newest first.
    `start_date` is annotated as the date of the earliest email in the thread —
    matching the legacy "Start Date" column in list.html.
    Protagonist data is nested so the frontend needs no extra API call.
    """
    return list(
        EmailThread.objects
        .annotate(start_date=Min("emails__date_sent"))
        .select_related("protagonist")
        .order_by("-updated_at")
    )


# ── Thread — Detail ───────────────────────────────────────────────────────────

@router.get("/threads/{thread_id}/", response=EmailThreadDetailSchema, auth=JWTAuth())
def get_thread(request, thread_id: int):
    """
    Returns full thread metadata plus all emails ordered by sent date.
    Email.Meta.ordering = ['date_sent'] guarantees chronological order.
    """
    thread = get_object_or_404(
        EmailThread.objects
        .select_related("protagonist")
        .prefetch_related("emails__sender_protagonist"),
        pk=thread_id,
    )
    # Materialise the RelatedManager so Pydantic receives a plain list
    return {
        "id": thread.id,
        "thread_id": thread.thread_id,
        "subject": thread.subject,
        "start_date": None,   # not annotated on detail fetch
        "saved_at": thread.saved_at,
        "updated_at": thread.updated_at,
        "protagonist": thread.protagonist,
        "emails": list(thread.emails.order_by("date_sent")),
    }


# ── Thread — Delete ───────────────────────────────────────────────────────────

@router.delete("/threads/{thread_id}/", auth=JWTAuth())
def delete_thread(request, thread_id: int):
    """
    Deletes a thread and all its child Email objects (CASCADE).
    Mirrors the legacy 'Delete' form button in list.html and detail.html.
    """
    thread = get_object_or_404(EmailThread, pk=thread_id)
    thread.delete()
    return {"success": True}


# ── EML Upload ────────────────────────────────────────────────────────────────

@router.post("/upload/", response=UploadResponseSchema, auth=JWTAuth())
def upload_eml(
    request,
    eml_file: UploadedFile = File(...),
    protagonist_id: Optional[int] = Form(None),
):
    """
    Accepts a multipart/form-data upload of a single .eml file.
    Parses headers (Subject, From, To, Cc, Date, Message-ID) and body, then
    persists one new EmailThread + one Email.  Mirrors EmlUploadView.form_valid().

    Fields:
      eml_file      — the .eml file (required)
      protagonist_id — integer FK to Protagonist (optional)
    """
    protagonist: Optional[Protagonist] = None
    if protagonist_id:
        protagonist = Protagonist.objects.filter(pk=protagonist_id).first()

    try:
        email_obj = import_eml_file(eml_file, linked_protagonist=protagonist)
    except Exception as exc:
        return UploadResponseSchema(
            success=False,
            thread_id=0,
            subject=None,
            message=str(exc),
        )

    return UploadResponseSchema(
        success=True,
        thread_id=email_obj.thread.pk,
        subject=email_obj.subject,
    )


# ── Emails (raw, kept for backward compat) ────────────────────────────────────

@router.get("/emails/", response=List[EmailSchema], auth=JWTAuth())
def list_emails(request):
    return list(Email.objects.select_related("sender_protagonist").all())


@router.get("/emails/{email_id}/", response=EmailSchema, auth=JWTAuth())
def get_email(request, email_id: int):
    return get_object_or_404(
        Email.objects.prefetch_related("recipient_protagonists"),
        pk=email_id,
    )


@router.get("/emails/{email_id}/quotes/", response=List[EmailQuoteSchema], auth=JWTAuth())
def list_email_quotes(request, email_id: int):
    return list(Quote.objects.filter(email_id=email_id))
