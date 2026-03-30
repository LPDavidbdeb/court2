from django import template
from datetime import date, datetime
from django.utils import timezone

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Allows accessing a dictionary item by a key that is a variable.
    Especially useful when the key is an object in a loop.
    """
    return dictionary.get(key)

@register.filter(name='model_name')
def get_model_name(value):
    """Returns the name of the model for a given object."""
    if hasattr(value, '__class__'):
        return value.__class__.__name__
    return ''

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the given value by the argument."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''

@register.inclusion_tag('document_manager/partials/_narrative_evidence_list.html')
def display_narrative_evidence(narrative):
    """
    An inclusion tag to display a chronologically sorted list of evidence 
    for a given TrameNarrative object.
    """
    flat_evidence_list = []
    if narrative:
        flat_evidence_list.extend(list(narrative.evenements.all()))
        flat_evidence_list.extend(list(narrative.citations_courriel.all()))
        flat_evidence_list.extend(list(narrative.citations_pdf.all()))
        flat_evidence_list.extend(list(narrative.photo_documents.all()))
        flat_evidence_list.extend(list(narrative.source_statements.all())) # NEW

    def get_evidence_datetime(evidence):
        """
        Returns a full, timezone-aware datetime object for sorting.
        """
        model_name = get_model_name(evidence)
        
        try:
            if model_name == 'Event' and evidence.date:
                naive_dt = datetime.combine(evidence.date, datetime.min.time())
                return timezone.make_aware(naive_dt)

            if model_name == 'Quote':
                if hasattr(evidence, 'email') and evidence.email and evidence.email.date_sent:
                    return evidence.email.date_sent
                
                if hasattr(evidence, 'pdf_document') and evidence.pdf_document:
                    if evidence.pdf_document.document_date:
                        naive_dt = datetime.combine(evidence.pdf_document.document_date, datetime.min.time())
                        return timezone.make_aware(naive_dt)
                    if evidence.pdf_document.uploaded_at:
                        return evidence.pdf_document.uploaded_at

            if model_name == 'PhotoDocument' and evidence.created_at:
                return evidence.created_at
            
            # NEW: Handle Statement
            if model_name == 'Statement' and evidence.created_at:
                return evidence.created_at

        except (AttributeError, TypeError):
            pass
            
        return timezone.make_aware(datetime(9999, 12, 31))

    flat_evidence_list.sort(key=get_evidence_datetime)

    return {
        'evidence_list': flat_evidence_list,
        'narrative': narrative
    }
