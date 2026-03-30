import os
import json
from collections import OrderedDict
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import PDFDocument, PDFDocumentType, Quote
from .forms import PDFDocumentForm, QuoteForm
from protagonist_manager.models import Protagonist
from protagonist_manager.forms import ProtagonistForm

# ==============================================================================
# List and Create Views
# ==============================================================================

def pdf_document_list(request):
    """
    Displays a list of all uploaded PDF documents, grouped by type into tabs,
    with a final tab showing all documents.
    """
    doc_types = PDFDocumentType.objects.all()
    all_documents = PDFDocument.objects.order_by('-document_date')
    
    grouped_documents = OrderedDict()

    for doc_type in doc_types:
        grouped_documents[doc_type.name] = all_documents.filter(document_type=doc_type)

    grouped_documents['All'] = all_documents

    context = {
        'grouped_documents': grouped_documents,
    }
    return render(request, 'pdf_manager/pdf_list.html', context)

def upload_pdf_document(request):
    """
    Handles the upload of a new PDF document.
    """
    if request.method == 'POST':
        form = PDFDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"PDF document '{form.cleaned_data['title']}' uploaded successfully.")
            return redirect('pdf_manager:pdf_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PDFDocumentForm()
    
    protagonist_form = ProtagonistForm()
    return render(request, 'pdf_manager/upload_pdf.html', {'form': form, 'protagonist_form': protagonist_form})

# ==============================================================================
# Detail, Update, and Delete Views
# ==============================================================================

class PDFDocumentDetailView(DetailView):
    """
    Displays the details of a single PDF document.
    """
    model = PDFDocument
    template_name = 'pdf_manager/pdf_detail.html'
    context_object_name = 'document'

class PDFDocumentUpdateView(UpdateView):
    """
    Allows editing the details of a PDF document.
    """
    model = PDFDocument
    form_class = PDFDocumentForm
    template_name = 'pdf_manager/pdf_form.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protagonist_form'] = ProtagonistForm()
        return context

    def get_success_url(self):
        messages.success(self.request, "PDF document details updated successfully.")
        return reverse_lazy('pdf_manager:pdf_detail', kwargs={'pk': self.object.pk})

class PDFDocumentDeleteView(DeleteView):
    """
    Handles the deletion of a PDF document and its associated file.
    """
    model = PDFDocument
    template_name = 'pdf_manager/pdf_confirm_delete.html'
    context_object_name = 'document'
    success_url = reverse_lazy('pdf_manager:pdf_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.file and os.path.isfile(self.object.file.path):
            os.remove(self.object.file.path)
        messages.success(request, f"PDF document '{self.object.title}' deleted successfully.")
        return super().post(request, *args, **kwargs)

def create_pdf_quote(request, pk):
    document = get_object_or_404(PDFDocument, pk=pk)
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.pdf_document = document
            quote.save()
            messages.success(request, "Quote created successfully.")
            return redirect('pdf_manager:pdf_detail', pk=document.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    return redirect('pdf_manager:pdf_detail', pk=document.pk)

class QuoteDetailView(DetailView):
    """
    Displays the details of a single PDF quote.
    """
    model = Quote
    template_name = 'pdf_manager/quote_detail.html'
    context_object_name = 'quote'

# ==============================================================================
# AJAX Views
# ==============================================================================

@require_POST
def ajax_update_pdf_quote(request, pk):
    try:
        quote = get_object_or_404(Quote, pk=pk)
        data = json.loads(request.body)
        new_text = data.get('quote_text', '')

        quote.quote_text = new_text
        quote.save(update_fields=['quote_text'])

        return JsonResponse({
            'success': True,
            'quote_text': quote.quote_text
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def ajax_get_pdf_metadata(request, doc_pk):
    document = get_object_or_404(PDFDocument, pk=doc_pk)
    data = {
        'title': document.title,
        'author_name': document.author.get_full_name() if document.author else None,
        'document_date': document.document_date.strftime('%Y-%m-%d') if document.document_date else None,
    }
    return JsonResponse(data)

def author_search_view(request):
    term = request.GET.get('term', '')
    protagonists = Protagonist.objects.filter(
        Q(first_name__icontains=term) | Q(last_name__icontains=term)
    )[:10]  # Limit results
    results = [
        {
            'id': p.id,
            'text': p.get_full_name()
        }
        for p in protagonists
    ]
    return JsonResponse(results, safe=False)

def add_protagonist_view(request):
    if request.method == 'POST':
        form = ProtagonistForm(request.POST)
        if form.is_valid():
            protagonist = form.save()
            return JsonResponse({'success': True, 'id': protagonist.id, 'name': protagonist.get_full_name()})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'errors': 'Invalid request'})
