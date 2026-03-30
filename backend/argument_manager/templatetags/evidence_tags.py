from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

register = template.Library()

@register.simple_tag
def get_evidence_type(evidence_object):
    """
    Returns a string identifier for the specific evidence type.
    This is more robust than just using __class__.__name__ when dealing with proxy or inherited models.
    """
    if hasattr(evidence_object, 'email') and evidence_object.email:
        return 'EmailQuote'
    if hasattr(evidence_object, 'pdf') and evidence_object.pdf:
        return 'PDFQuote'
    # Fallback to the class name for other types like Event and PhotoDocument
    return evidence_object.__class__.__name__

@register.simple_tag(takes_context=True)
def get_evidence_source_url(context, evidence_object):
    """
    Generates a URL to the source of a piece of evidence (if applicable),
    with a 'next' parameter to return to the current page.
    Returns an empty string if no source URL is applicable.
    """
    request = context['request']
    url = None

    try:
        evidence_type = get_evidence_type(evidence_object)
        if evidence_type == 'EmailQuote':
            url = reverse('email_manager:email_detail', kwargs={'pk': evidence_object.email.pk})
        elif evidence_type == 'PDFQuote':
            url = reverse('pdf_manager:pdf_detail', kwargs={'pk': evidence_object.pdf.pk})
        elif evidence_type == 'PhotoDocument':
            url = reverse('photos:photo_detail', kwargs={'pk': evidence_object.pk})

        if url:
            next_url = request.get_full_path()
            if '?' in url:
                return f"{url}&{urlencode({'next': next_url})}"
            else:
                return f"{url}?{urlencode({'next': next_url})}"
        
        return ""  # Return empty string if no URL

    except Exception:
        return ""  # Fail silently


@register.simple_tag
def remove_evidence_button(evidence_object):
    """
    Generates a standardized "remove" button for any piece of evidence,
    styled to look like a Bootstrap badge pill.
    """
    evidence_type = get_evidence_type(evidence_object) # Use the robust type checker here too
    evidence_id = evidence_object.pk

    button_html = f'''
        <a href="#" class="badge bg-danger rounded-pill text-decoration-none remove-evidence-btn"
           role="button"
           data-evidence-id="{evidence_id}"
           data-evidence-type="{evidence_type}">
            <i class="fas fa-trash"></i> Remove
        </a>
    '''
    return format_html(button_html)
