from typing import List, Optional
from django.shortcuts import get_object_or_404
from .models import LegalCase, PerjuryContestation, ProducedExhibit

# Original services imported as a facade for views.py
from .exhibit_service import (
    refresh_case_exhibits,
    get_datetime_for_sorting,
    rebuild_produced_exhibits,
)

from .archive_service import (
    rebuild_global_exhibits,
    get_item_metadata,
    get_sort_date,
)

# CRUD Services for the new API
def list_cases_service() -> List[LegalCase]:
    return LegalCase.objects.all()

def get_case_service(case_id: int) -> LegalCase:
    return get_object_or_404(
        LegalCase.objects.prefetch_related('contestations', 'produced_exhibits'), 
        pk=case_id
    )

def create_case_service(data: dict) -> LegalCase:
    return LegalCase.objects.create(**data)

def update_case_service(case_id: int, data: dict) -> LegalCase:
    case = get_object_or_404(LegalCase, pk=case_id)
    for attr, value in data.items():
        setattr(case, attr, value)
    case.save()
    return case

def delete_case_service(case_id: int) -> None:
    case = get_object_or_404(LegalCase, pk=case_id)
    case.delete()

# Contestation Services
def list_contestations_service(case_id: int) -> List[PerjuryContestation]:
    return PerjuryContestation.objects.filter(case_id=case_id)

def create_contestation_service(case_id: int, data: dict) -> PerjuryContestation:
    return PerjuryContestation.objects.create(case_id=case_id, **data)

def update_contestation_service(contestation_id: int, data: dict) -> PerjuryContestation:
    contestation = get_object_or_404(PerjuryContestation, pk=contestation_id)
    for attr, value in data.items():
        setattr(contestation, attr, value)
    contestation.save()
    return contestation

def delete_contestation_service(contestation_id: int) -> None:
    contestation = get_object_or_404(PerjuryContestation, pk=contestation_id)
    contestation.delete()
