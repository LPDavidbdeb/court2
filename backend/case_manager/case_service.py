from typing import List, Set
from django.shortcuts import get_object_or_404
from .models import LegalCase, ProducedExhibit
from .services import rebuild_produced_exhibits
from protagonist_manager.models import Protagonist

def get_case_protagonists(case_id: int) -> List[Protagonist]:
    """
    Collects all distinct protagonists associated with a case's produced exhibits.
    """
    case = get_object_or_404(LegalCase, pk=case_id)
    
    # Ensure exhibits are up to date
    if not case.produced_exhibits.exists():
        rebuild_produced_exhibits(case.pk)
    
    protagonists: Set[Protagonist] = set()
    
    # Iterate through all produced exhibits
    for exhibit in case.produced_exhibits.all():
        obj = exhibit.content_object
        if not obj:
            continue
            
        model_name = exhibit.content_type.model
        
        if model_name == 'email':
            if obj.sender_protagonist:
                protagonists.add(obj.sender_protagonist)
            for recipient in obj.recipient_protagonists.all():
                protagonists.add(recipient)
                
        elif model_name == 'pdfdocument':
            if obj.author:
                protagonists.add(obj.author)
                
        elif model_name == 'document':
            if obj.author:
                protagonists.add(obj.author)
                
        elif model_name == 'photodocument':
            if obj.author:
                protagonists.add(obj.author)
                
        elif model_name == 'chatsequence':
            # For chat sequences, we need to check the messages
            for msg in obj.messages.all():
                if msg.sender and msg.sender.protagonist:
                    protagonists.add(msg.sender.protagonist)
    
    # Convert set to list and sort by name
    return sorted(list(protagonists), key=lambda p: p.get_full_name())
