from typing import List
from ninja import Router
from .models import PDFDocument
from .schemas import PDFDocumentSchema, PDFTableDataSchema
from .services import extract_tables_from_pdf

router = Router(tags=["PDFs"])

@router.get("/", response=List[PDFDocumentSchema])
def list_pdfs(request):
    """
    List all PDF documents.
    """
    return PDFDocument.objects.all()

@router.get("/{pdf_id}/tables", response=List[PDFTableDataSchema])
def get_pdf_tables(request, pdf_id: int, pages: str = "all"):
    """
    Trigger Tabula PDF parsing and return extracted tabular data as JSON.
    """
    return extract_tables_from_pdf(pdf_id, pages=pages)
