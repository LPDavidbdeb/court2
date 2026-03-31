from typing import List
from ninja import Router
from .models import Photo
from .schemas import PhotoDocumentSchema

router = Router(tags=["Photos"])

@router.get("/", response=List[PhotoDocumentSchema])
def list_photos(request):
    """
    Return the photo gallery (all photos).
    """
    return Photo.objects.all()

