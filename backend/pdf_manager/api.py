from typing import List
from django.shortcuts import get_object_or_404
from django.conf import settings
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from .models import PDFDocument, Quote
from .schemas import (
    PDFDocumentSchema, 
    PDFDocumentCreateSchema, 
    PDFQuoteSchema, 
    QuoteCreateSchema
)

router = Router(tags=["PDFs"])

def _get_absolute_media_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith(('http://', 'https://')):
        return url
    
    # Try to get backend URL from settings or default to local dev
    backend_base = getattr(settings, 'BACKEND_URL', 'http://localhost:8001')
    
    # Ensure no double slashes
    base = backend_base.rstrip('/')
    path = url if url.startswith('/') else f'/{url}'
    return f"{base}{path}"

def _pdf_to_dict(p: PDFDocument) -> dict:
    """Helper to materialize PDFDocument and its nested related managers for Pydantic."""
    
    # Handle author materialization manually if it exists to evaluation RelatedManagers
    author_data = None
    if p.author:
        author_data = {
            "id": p.author.id,
            "first_name": p.author.first_name,
            "last_name": p.author.last_name,
            "role": p.author.role,
            "linkedin_url": p.author.linkedin_url,
            "created_at": p.author.created_at,
            "updated_at": p.author.updated_at,
            "emails": list(p.author.emails.all()),
        }

    return {
        "id": p.id,
        "title": p.title,
        "author": author_data,
        "document_date": p.document_date,
        "document_type": p.document_type,
        "file": _get_absolute_media_url(p.file.url) if p.file else None,
        "ai_analysis": p.ai_analysis,
        "uploaded_at": p.uploaded_at,
        "public_url": p.get_public_url(),
        "created_at": p.uploaded_at,
        "updated_at": p.uploaded_at,
        "quotes": list(p.quotes.all()),
    }

@router.get("/", response=List[PDFDocumentSchema], auth=JWTAuth())
def list_pdfs(request):
    """List all PDF documents with pre-fetched related data."""
    qs = PDFDocument.objects.select_related("author", "document_type").prefetch_related("author__emails", "quotes").all()
    return [_pdf_to_dict(p) for p in qs]

@router.get("/{pdf_id}/", response=PDFDocumentSchema, auth=JWTAuth())
def get_pdf(request, pdf_id: int):
    """Retrieve a specific PDF document detail."""
    p = get_object_or_404(
        PDFDocument.objects.select_related("author", "document_type").prefetch_related("author__emails", "quotes"),
        pk=pdf_id
    )
    return _pdf_to_dict(p)

@router.post("/{pdf_id}/quotes/", response=PDFQuoteSchema, auth=JWTAuth())
def create_pdf_quote(request, pdf_id: int, data: QuoteCreateSchema):
    """Create a new quote for a specific PDF document."""
    pdf = get_object_or_404(PDFDocument, pk=pdf_id)
    quote = Quote.objects.create(
        pdf_document=pdf,
        **data.dict()
    )
    return quote

@router.delete("/{pdf_id}/", auth=JWTAuth())
def delete_pdf(request, pdf_id: int):
    """Delete a PDF document."""
    pdf = get_object_or_404(PDFDocument, pk=pdf_id)
    pdf.delete()
    return {"success": True}

@router.delete("/quotes/{quote_id}/", auth=JWTAuth())
def delete_pdf_quote(request, quote_id: int):
    """Delete a specific quote."""
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.delete()
    return {"success": True}
