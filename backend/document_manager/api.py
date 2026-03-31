from typing import List, Any
from ninja import Router
from .models import Document
from .schemas import DocumentSchema
from .services import get_document_tree_service

router = Router(tags=["Documents"])

@router.get("/", response=List[DocumentSchema])
def list_documents(request):
    """
    List all documents in the library.
    """
    return Document.objects.all()

@router.get("/{document_id}/tree", response=List[Any])
def get_document_tree(request, document_id: int):
    """
    Returns the treebeard annotated list for a document.
    """
    # treebeard returns tuples (instance, info)
    annotated_list = get_document_tree_service(document_id)
    
    # Format the data for JSON serialization
    result = []
    for instance, info in annotated_list:
        result.append({
            "id": instance.id,
            "item": instance.item,
            "depth": instance.depth,
            "document_id": instance.document_id,
            "content_type_id": instance.content_type_id,
            "object_id": instance.object_id,
            "info": info # This contains 'open' and 'close' flags for the tree
        })
    return result
