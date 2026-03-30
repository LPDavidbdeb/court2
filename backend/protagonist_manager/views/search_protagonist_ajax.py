# --- AJAX Endpoint for Protagonist Search ---
from django.db.models import Q
from django.http import JsonResponse

from protagonist_manager.models import Protagonist


def search_protagonists_ajax(request):
    """
    AJAX endpoint to search for protagonists by name or email.
    Returns a JSON list of matching protagonists.
    """
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse([], safe=False)

    # Search by first name, last name, or associated email address
    protagonists = Protagonist.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(emails__email_address__icontains=query) # Search through related emails
    ).distinct() # Use distinct to avoid duplicate protagonists if they have multiple matching emails

    results = []
    for p in protagonists:
        emails = [e.email_address for e in p.emails.all()] # Get all emails for the protagonist
        results.append({
            'id': p.pk,
            'full_name': p.get_full_name(),
            'role': p.role,
            'emails': emails # Include all emails
        })
    return JsonResponse(results, safe=False)