from typing import List, Dict, Any
from .models import LibraryNode

def get_document_tree_service(document_id: int) -> List[Dict[str, Any]]:
    """
    Service to retrieve the treebeard hierarchy for a specific document.
    Returns the annotated list format.
    """
    # Using treebeard's get_annotated_list on the queryset
    # We first get the roots for this document, then get the full tree for each
    roots = LibraryNode.objects.filter(document_id=document_id, depth=1)
    
    full_tree = []
    for root in roots:
        full_tree.extend(LibraryNode.get_annotated_list(parent=root))
        
    return full_tree
