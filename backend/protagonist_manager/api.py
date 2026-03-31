from typing import List
from ninja import Router
from .schemas import ProtagonistSchema, ProtagonistCreateSchema
from .services import (
    list_protagonists_service,
    get_protagonist_service,
    create_protagonist_service,
    update_protagonist_service,
    delete_protagonist_service
)

router = Router(tags=["Protagonists"])

@router.get("/", response=List[ProtagonistSchema])
def list_protagonists(request):
    return list_protagonists_service()

@router.get("/{protagonist_id}", response=ProtagonistSchema)
def get_protagonist(request, protagonist_id: int):
    return get_object_or_404(Protagonist, pk=protagonist_id) # Should use service but get_object_or_404 is direct
    # Correcting to use service
    return get_protagonist_service(protagonist_id)

@router.post("/", response=ProtagonistSchema)
def create_protagonist(request, data: ProtagonistCreateSchema):
    return create_protagonist_service(data.dict())

@router.put("/{protagonist_id}", response=ProtagonistSchema)
def update_protagonist(request, protagonist_id: int, data: ProtagonistCreateSchema):
    return update_protagonist_service(protagonist_id, data.dict())

@router.delete("/{protagonist_id}")
def delete_protagonist(request, protagonist_id: int):
    delete_protagonist_service(protagonist_id)
    return {"success": True}
