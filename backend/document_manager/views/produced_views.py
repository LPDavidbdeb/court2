from django.db import transaction, models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.contenttypes.models import ContentType
from collections import defaultdict
import json
from datetime import date

from ..models import Document, Statement, LibraryNode, DocumentSource
from ..forms.manual_forms import ProducedDocumentForm, NodeForm, LibraryNodeCreateForm
from argument_manager.models import TrameNarrative
from pdf_manager.models import Quote as PDFQuote
from email_manager.models import Quote as EmailQuote
from events.models import Event
from photos.models import PhotoDocument

def _get_and_process_tree(document, add_numbering=False):
    """
    Fetches all nodes for a document, pre-fetches related content objects,
    builds a hierarchical structure safely in memory, and adds display properties.
    This is robust against orphaned nodes.
    """
    all_nodes = list(LibraryNode.objects.filter(document=document).select_related('content_type').order_by('path'))
    
    # --- 1. Efficiently prefetch all related content objects ---
    nodes_by_type = defaultdict(list)
    for node in all_nodes:
        if node.content_type:
            nodes_by_type[node.content_type.model].append(node)

    model_prefetch_map = {
        'statement': (Statement, []),
        'tramenarrative': (TrameNarrative, ['evenements', 'citations_courriel__email', 'citations_pdf__pdf_document', 'photo_documents', 'source_statements']),
        'quote': {
            'pdf_manager': (PDFQuote, ['pdf_document']),
            'email_manager': (EmailQuote, ['email']),
        },
        'event': (Event, []),
        'photodocument': (PhotoDocument, ['photos']),
    }

    content_objects_map = {}
    for model_name, nodes in nodes_by_type.items():
        object_ids = [node.object_id for node in nodes]
        
        if model_name == 'quote':
            nodes_by_app = defaultdict(list)
            for node in nodes:
                nodes_by_app[node.content_type.app_label].append(node)
            for app_label, app_nodes in nodes_by_app.items():
                app_object_ids = [node.object_id for node in app_nodes]
                Model, prefetches = model_prefetch_map[model_name][app_label]
                queryset = Model.objects.filter(pk__in=app_object_ids).prefetch_related(*prefetches)
                for obj in queryset:
                    content_objects_map[(ContentType.objects.get_for_model(Model).id, obj.id)] = obj
        elif model_name in model_prefetch_map:
            Model, prefetches = model_prefetch_map[model_name]
            queryset = Model.objects.filter(pk__in=object_ids).prefetch_related(*prefetches)
            for obj in queryset:
                content_objects_map[(ContentType.objects.get_for_model(Model).id, obj.id)] = obj

    # --- 2. Attach content and prepare for hierarchy building ---
    for node in all_nodes:
        node.content_object = content_objects_map.get((node.content_type_id, node.object_id))
        if node.content_object and node.content_type:
            app_label = node.content_type.app_label
            model = node.content_type.model
            node.content_template_name = f"document_manager/content_types/{app_label}_{model}" if model == 'quote' else f"document_manager/content_types/{model}"
        node.children_list = []

    # --- 3. Build the hierarchy safely using a path map (avoids DB queries) ---
    node_map = {node.path: node for node in all_nodes}
    root_nodes = []
    for node in all_nodes:
        if node.depth == 1:
            root_nodes.append(node)
        else:
            parent_path = node.path[:-LibraryNode.steplen]
            parent = node_map.get(parent_path)
            if parent:
                parent.children_list.append(node)

    # --- 4. Add formatting properties (indentation and numbering) ---
    def format_node_recursive(node, parent_numbering=''):
        node.indent_pixels = (node.depth - 1) * 40
        
        if node.depth > 1:
            sibling_index = 1
            parent = node.get_parent()
            if parent:
                # get_children() returns an ordered list of all children
                siblings = list(parent.get_children())
                try:
                    # Find the 1-based index of the current node in the list of its siblings
                    sibling_index = siblings.index(node) + 1
                except ValueError:
                    pass # Should not happen if the tree is consistent
            
            node.numbering = f"{parent_numbering}{sibling_index}."
        else:
            node.numbering = ""

        for i, child in enumerate(node.children_list):
            format_node_recursive(child, node.numbering)

    for root_node in root_nodes:
        format_node_recursive(root_node)
            
    return root_nodes

class ProducedDocumentListView(ListView):
    model = Document
    template_name = 'document_manager/produced/list.html'
    context_object_name = 'documents'
    def get_queryset(self):
        return Document.objects.filter(source_type=DocumentSource.PRODUCED).order_by('-created_at')

class ProducedDocumentCreateView(CreateView):
    model = Document
    form_class = ProducedDocumentForm
    template_name = 'document_manager/produced/form.html'
    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()
        root_statement = Statement.objects.create(text=f"Root node for {self.object.title}", is_user_created=True)
        LibraryNode.add_root(document=self.object, content_object=root_statement, item=self.object.title)
        return redirect('document_manager:produced_editor', pk=self.object.pk)

class ProducedDocumentEditorView(DetailView):
    model = Document
    template_name = 'document_manager/produced/editor.html'
    context_object_name = 'document'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nodes'] = _get_and_process_tree(self.object, add_numbering=True)
        context['modal_form'] = NodeForm()
        context['library_node_create_form'] = LibraryNodeCreateForm()
        return context

class ProducedDocumentCleanDetailView(DetailView):
    model = Document
    template_name = 'document_manager/produced/clean_detail_view.html'
    context_object_name = 'document'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formatted_nodes'] = _get_and_process_tree(self.object, add_numbering=True)
        try:
            root_node = LibraryNode.objects.get(document=self.object, depth=0)
            context['document'].text = root_node.content_object.text if root_node.content_object and hasattr(root_node.content_object, 'text') else ""
        except LibraryNode.DoesNotExist:
            context['document'].text = ""
        return context

# --- AJAX Views ---
@transaction.atomic
def ajax_add_node(request, node_pk):
    if request.method != 'POST': return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        parent_node = get_object_or_404(LibraryNode, pk=node_pk)
        form = NodeForm(request.POST)
        if form.is_valid():
            new_statement = Statement.objects.create(text=form.cleaned_data['text'], is_user_created=True)
            new_node = parent_node.add_child(document=parent_node.document, content_object=new_statement, item=form.cleaned_data['item'])
            return JsonResponse({'status': 'success', 'message': 'Node added successfully', 'new_node': {'id': new_node.id, 'item': new_node.item, 'text': new_statement.text}})
        else:
            return JsonResponse({'status': 'error', 'message': 'Form is invalid', 'errors': form.errors.as_json()}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@transaction.atomic
def ajax_edit_node(request, node_pk):
    node_to_edit = get_object_or_404(LibraryNode.objects.select_related('content_type'), pk=node_pk)
    if request.method == 'POST':
        form = NodeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            node_to_edit.item = data['item']
            node_to_edit.save()
            if node_to_edit.content_object and hasattr(node_to_edit.content_object, 'text'):
                node_to_edit.content_object.text = data['text']
                node_to_edit.content_object.save()
            else:
                new_statement = Statement.objects.create(text=data['text'], is_user_created=True)
                node_to_edit.content_object = new_statement
                node_to_edit.save()
            return JsonResponse({'status': 'success', 'message': 'Node updated.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Form is invalid', 'errors': form.errors.as_json()}, status=400)
    text_content = ''
    if node_to_edit.content_object and hasattr(node_to_edit.content_object, 'text'):
        text_content = node_to_edit.content_object.text
    return JsonResponse({'item': node_to_edit.item, 'text': text_content})

@transaction.atomic
def ajax_delete_node(request, node_pk):
    if request.method != 'POST': return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        node_to_delete = get_object_or_404(LibraryNode, pk=node_pk)
        
        content_objects_to_consider = {}
        for node in [node_to_delete] + list(node_to_delete.get_descendants()):
            if node.content_object:
                key = (node.content_type_id, node.object_id)
                if key not in content_objects_to_consider:
                    content_objects_to_consider[key] = node.content_object
        
        node_to_delete.delete()

        statement_content_type = ContentType.objects.get_for_model(Statement)
        for (ct_id, obj_id), content_obj in content_objects_to_consider.items():
            if ct_id == statement_content_type.id and isinstance(content_obj, Statement) and content_obj.is_user_created:
                if not LibraryNode.objects.filter(content_type=statement_content_type, object_id=content_obj.pk).exists():
                    content_obj.delete()
            
        return JsonResponse({'status': 'success', 'message': f"Node '{node_to_delete.item}' and its descendants deleted successfully."})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@transaction.atomic
def ajax_update_narrative_summary(request, narrative_pk):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        data = json.loads(request.body)
        new_resume = data.get('resume')

        if new_resume is None:
            return JsonResponse({'success': False, 'error': 'No summary content provided.'}, status=400)

        narrative.resume = new_resume
        narrative.save(update_fields=['resume'])
        
        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except TrameNarrative.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Narrative not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
