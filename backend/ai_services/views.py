import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from .services import analyze_document_content
from pdf_manager.models import PDFDocument
from photos.models import PhotoDocument

@require_POST
def trigger_ai_analysis(request, doc_type, pk):
    """
    Triggers AI analysis on a document based on its type (PDF or Photo) and a specified persona.
    """
    model_map = {
        'pdf': PDFDocument,
        'photo': PhotoDocument,
    }
    model = model_map.get(doc_type)

    if not model:
        return JsonResponse({'status': 'error', 'message': 'Invalid document type'}, status=400)

    obj = get_object_or_404(model, pk=pk)

    try:
        data = json.loads(request.body)
        persona_key = data.get('persona', 'forensic_clerk')  # Default to 'forensic_clerk'
    except (json.JSONDecodeError, KeyError):
        # If JSON is malformed or 'persona' key is missing, use the default
        persona_key = 'forensic_clerk'

    # Pass the selected persona to the analysis service
    success = analyze_document_content(obj, persona_key=persona_key)

    if success:
        return JsonResponse({'status': 'success', 'analysis': obj.ai_analysis})
    else:
        # Provide a more specific error message if possible
        return JsonResponse({'status': 'error', 'message': 'Analysis failed in the backend service.'}, status=500)

@require_POST
def clear_ai_analysis(request, doc_type, pk):
    """
    Clears the AI analysis field for a given document.
    """
    model_map = {
        'pdf': PDFDocument,
        'photo': PhotoDocument,
    }
    model = model_map.get(doc_type)

    if not model:
        return JsonResponse({'status': 'error', 'message': 'Invalid document type'}, status=400)

    obj = get_object_or_404(model, pk=pk)
    obj.ai_analysis = ''
    obj.save()

    return JsonResponse({'status': 'success', 'message': 'Analysis cleared.'})
