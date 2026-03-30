from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from argument_manager.models import TrameNarrative
from pdf_manager.models import PDFDocument
from email_manager.models import Email
from document_manager.models import Document
from case_manager.models import LegalCase
from case_manager.services import rebuild_global_exhibits
from .services import global_semantic_search

def index(request):
    return render(request, 'core/index.html')

def semantic_search_view(request):
    """
    View to display and process global semantic search.
    """
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        results = global_semantic_search(query)
        
    return render(request, 'core/semantic_search.html', {
        'query': query,
        'results': results,
    })

def story_scrollytelling_view(request, pk):
    """
    Affiche une trame narrative sous forme d'histoire chronologique interactive.
    pk: L'ID de la Trame Narrative "L'Érosion des Motifs"
    """
    trame = get_object_or_404(TrameNarrative, pk=pk)
    timeline = trame.get_chronological_evidence()
    
    return render(request, 'core/story_scrollytelling.html', {
        'trame': trame,
        'timeline': timeline
    })

def story_cinematic_view(request, pk):
    """
    Processus parallèle : Vue "Expérience Cinématographique".
    Utilise les mêmes données que la vue standard, mais les injecte 
    dans le template d'animation GSAP.
    """
    trame = get_object_or_404(TrameNarrative, pk=pk)
    
    # On réutilise la logique de tri existante du modèle (Data Source of Truth)
    timeline = trame.get_chronological_evidence()
    source_documents = trame.get_source_documents()
    
    return render(request, 'core/story_cinematic.html', {
        'trame': trame,
        'timeline': timeline,
        'source_documents': source_documents
    })

def pdf_document_public_view(request, pk):
    pdf_document = get_object_or_404(PDFDocument, pk=pk)
    return redirect(pdf_document.file.url)

def email_public_view(request, pk):
    email = get_object_or_404(Email, pk=pk)
    
    raw_body = email.body_plain_text or ""
    body_lines = raw_body.splitlines()
    cleaned_lines = [line for line in body_lines if not line.strip().startswith('>')]
    cleaned_body = "\n".join(cleaned_lines)
    
    # Order quotes by creation date (ascending)
    quotes = email.quotes.all().order_by('created_at')
    
    return render(request, 'core/public_email.html', {
        'email': email,
        'cleaned_body': cleaned_body,
        'quotes': quotes
    })

def document_public_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    nodes = document.nodes.filter(depth__gt=1).prefetch_related('content_object').order_by('path')
    
    formatted_list = []
    counters = {2: 0, 3: 0, 4: 0}
    for node in nodes:
        depth = node.depth
        if depth == 2:
            counters[2] += 1
            counters[3] = 0
            counters[4] = 0
            node.numbering = f"{counters[2]}."
        elif depth == 3:
            counters[3] += 1
            counters[4] = 0
            node.numbering = f"{chr(96 + counters[3])}."
        elif depth == 4:
            counters[4] += 1
            roman_map = {1: 'i', 2: 'ii', 3: 'iii', 4: 'iv', 5: 'v'}
            node.numbering = f"{roman_map.get(counters[4], counters[4])}."
        else:
            node.numbering = ""
        node.indent_pixels = (depth - 2) * 40  # Adjust indent since we start from depth 2
        formatted_list.append(node)
        
    return render(request, 'core/public_document.html', {
        'document': document,
        'formatted_nodes': formatted_list
    })

class GenerateGlobalTimelineView(View):
    def get(self, request, *args, **kwargs):
        # 1. Find or Create the Master Case
        master_case, created = LegalCase.objects.get_or_create(
            title="MASTER ARCHIVE - ALL EVIDENCE"
        )
        
        # 2. Run the rebuild service
        try:
            count = rebuild_global_exhibits(master_case.pk)
            messages.success(request, f"Global Timeline updated! {count} items indexed.")
        except Exception as e:
            messages.error(request, f"Error generating timeline: {e}")

        # 3. Redirect to the STANDARD Case Detail view
        # This leverages your existing template, Word export, and Zip download!
        return redirect('case_manager:case_detail', pk=master_case.pk)
