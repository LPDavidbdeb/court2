from typing import List, Optional
from django.shortcuts import get_object_or_404
from .models import PDFDocument, Quote

# --- PDF Document Services ---
def list_pdfs_service() -> List[PDFDocument]:
    return PDFDocument.objects.select_related('author').all()

def get_pdf_service(pdf_id: int) -> PDFDocument:
    return get_object_or_404(PDFDocument.objects.select_related('author'), pk=pdf_id)

def create_pdf_service(data: dict) -> PDFDocument:
    return PDFDocument.objects.create(**data)

def update_pdf_service(pdf_id: int, data: dict) -> PDFDocument:
    pdf = get_pdf_service(pdf_id)
    for attr, value in data.items():
        setattr(pdf, attr, value)
    pdf.save()
    return pdf

def delete_pdf_service(pdf_id: int) -> None:
    pdf = get_pdf_service(pdf_id)
    pdf.delete()

# --- Quote Services ---
def list_pdf_quotes_service(pdf_id: Optional[int] = None) -> List[Quote]:
    qs = Quote.objects.all()
    if pdf_id:
        qs = qs.filter(pdf_document_id=pdf_id)
    return qs

def get_pdf_quote_service(quote_id: int) -> Quote:
    return get_object_or_404(Quote, pk=quote_id)
