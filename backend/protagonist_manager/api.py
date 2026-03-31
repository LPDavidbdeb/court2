from typing import List

from django.db.models import Count
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .models import Protagonist, ProtagonistEmail
from .schemas import (
    ProtagonistCreateSchema,
    ProtagonistDetailSchema,
    ProtagonistListSchema,
    ProtagonistSchema,
)

router = Router(tags=["Protagonists"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detail_dict(p: Protagonist) -> dict:
    """Materialise related managers so Pydantic receives plain lists."""
    return {
        "id": p.id,
        "first_name": p.first_name,
        "last_name": p.last_name,
        "role": p.role,
        "linkedin_url": p.linkedin_url,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "emails": list(p.emails.all()),
        "email_thread_count": p.email_threads.count(),
        "photo_document_count": p.authored_photo_documents.count(),
        "email_threads": list(p.email_threads.order_by("-updated_at")),
        "authored_photo_documents": list(
            p.authored_photo_documents.order_by("-created_at")
        ),
    }


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/", response=List[ProtagonistListSchema], auth=JWTAuth())
def list_protagonists(request):
    """
    All protagonists ordered alphabetically, with denormalised evidence counts
    so the directory table needs no extra API calls.
    """
    return list(
        Protagonist.objects
        .prefetch_related("emails")
        .annotate(
            email_thread_count=Count("email_threads", distinct=True),
            photo_document_count=Count("authored_photo_documents", distinct=True),
        )
        .order_by("last_name", "first_name")
    )


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get("/{protagonist_id}/", response=ProtagonistDetailSchema, auth=JWTAuth())
def get_protagonist(request, protagonist_id: int):
    """
    Full protagonist profile with nested evidence:
    - email_threads  : EmailThread objects where protagonist is the FK subject
    - authored_photo_documents : PhotoDocument objects where protagonist is the author
    """
    p = get_object_or_404(
        Protagonist.objects.prefetch_related(
            "emails",
            "email_threads",
            "authored_photo_documents",
        ),
        pk=protagonist_id,
    )
    return _detail_dict(p)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/", response=ProtagonistSchema, auth=JWTAuth())
def create_protagonist(request, data: ProtagonistCreateSchema):
    emails = data.emails
    protagonist = Protagonist.objects.create(
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        linkedin_url=data.linkedin_url,
    )
    for e in emails:
        ProtagonistEmail.objects.create(
            protagonist=protagonist,
            email_address=e.email_address,
            description=e.description,
        )
    protagonist = Protagonist.objects.prefetch_related("emails").get(pk=protagonist.pk)
    return protagonist


# ── Update (full replace) ─────────────────────────────────────────────────────

@router.put("/{protagonist_id}/", response=ProtagonistDetailSchema, auth=JWTAuth())
def update_protagonist(request, protagonist_id: int, data: ProtagonistCreateSchema):
    p = get_object_or_404(Protagonist, pk=protagonist_id)
    p.first_name = data.first_name
    p.last_name = data.last_name
    p.role = data.role
    p.linkedin_url = data.linkedin_url
    p.save()
    # Sync emails: replace existing
    p.emails.all().delete()
    for e in data.emails:
        ProtagonistEmail.objects.create(
            protagonist=p, email_address=e.email_address, description=e.description
        )
    p.refresh_from_db()
    p = Protagonist.objects.prefetch_related(
        "emails", "email_threads", "authored_photo_documents"
    ).get(pk=p.pk)
    return _detail_dict(p)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{protagonist_id}/", auth=JWTAuth())
def delete_protagonist(request, protagonist_id: int):
    p = get_object_or_404(Protagonist, pk=protagonist_id)
    p.delete()
    return {"success": True}
