from typing import List

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .models import Photo, PhotoDocument
from .schemas import (
    AnalysisResponseSchema,
    AnalyzeRequestSchema,
    DescriptionUpdateSchema,
    PhotoDocumentDetailSchema,
    PhotoDocumentListSchema,
    PhotoSchema,
)
from ai_services.services import analyze_document_content

router = Router(tags=["Photos"])


def _build_photo_url(request, photo) -> str | None:
    """Return an absolute URL for photo.file, handling relative MEDIA_URL."""
    if not photo.file:
        return None
    url = photo.file.url
    # MEDIA_URL may be configured without a leading slash ('media/')
    if not url.startswith(("http://", "https://")):
        if not url.startswith("/"):
            url = "/" + url
    return request.build_absolute_uri(url)


# ── Raw photos ────────────────────────────────────────────────────────────────

@router.get("/", response=List[PhotoSchema], auth=JWTAuth())
def list_photos(request):
    """Return all raw Photo objects."""
    return list(Photo.objects.all())


# ── Photo Document — List ─────────────────────────────────────────────────────

@router.get("/documents/", response=List[PhotoDocumentListSchema], auth=JWTAuth())
def list_photo_documents(request, offset: int = 0, limit: int = 50):
    """
    Return Photo Documents, newest first.
    Supports optional pagination via `offset` and `limit` query params.
    """
    qs = PhotoDocument.objects.all()[offset : offset + limit]
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "description": doc.description or "",
            "photo_count": doc.photos.count(),
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
        }
        for doc in qs
    ]


# ── Photo Document — Detail ───────────────────────────────────────────────────

@router.get("/documents/{doc_id}/", response=PhotoDocumentDetailSchema, auth=JWTAuth())
def get_photo_document(request, doc_id: int):
    """Return full Photo Document detail including absolute-URL photos."""
    doc = get_object_or_404(PhotoDocument, pk=doc_id)
    photos = [
        {
            "id": photo.id,
            "file_name": photo.file_name,
            "file_url": _build_photo_url(request, photo),
            "width": photo.width,
            "height": photo.height,
        }
        for photo in doc.photos.all()
    ]
    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description or "",
        "ai_analysis": doc.ai_analysis or "",
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "photos": photos,
    }


# ── Photo Document — Inline description edit ─────────────────────────────────

@router.patch("/documents/{doc_id}/description/", auth=JWTAuth())
def update_description(request, doc_id: int, payload: DescriptionUpdateSchema):
    """
    Persist an updated HTML description (from the inline editor).
    Mirrors the legacy AJAX endpoint: /photos/document/{id}/ajax_update_description/
    """
    doc = get_object_or_404(PhotoDocument, pk=doc_id)
    doc.description = payload.description
    doc.save(update_fields=["description", "updated_at"])
    return {"success": True}


# ── Photo Document — AI Analysis ──────────────────────────────────────────────

@router.post("/documents/{doc_id}/analyze/", response=AnalysisResponseSchema, auth=JWTAuth())
def analyze_photo_document(request, doc_id: int, payload: AnalyzeRequestSchema):
    """
    Trigger AI analysis with the specified persona.
    Personas: forensic_clerk | official_scribe | summary_clerk
    Mirrors the legacy AJAX endpoint: /ai/analyze/photo/{pk}/
    """
    doc = get_object_or_404(PhotoDocument, pk=doc_id)
    persona = payload.effective_persona()
    success = analyze_document_content(doc, persona_key=persona)
    if success:
        return {"status": "success", "analysis": doc.ai_analysis}
    return {"status": "error", "message": "Analysis failed in the backend service."}


@router.delete("/documents/{doc_id}/analyze/", response=AnalysisResponseSchema, auth=JWTAuth())
def clear_photo_document_analysis(request, doc_id: int):
    """
    Clear the stored AI analysis.
    Mirrors the legacy AJAX endpoint: /ai/clear/photo/{pk}/
    """
    doc = get_object_or_404(PhotoDocument, pk=doc_id)
    doc.ai_analysis = ""
    doc.save(update_fields=["ai_analysis", "updated_at"])
    return {"status": "success"}
