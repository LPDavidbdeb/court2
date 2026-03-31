from typing import List
from ninja import Router
from .schemas import PDFDocumentSchema, PDFDocumentCreateSchema, PDFQuoteSchema
from .services import (
    list_pdfs_service,
    get_pdf_service,
    create_pdf_service,
    update_pdf_service,
    delete_pdf_service,
    list_pdf_quotes_service,
    get_pdf_quote_service
)

router = Router(tags=["PDFs"])

@router.get("/", response=List[PDFDocumentSchema])
def list_pdfs(request):
    return list_pdfs_service()

@router.get("/{pdf_id}", response=PDFDocumentSchema)
def get_pdf(request, pdf_id: int):
    return get_pdf_service(pdf_id)

@router.post("/", response=PDFDocumentSchema)
def create_pdf(request, data: PDFDocumentCreateSchema):
    return create_pdf_service(data.dict())

@router.put("/{pdf_id}", response=PDFDocumentSchema)
def update_pdf(request, pdf_id: int, data: PDFDocumentCreateSchema):
    return update_pdf_service(pdf_id, data.dict())

@router.delete("/{pdf_id}")
def delete_pdf(request, pdf_id: int):
    delete_pdf_service(pdf_id)
    return {"success": True}

@router.get("/{pdf_id}/quotes", response=List[PDFQuoteSchema])
def list_pdf_quotes(request, pdf_id: int):
    return list_pdf_quotes_service(pdf_id=pdf_id)
