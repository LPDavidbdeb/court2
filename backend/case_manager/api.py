from typing import List
from ninja import Router
from .models import LegalCase
from .schemas import LegalCaseSchema, LegalCaseDetailSchema
from .case_service import get_case_protagonists
from protagonist_manager.schemas import ProtagonistSchema # Need to create this

router = Router(tags=["Cases"])

@router.get("/", response=List[LegalCaseSchema])
def list_cases(request):
    return LegalCase.objects.all()

@router.get("/{case_id}", response=LegalCaseDetailSchema)
def get_case(request, case_id: int):
    case = LegalCase.objects.prefetch_related('contestations', 'produced_exhibits').get(pk=case_id)
    return case

@router.get("/{case_id}/protagonists", response=List[ProtagonistSchema])
def list_case_protagonists(request, case_id: int):
    return get_case_protagonists(case_id)
