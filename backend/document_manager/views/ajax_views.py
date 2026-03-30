from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
import json
from ..models import Statement, LibraryNode, Document
from ai_services.services import analyze_document_content, correct_and_clarify_text, AI_PERSONAS
from pdf_manager.models import PDFDocument
from photos.models import PhotoDocument

@require_POST
def update_statement_flags(request):
    try:
        data = json.loads(request.body)
        statement_id = data.get('statement_id')
        field = data.get('field')
        value = data.get('value')

        if not all([statement_id, field, value is not None]):
            return JsonResponse({'status': 'error', 'message': 'Missing data.'}, status=400)

        if field not in ['is_true', 'is_falsifiable']:
            return JsonResponse({'status': 'error', 'message': 'Invalid field.'}, status=400)

        statement = Statement.objects.get(pk=statement_id)
        
        if field == 'is_true' and value is True:
            statement.is_falsifiable = False
        
        setattr(statement, field, value)
        statement.save()

        return JsonResponse({'status': 'success', 'message': 'Statement updated.'})

    except Statement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Statement not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def trigger_ai_analysis(request, doc_type, pk):
    if doc_type == 'pdf':
        obj = get_object_or_404(PDFDocument, pk=pk)
    elif doc_type == 'photo':
        obj = get_object_or_404(PhotoDocument, pk=pk)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid type'}, status=400)
    
    success = analyze_document_content(obj)
    
    if success:
        return JsonResponse({'status': 'success', 'analysis': obj.ai_analysis})
    else:
        return JsonResponse({'status': 'error', 'message': 'Analysis failed'}, status=500)

@require_POST
def ajax_correct_text_with_ai(request):
    try:
        data = json.loads(request.body)
        text_to_correct = data.get('text')
        document_id = data.get('document_id')
        custom_prompt = data.get('prompt') # Get the custom prompt from the request

        if not text_to_correct or not document_id:
            return JsonResponse({'status': 'error', 'message': 'Missing text or document_id.'}, status=400)

        document = get_object_or_404(Document, pk=document_id)
        
        # Simplified tree structure generation
        nodes = LibraryNode.objects.filter(document=document).order_by('path')
        tree_structure = []
        for node in nodes:
            tree_structure.append(f"{'  ' * (node.depth - 1)}- {node.item}")
        tree_structure_str = "\n".join(tree_structure)

        corrected_text = correct_and_clarify_text(text_to_correct, tree_structure_str, custom_prompt)

        return JsonResponse({'status': 'success', 'corrected_text': corrected_text})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def get_ai_persona_prompt(request):
    persona_key = 'media_editor' # Or make this dynamic if needed
    prompt = AI_PERSONAS.get(persona_key, {}).get('prompt', '')
    return JsonResponse({'status': 'success', 'prompt': prompt})
