from typing import List
from ninja import Router
from .models import Photo, PhotoDocument
from .schemas import PhotoSchema, PhotoDocumentSchema

router = Router(tags=["Photos"])

@router.get("/", response=List[PhotoSchema])
def list_photos(request):
    """
    Return the photo gallery (all raw photos).
    """
    return Photo.objects.all()

@router.get("/documents", response=List[PhotoDocumentSchema])
def list_photo_documents(request):
    """
    Return all photo-based documents.
    """
    return PhotoDocument.objects.all()
