from typing import List, Optional
from django.shortcuts import get_object_or_404
from .models import Protagonist, ProtagonistEmail

def list_protagonists_service() -> List[Protagonist]:
    return Protagonist.objects.all().prefetch_related('emails')

def get_protagonist_service(protagonist_id: int) -> Protagonist:
    return get_object_or_404(Protagonist.objects.prefetch_related('emails'), pk=protagonist_id)

def create_protagonist_service(data: dict) -> Protagonist:
    emails = data.pop('emails', [])
    protagonist = Protagonist.objects.create(**data)
    for email_data in emails:
        ProtagonistEmail.objects.create(protagonist=protagonist, **email_data)
    return protagonist

def update_protagonist_service(protagonist_id: int, data: dict) -> Protagonist:
    protagonist = get_protagonist_service(protagonist_id)
    emails = data.pop('emails', None)
    
    for attr, value in data.items():
        setattr(protagonist, attr, value)
    protagonist.save()
    
    if emails is not None:
        # Simple sync: replace existing emails
        protagonist.emails.all().delete()
        for email_data in emails:
            ProtagonistEmail.objects.create(protagonist=protagonist, **email_data)
            
    return protagonist

def delete_protagonist_service(protagonist_id: int) -> None:
    protagonist = get_protagonist_service(protagonist_id)
    protagonist.delete()
