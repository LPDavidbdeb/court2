from typing import List, Optional, Dict, Any
from django.shortcuts import get_object_or_404
from .models import Document, Statement, LibraryNode
from mptt.utils import get_cached_trees

# --- Document Services ---
def list_documents_service() -> List[Document]:
    return Document.objects.select_related('author').all()

def get_document_service(doc_id: int) -> Document:
    return get_object_or_404(Document.objects.select_related('author'), pk=doc_id)

def create_document_service(data: dict) -> Document:
    return Document.objects.create(**data)

def update_document_service(doc_id: int, data: dict) -> Document:
    doc = get_document_service(doc_id)
    for attr, value in data.items():
        setattr(doc, attr, value)
    doc.save()
    return doc

def delete_document_service(doc_id: int) -> None:
    doc = get_document_service(doc_id)
    doc.delete()

# --- Tree/Hierarchy Services ---
def get_document_tree_service(document_id: int) -> List[Any]:
    """
    Returns the treebeard annotated list for a document.
    """
    roots = LibraryNode.objects.filter(document_id=document_id, depth=1)
    full_tree = []
    for root in roots:
        full_tree.extend(LibraryNode.get_annotated_list(parent=root))
    return full_tree

# --- Statement Services ---
def list_statements_service() -> List[Statement]:
    return Statement.objects.all()

def create_statement_service(data: dict) -> Statement:
    return Statement.objects.create(**data)
