from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, UpdateView
from django.db.models import Prefetch, Q
from datetime import datetime, date
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib import messages
from collections import defaultdict

from ..models import Document, LibraryNode, Statement
from ..forms import DocumentForm
from argument_manager.models import TrameNarrative
from case_manager.models import PerjuryContestation, ExhibitRegistry
from email_manager.models import Quote as EmailQuote, Email
from pdf_manager.models import Quote as PDFQuote, PDFDocument
from events.models import Event
from photos.models import PhotoDocument, Photo
from protagonist_manager.models import Protagonist

User = get_user_model()


def _format_nodes_for_new_display(nodes):
    formatted_list = []
    counters = {2: 0, 3: 0, 4: 0}
    for node in nodes:
        depth = node.depth
        if depth == 2:
            counters[2] += 1;
            counters[3] = 0;
            counters[4] = 0
            node.numbering = f"{counters[2]}."
        elif depth == 3:
            counters[3] += 1;
            counters[4] = 0
            node.numbering = f"{chr(96 + counters[3])}."
        elif depth == 4:
            counters[4] += 1
            roman_map = {1: 'i', 2: 'ii', 3: 'iii', 4: 'iv', 5: 'v'}
            node.numbering = f"{roman_map.get(counters[4], counters[4])}."
        else:
            node.numbering = ""
        node.indent_pixels = (depth - 1) * 40
        formatted_list.append(node)
    return formatted_list


def new_document_list_view(request):
    documents = Document.objects.all().order_by('-created_at')
    return render(request, 'document_manager/new_document_list.html', {'documents': documents})


def new_document_detail_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    nodes = document.nodes.all().prefetch_related('content_object').order_by('path')
    for node in nodes:
        node.indent_pixels = (node.depth - 1) * 40
    context = {'document': document, 'nodes': nodes}
    return render(request, 'document_manager/new_document_detail.html', context)


def new_clean_detail_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    descendants = document.nodes.filter(depth__gt=1).prefetch_related('content_object').order_by('path')
    formatted_nodes = _format_nodes_for_new_display(descendants)
    context = {'document': document, 'formatted_nodes': formatted_nodes}
    return render(request, 'document_manager/new_clean_detail.html', context)


def new_interactive_detail_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    descendants = document.nodes.all().prefetch_related('content_object').order_by('path')
    formatted_nodes = _format_nodes_for_new_display(descendants)
    
    context = {
        'document': document, 
        'formatted_nodes': formatted_nodes,
    }
    return render(request, 'document_manager/new_interactive_detail.html', context)


def reproduced_cinematic_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    # 1. Fetch Basic Nodes for Phase 1 (Reading) & Phase 2 (List)
    nodes = document.nodes.filter(depth__gt=1).prefetch_related('content_object').order_by('path')
    formatted_nodes = _format_nodes_for_new_display(nodes)
    
    # 2. PHASE 3: CONTESTATION-BASED CONFRONTATION
    
    # A. Identify Statements belonging to this document
    statement_ct = ContentType.objects.get_for_model(Statement)
    doc_statement_ids = list(LibraryNode.objects.filter(
        document=document,
        content_type=statement_ct
    ).values_list('object_id', flat=True))

    # B. Find Contestations that target THESE statements
    relevant_contestations = PerjuryContestation.objects.filter(
        targeted_statements__id__in=doc_statement_ids
    ).prefetch_related(
        'targeted_statements',
        'supporting_narratives',
        'case__exhibits'
    ).distinct()

    confrontation_blocks = []

    for contestation in relevant_contestations:
        # --- 1. PREPARE EXHIBIT LOOKUP ---
        exhibit_map = {}
        for ex in contestation.case.exhibits.all():
            exhibit_map[(ex.content_type_id, ex.object_id)] = ex.get_label()

        # --- 2. LEFT PANE: TARGETED STATEMENTS ---
        target_stmts = contestation.targeted_statements.filter(
            id__in=doc_statement_ids
        ).order_by('id')
        
        display_statements = []
        for stmt in target_stmts:
            node_match = next((n for n in formatted_nodes if n.object_id == stmt.id), None)
            display_statements.append({
                'text': stmt.text,
                'numbering': node_match.numbering if node_match else ""
            })

        # --- 3. RIGHT PANE: EVIDENCE WITH P-NUMBERS ---
        combined_evidence = []
        for narrative in contestation.supporting_narratives.all():
            evidence_list = narrative.get_chronological_evidence()
            
            for item in evidence_list:
                obj = item['object']
                
                lookup_key = None
                
                if hasattr(obj, 'email'):
                    lookup_key = (ContentType.objects.get_for_model(obj.email).id, obj.email.id)
                elif hasattr(obj, 'pdf_document'):
                    lookup_key = (ContentType.objects.get_for_model(obj.pdf_document).id, obj.pdf_document.id)
                elif hasattr(obj, 'id'):
                    lookup_key = (ContentType.objects.get_for_model(obj).id, obj.id)
                
                label = exhibit_map.get(lookup_key)
                item['exhibit_label'] = label

            combined_evidence.extend(evidence_list)
        
        combined_evidence.sort(key=lambda x: x['date'] or timezone.now())

        confrontation_blocks.append({
            'title': contestation.title,
            'statements': display_statements,
            'evidence': combined_evidence,
            'narrative_count': contestation.supporting_narratives.count(),
            'case_title': contestation.case.title
        })

    context = {
        'document': document, 
        'nodes': formatted_nodes,
        'confrontation_blocks': confrontation_blocks,
        'mode': 'cinematic',
    }
    
    return render(request, 'document_manager/story_cinematic.html', context)


class DocumentUpdateView(UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'document_manager/document_form.html'

    def get_success_url(self):
        messages.success(self.request, "Document updated successfully.")
        return reverse_lazy('document_manager:document_detail', kwargs={'pk': self.object.pk})

def author_search_view(request):
    term = request.GET.get('term', '')
    protagonists = Protagonist.objects.filter(
        Q(first_name__icontains=term) | Q(last_name__icontains=term)
    )[:10]
    results = [{'id': p.id, 'text': p.get_full_name()} for p in protagonists]
    return JsonResponse(results, safe=False)


class NewPerjuryElementListView(ListView):
    model = Statement
    template_name = 'document_manager/new_perjury_element_list.html'
    context_object_name = 'data_by_document'

    def get_queryset(self):
        return Statement.objects.filter(is_true=False, is_falsifiable=True)

    def _get_paragraph_numbering_map(self, document):
        nodes = document.nodes.all().order_by('path')
        numbering_map = {}
        counters = {2: 0, 3: 0, 4: 0}
        for node in nodes:
            depth = node.depth
            numbering = ""
            if depth == 2:
                counters[2] += 1;
                counters[3] = 0;
                counters[4] = 0
                numbering = f"{counters[2]}."
            elif depth == 3:
                counters[3] += 1;
                counters[4] = 0
                numbering = f"{chr(96 + counters[3])}."
            elif depth == 4:
                counters[4] += 1
                roman_map = {1: 'i', 2: 'ii', 3: 'iii', 4: 'iv', 5: 'v'}
                numbering = f"{roman_map.get(counters[4], counters[4])}."
            if numbering:
                numbering_map[node.pk] = numbering.rstrip('.')
        return numbering_map

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        statement_content_type = ContentType.objects.get_for_model(Statement)

        perjury_statements = self.object_list
        perjury_statement_ids = [s.id for s in perjury_statements]

        data_by_document = []
        
        document_ids = LibraryNode.objects.filter(
            content_type=statement_content_type,
            object_id__in=perjury_statement_ids
        ).values_list('document_id', flat=True).distinct()
        
        main_documents = Document.objects.filter(id__in=document_ids).order_by('id')

        doc_counter = 0
        for doc in main_documents:
            nodes_in_doc = LibraryNode.objects.filter(
                document=doc,
                content_type=statement_content_type,
                object_id__in=perjury_statement_ids
            ).prefetch_related('content_object').order_by('path')

            if not nodes_in_doc:
                continue

            doc_counter += 1
            doc_id = f"C-{doc_counter}"
            paragraph_number_map = self._get_paragraph_numbering_map(doc)
            doc_data = {'document': doc, 'doc_id': doc_id, 'claims': []}
            for claim_node in nodes_in_doc:
                para_num = paragraph_number_map.get(claim_node.pk)
                claim_id = f"{doc_id}-{para_num}" if para_num else doc_id
                node_data = {'node': claim_node, 'claim_id': claim_id}
                doc_data['claims'].append(node_data)
            data_by_document.append(doc_data)

        context.update({
            'data_by_document': data_by_document,
        })
        return context
