from typing import List
from ninja import Router
from django.shortcuts import get_object_or_404
from .schemas import (
    LegalCaseSchema, 
    LegalCaseDetailSchema, 
    CaseCreateSchema,
    PerjuryContestationSchema,
    ContestationCreateSchema
)
from .services import (
    list_cases_service,
    get_case_service,
    create_case_service,
    update_case_service,
    delete_case_service,
    list_contestations_service,
    create_contestation_service,
    update_contestation_service,
    delete_contestation_service
)

router = Router(tags=["Cases"])

# Case Endpoints
@router.get("/", response=List[LegalCaseSchema])
def list_cases(request):
    return list_cases_service()

@router.post("/", response=LegalCaseSchema)
def create_case(request, data: CaseCreateSchema):
    return create_case_service(data.dict())

@router.get("/{case_id}", response=LegalCaseDetailSchema)
def get_case(request, case_id: int):
    return get_case_service(case_id)

@router.put("/{case_id}", response=LegalCaseSchema)
def update_case(request, case_id: int, data: CaseCreateSchema):
    return update_case_service(case_id, data.dict())

@router.delete("/{case_id}")
def delete_case(request, case_id: int):
    delete_case_service(case_id)
    return {"success": True}

# Contestation Endpoints
@router.get("/{case_id}/contestations", response=List[PerjuryContestationSchema])
def list_contestations(request, case_id: int):
    return list_contestations_service(case_id)

@router.post("/{case_id}/contestations", response=PerjuryContestationSchema)
def create_contestation(request, case_id: int, data: ContestationCreateSchema):
    return create_contestation_service(case_id, data.dict())

@router.put("/contestations/{contestation_id}", response=PerjuryContestationSchema)
def update_contestation(request, contestation_id: int, data: ContestationCreateSchema):
    return update_contestation_service(contestation_id, data.dict())

@router.delete("/contestations/{contestation_id}")
def delete_contestation(request, contestation_id: int):
    delete_contestation_service(contestation_id)
    return {"success": True}
