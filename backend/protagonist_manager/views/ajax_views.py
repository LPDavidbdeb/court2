from django.http import JsonResponse
from django.db.models import Q, Prefetch
from django.views.decorators.http import require_POST
import json

from ..models import Protagonist, ProtagonistEmail

def search_protagonists_ajax(request):
    """
    An AJAX view that searches for protagonists based on a query term.
    """
    term = request.GET.get('q', '')
    
    protagonists = Protagonist.objects.prefetch_related(
        Prefetch('emails', queryset=ProtagonistEmail.objects.all())
    ).filter(
        Q(first_name__icontains=term) | 
        Q(last_name__icontains=term) |
        Q(emails__email_address__icontains=term)
    ).distinct()[:15]

    results = []
    for protagonist in protagonists:
        results.append({
            'id': protagonist.id,
            'full_name': protagonist.get_full_name(),
            'role': protagonist.role,
            'emails': [email.email_address for email in protagonist.emails.all()]
        })
    
    return JsonResponse(results, safe=False)

@require_POST
def update_protagonist_role_ajax(request):
    """
    An AJAX view to update the role of a protagonist.
    """
    try:
        data = json.loads(request.body)
        protagonist_id = data.get('protagonist_id')
        new_role = data.get('role')

        if protagonist_id is None or new_role is None:
            return JsonResponse({'status': 'error', 'message': 'Missing data.'}, status=400)

        protagonist = Protagonist.objects.get(pk=protagonist_id)
        protagonist.role = new_role
        protagonist.save(update_fields=['role'])

        return JsonResponse({'status': 'success', 'message': 'Role updated successfully.'})

    except Protagonist.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Protagonist not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
def update_protagonist_linkedin_ajax(request):
    """
    An AJAX view to update the LinkedIn URL of a protagonist.
    """
    try:
        data = json.loads(request.body)
        protagonist_id = data.get('protagonist_id')
        new_linkedin_url = data.get('linkedin_url')

        if protagonist_id is None:
            return JsonResponse({'status': 'error', 'message': 'Missing data.'}, status=400)

        protagonist = Protagonist.objects.get(pk=protagonist_id)
        protagonist.linkedin_url = new_linkedin_url
        protagonist.save(update_fields=['linkedin_url'])

        return JsonResponse({'status': 'success', 'message': 'LinkedIn URL updated successfully.'})

    except Protagonist.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Protagonist not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
