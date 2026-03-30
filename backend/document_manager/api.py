from typing import List
from ninja import Router
from .models import Document, LibraryNode
from .schemas import DocumentSchema, LibraryNodeSchema
from mptt.utils import get_cached_trees

router = Router(tags=["Documents"])

@router.get("/", response=List[DocumentSchema])
def list_documents(request):
    return Document.objects.all()

@router.get("/{document_id}/tree", response=List[LibraryNodeSchema])
def get_document_tree(request, document_id: int):
    # Fetch all nodes for the document
    nodes = LibraryNode.objects.filter(document_id=document_id)
    
    # Use MPTT's get_cached_trees to build the hierarchy in-memory
    # This expects a queryset and returns a list of root nodes with children cached.
    root_nodes = get_cached_trees(nodes)
    return root_nodes
