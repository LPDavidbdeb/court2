from typing import List, Any
from ninja import Router
from .schemas import DocumentSchema, DocumentCreateSchema, StatementSchema
from .services import (
    list_documents_service,
    get_document_service,
    create_document_service,
    update_document_service,
    delete_document_service,
    get_document_tree_service,
    list_statements_service
)

router = Router(tags=["Documents"])

@router.get("/", response=List[DocumentSchema])
def list_documents(request):
    return list_documents_service()

@router.get("/{doc_id}", response=DocumentSchema)
def get_document(request, doc_id: int):
    return get_document_service(doc_id)

@router.post("/", response=DocumentSchema)
def create_document(request, data: DocumentCreateSchema):
    return create_document_service(data.dict())

@router.put("/{doc_id}", response=DocumentSchema)
def update_document(request, doc_id: int, data: DocumentCreateSchema):
    return update_document_service(doc_id, data.dict())

@router.delete("/{doc_id}")
def delete_document(request, doc_id: int):
    delete_document_service(doc_id)
    return {"success": True}

@router.get("/{doc_id}/tree", response=List[Any])
def get_document_tree(request, doc_id: int):
    annotated_list = get_document_tree_service(doc_id)
    result = []
    for instance, info in annotated_list:
        result.append({
            "id": instance.id,
            "item": instance.item,
            "depth": instance.depth,
            "document_id": instance.document_id,
            "content_type_id": instance.content_type_id,
            "object_id": instance.object_id,
            "info": info
        })
    return result
