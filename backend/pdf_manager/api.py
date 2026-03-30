from typing import List, Dict, Any
from ninja import Router
from .models import PDFDocument
from .services import extract_tables_from_pdf

router = Router(tags=["PDFs"])

@router.get("/{pdf_id}/tables", response=List[Dict[str, Any]])
def get_pdf_tables(request, pdf_id: int, pages: str = "all"):
    """
    Expose PDF table parsing results via tabula-py.
    """
    return extract_tables_from_pdf(pdf_id, pages=pages)

@router.get("/", response=List[Dict[str, Any]])
def list_pdfs(request):
    """
    Simple list of PDFs.
    """
    return list(PDFDocument.objects.all().values("id", "title", "uploaded_at"))
