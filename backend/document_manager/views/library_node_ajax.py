from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
import logging

from ..models import LibraryNode, Document, Statement
from ..forms.manual_forms import LibraryNodeCreateForm

# Models from other apps to be searched
from argument_manager.models import TrameNarrative
from email_manager.models import Quote as EmailQuote
from pdf_manager.models import Quote as PDFQuote
from events.models import Event
from photos.models import PhotoDocument

logger = logging.getLogger(__name__)

@require_GET
def search_evidence_ajax(request):
    """
    Performs a federated search across multiple models for a given query.
    Returns results in a standardized JSON format for the 'Link Existing Evidence' modal.
    """
    query = request.GET.get('query', '').strip()
    results = []
    
    logger.info(f"Starting evidence search for query: '{query}'")

    RESULT_LIMIT = 10

    if not query or len(query) < 2:
        logger.warning("Query too short, returning empty results.")
        return JsonResponse({'results': []})

    content_types = {
        'Statement': ContentType.objects.get_for_model(Statement),
        'TrameNarrative': ContentType.objects.get_for_model(TrameNarrative),
        'EmailQuote': ContentType.objects.get_for_model(EmailQuote),
        'PDFQuote': ContentType.objects.get_for_model(PDFQuote),
        'Event': ContentType.objects.get_for_model(Event),
        'PhotoDocument': ContentType.objects.get_for_model(PhotoDocument),
    }

    try:
        reproduced_statements = Statement.objects.filter(is_user_created=False, text__icontains=query)[:RESULT_LIMIT]
        for item in reproduced_statements:
            results.append({
                'content_type_id': content_types['Statement'].id, 'object_id': item.id,
                'preview_text': f"'{item.text[:80]}...'", 'object_type': 'Reproduced Text'
            })
    except Exception as e:
        logger.error(f"Error searching Statements: {e}")

    try:
        trames = TrameNarrative.objects.filter(Q(titre__icontains=query) | Q(resume__icontains=query))[:RESULT_LIMIT]
        for item in trames:
            results.append({
                'content_type_id': content_types['TrameNarrative'].id, 'object_id': item.id,
                'preview_text': f"{item.titre}: {item.resume[:60]}...", 'object_type': 'Narrative'
            })
    except Exception as e:
        logger.error(f"Error searching TrameNarratives: {e}")

    try:
        email_quotes = EmailQuote.objects.filter(quote_text__icontains=query).select_related('email')[:RESULT_LIMIT]
        for item in email_quotes:
            results.append({
                'content_type_id': content_types['EmailQuote'].id, 'object_id': item.id,
                'preview_text': f"Email from '{item.email.subject}': '{item.quote_text[:60]}...'", 'object_type': 'Email Quote'
            })
    except Exception as e:
        logger.error(f"Error searching EmailQuotes: {e}")

    try:
        pdf_quotes = PDFQuote.objects.filter(quote_text__icontains=query).select_related('pdf_document')[:RESULT_LIMIT]
        for item in pdf_quotes:
            results.append({
                'content_type_id': content_types['PDFQuote'].id, 'object_id': item.id,
                'preview_text': f"PDF '{item.pdf_document.title}': '{item.quote_text[:60]}...'", 'object_type': 'PDF Quote'
            })
    except Exception as e:
        logger.error(f"Error searching PDFQuotes: {e}")

    try:
        events = Event.objects.filter(explanation__icontains=query)[:RESULT_LIMIT]
        for item in events:
            results.append({
                'content_type_id': content_types['Event'].id, 'object_id': item.id,
                'preview_text': f"Event on {item.date.strftime('%Y-%m-%d')}: {item.explanation[:60]}...", 'object_type': 'Event'
            })
    except Exception as e:
        logger.error(f"Error searching Events: {e}")
        
    try:
        photo_documents = PhotoDocument.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))[:RESULT_LIMIT]
        for item in photo_documents:
            results.append({
                'content_type_id': content_types['PhotoDocument'].id, 'object_id': item.id,
                'preview_text': f"Photo Doc: '{item.title}'", 'object_type': 'Photo Document'
            })
    except Exception as e:
        logger.error(f"Error searching PhotoDocuments: {e}")

    return JsonResponse({'results': results})


@require_POST
@transaction.atomic
def add_library_node_ajax(request, document_pk):
    document = get_object_or_404(Document, pk=document_pk)
    form = LibraryNodeCreateForm(request.POST)

    if not form.is_valid():
        errors = form.errors.as_json()
        logger.error(f"Form validation failed: {errors}")
        return JsonResponse({'status': 'error', 'message': 'Form validation failed.', 'errors': errors}, status=400)

    try:
        new_node_instance = form.save(commit=False)
        new_node_instance.document = document

        content_type_id = request.POST.get('content_type_id')
        object_id = request.POST.get('object_id')
        text = form.cleaned_data.get('text')

        if content_type_id and object_id and content_type_id.strip() and object_id.strip():
            try:
                ct_id = int(content_type_id)
                obj_id = int(object_id)
                content_type = get_object_or_404(ContentType, pk=ct_id)
                content_type.get_object_for_this_type(pk=obj_id)
                new_node_instance.content_type_id = ct_id
                new_node_instance.object_id = obj_id
            except (ValueError, TypeError):
                return JsonResponse({'status': 'error', 'message': 'Invalid ID provided for linking.'}, status=400)
            except ContentType.DoesNotExist:
                 return JsonResponse({'status': 'error', 'message': 'Invalid content type for linking.'}, status=400)
            except Exception:
                 return JsonResponse({'status': 'error', 'message': 'Could not find the specified evidence to link.'}, status=404)
        elif text and text.strip():
            statement = Statement.objects.create(text=text.strip(), is_user_created=True)
            new_node_instance.content_object = statement
        
        action_type = request.POST.get('action_type')
        reference_node_pk = request.POST.get('reference_node_pk')
        message = ""

        # If no reference node is provided, it MUST be a root node action.
        if not reference_node_pk:
            action_type = 'add_root'

        if action_type == 'add_root':
            LibraryNode.add_root(instance=new_node_instance)
            message = f"Root node '{new_node_instance.item}' created successfully."
        else:
            reference_node = get_object_or_404(LibraryNode, pk=reference_node_pk, document=document)

            if reference_node.is_root() and action_type in ['add_sibling_left', 'add_sibling_right', 'add_parent']:
                return JsonResponse({'status': 'error', 'message': f"Cannot '{action_type.replace('_', ' ')}' relative to a root node."}, status=400)

            if action_type == 'add_child':
                reference_node.add_child(instance=new_node_instance)
                message = f"Child node '{new_node_instance.item}' added to '{reference_node.item}'."
            elif action_type == 'add_sibling_left':
                reference_node.add_sibling(instance=new_node_instance, pos='left')
                message = f"Sibling node '{new_node_instance.item}' added to the left of '{reference_node.item}'."
            elif action_type == 'add_sibling_right':
                reference_node.add_sibling(instance=new_node_instance, pos='right')
                message = f"Sibling node '{new_node_instance.item}' added to the right of '{reference_node.item}'."
            elif action_type == 'add_parent':
                original_parent = reference_node.get_parent()
                new_parent_node = original_parent.add_child(instance=new_node_instance)
                reference_node.move(new_parent_node, pos='last-child')
                message = f"Node '{new_parent_node.item}' created as parent of '{reference_node.item}'."
            else:
                return JsonResponse({'status': 'error', 'message': f"Invalid action type specified: '{action_type}'."}, status=400)
        
        return JsonResponse({'status': 'success', 'message': message, 'node_id': new_node_instance.pk})

    except Exception as e:
        logger.error(f"Error in add_library_node_ajax: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
