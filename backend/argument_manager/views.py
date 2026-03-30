from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from django.urls import reverse_lazy, reverse
from .models import TrameNarrative, PerjuryArgument
from .forms import TrameNarrativeForm, PerjuryArgumentForm
from document_manager.models import LibraryNode, Statement, Document, DocumentSource
from django.contrib.contenttypes.models import ContentType
from ai_services.services import analyze_for_json_output, run_narrative_audit_service
from django.utils import timezone
from django.utils.html import escape
from django.contrib import messages

import json
import time
from itertools import groupby
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q, Prefetch
from email_manager.models import Email, EmailThread, Quote as EmailQuote
from events.models import Event
from pdf_manager.models import PDFDocument, Quote as PDFQuote
from photos.models import PhotoDocument
from googlechat_manager.models import ChatSequence


def grouped_narrative_view(request):
    narratives = TrameNarrative.objects.prefetch_related('targeted_statements').order_by('titre')
    grouped_narratives = defaultdict(list)

    for narrative in narratives:
        statement_pks = tuple(sorted(s.pk for s in narrative.targeted_statements.all()))
        grouped_narratives[statement_pks].append(narrative)

    context_groups = []
    for pks, narrative_list in grouped_narratives.items():
        if pks:
            statements = narrative_list[0].targeted_statements.all()
            context_groups.append({
                'statements': statements,
                'narratives': narrative_list
            })

    return render(request, 'argument_manager/grouped_narrative_list.html', {'grouped_narratives': context_groups})


def manage_perjury_argument(request, narrative_pk):
    narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
    argument, created = PerjuryArgument.objects.get_or_create(trame=narrative)
    return redirect('argument_manager:perjury_update', pk=argument.pk)

class PerjuryArgumentUpdateView(UpdateView):
    model = PerjuryArgument
    form_class = PerjuryArgumentForm
    template_name = 'argument_manager/perjury_argument_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(self, **kwargs)
        context['narrative'] = self.object.trame
        narrative = self.object.trame
        narrative_data = {
            'events': [{'title': f'{e.date.strftime("%Y-%m-%d")}: {e.explanation[:50]}...', 'text': e.explanation, 'url': reverse('events:detail', args=[e.pk])} for e in narrative.evenements.all()],
            'emailQuotes': [{'title': f'{q.quote_text[:50]}...', 'text': q.quote_text, 'url': reverse('email_manager:thread_detail', args=[q.email.thread.pk])} for q in narrative.citations_courriel.select_related('email__thread').all()],
            'pdfQuotes': [{'title': f'{q.quote_text[:50]}...', 'text': q.quote_text, 'url': reverse('pdf_manager:pdf_detail', args=[q.pdf_document.pk])} for q in narrative.citations_pdf.select_related('pdf_document').all()],
            'chatSequences': [{'title': f'{s.title[:50]}...', 'text': s.title, 'url': reverse('googlechat:sequence_detail', args=[s.pk])} for s in narrative.citations_chat.all()]
        }
        context['narrative_data_json'] = json.dumps(narrative_data)
        return context

    def get_success_url(self):
        return reverse('argument_manager:detail', kwargs={'pk': self.object.trame.pk})


@require_POST
def ajax_generate_argument_text(request, narrative_pk):
    narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
    data = json.loads(request.body)
    section = data.get('section')
    
    # Build a text block of all available evidence
    evidence_text = ""
    for e in narrative.evenements.all():
        evidence_text += f"Event on {e.date.strftime('%Y-%m-%d')}: {e.explanation}\n\n"
    for q in narrative.citations_courriel.all():
        evidence_text += f"Email Quote from {q.email.date.strftime('%Y-%m-%d')}: '{q.quote_text}'\n\n"
    for q in narrative.citations_pdf.all():
        evidence_text += f"PDF Quote from '{q.pdf_document.title}' (p. {q.page_number}): '{q.quote_text}'\n\n"
    for s in narrative.citations_chat.all():
        evidence_text += f"Chat Sequence '{s.title}' from {s.start_date.strftime('%Y-%m-%d')}:\n"
        for msg in s.messages.all():
            evidence_text += f"  - {msg.sender.name}: {msg.text_content}\n"
        evidence_text += "\n"

    # Build the prompt based on the narrative's goal
    system_prompt = "You are a legal assistant writing a clear, concise, and persuasive argument. Use only the evidence provided."
    
    if narrative.type_argument == 'CONTRADICTION':
        if section == 'proof':
            user_prompt = f"Here is a statement made under oath: '{narrative.targeted_statements.first().text}'. Here is the evidence: \n\n{evidence_text}\n\nDraft a paragraph for the 'Proof of Falsity' section explaining how the evidence proves the statement is false."
        elif section == 'mens_rea':
            user_prompt = f"Here is a statement made under oath: '{narrative.targeted_statements.first().text}'. Here is the evidence: \n\n{evidence_text}\n\nDraft a paragraph for the 'Knowledge of Falsity (Mens Rea)' section, explaining how the evidence shows the person KNEW their statement was false when they made it."
        else: # intent
            user_prompt = f"Here is a false statement made under oath: '{narrative.targeted_statements.first().text}'. Based on the context, what was the likely goal or strategic advantage this person hoped to gain by making this false statement? Draft a paragraph for the 'Intent to Deceive' section."
    
    else: # SUPPORT
        user_prompt = f"Here is a statement: '{narrative.targeted_statements.first().text}'. Here is the evidence: \n\n{evidence_text}\n\nDraft a paragraph that uses the evidence to support and confirm that the statement is true and credible."

    try:
        response_text = analyze_for_json_output([system_prompt, user_prompt])
        return JsonResponse({'success': True, 'text': response_text})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def ajax_remove_allegation(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        data = json.loads(request.body)
        allegation_id = data.get('allegation_id')
        if not allegation_id:
            return JsonResponse({'success': False, 'error': 'Allegation ID is required.'}, status=400)
        allegation = get_object_or_404(Statement, pk=allegation_id)
        narrative.targeted_statements.remove(allegation)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def ajax_remove_evidence(request, narrative_pk):
    EVIDENCE_MODELS = {
        'Quote': (PDFQuote, 'citations_pdf'),
        'PDFDocument': (PDFQuote, 'citations_pdf'),
        'EmailQuote': (EmailQuote, 'citations_courriel'),
        'Event': (Event, 'evenements'),
        'PhotoDocument': (PhotoDocument, 'photo_documents'),
        'Statement': (Statement, 'source_statements'),
        'ChatSequence': (ChatSequence, 'citations_chat'),
    }
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        data = json.loads(request.body)
        evidence_type = data.get('evidence_type')
        evidence_id = data.get('evidence_id')
        
        if not evidence_type or not evidence_id:
            return JsonResponse({'success': False, 'error': 'Evidence type and ID are required.'}, status=400)
        
        model_info = EVIDENCE_MODELS.get(evidence_type)
        if not model_info:
            return JsonResponse({'success': False, 'error': f'Invalid evidence type: {evidence_type}'}, status=400)
        
        model_class, relationship_name = model_info
        evidence_to_remove = get_object_or_404(model_class, pk=evidence_id)
        relationship_manager = getattr(narrative, relationship_name)
        relationship_manager.remove(evidence_to_remove)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def pdf_quote_list_for_tinymce(request):
    quotes = PDFQuote.objects.select_related('pdf_document').order_by('pdf_document__title', 'page_number')
    formatted_quotes = []
    for quote in quotes:
        if quote.pdf_document:
            title = f"{quote.pdf_document.title} (p. {quote.page_number}) - {quote.quote_text[:50]}..."
            value = f'''<blockquote data-quote-id="{quote.id}" data-source="pdf"> <p>{quote.quote_text}</p> <cite>Source: {quote.pdf_document.title}, page {quote.page_number}</cite> </blockquote>'''
            formatted_quotes.append({'title': title, 'value': value})
    return JsonResponse(formatted_quotes, safe=False)


def all_quotes_list_for_tinymce(request):
    all_quotes = []

    # PDF Quotes
    pdf_quotes = PDFQuote.objects.select_related('pdf_document').all()
    for quote in pdf_quotes:
        if quote.pdf_document:
            url = reverse('core:pdf_document_public', args=[quote.pdf_document.pk])
            source_text = f"Source: {escape(quote.pdf_document.title)}, page {quote.page_number}"
            all_quotes.append({
                'id': quote.id,
                'type': 'PDF',
                'sort_date': quote.pdf_document.document_date or quote.pdf_document.uploaded_at.date(),
                'title': f"{quote.pdf_document.title} (p. {quote.page_number}) - {quote.quote_text[:50]}...",
                'value': f'<i>"{escape(quote.quote_text)}"</i> (<a href="{url}" style="color: black; text-decoration: none;" data-quote-id="{quote.id}" data-source="pdf">{source_text}</a>)'
            })

    # Email Quotes
    email_quotes = EmailQuote.objects.select_related('email').all()
    for quote in email_quotes:
        url = reverse('core:email_public', args=[quote.email.pk])
        source_text = f"Source: Email from {escape(quote.email.sender)} on {quote.email.date_sent.strftime('%Y-%m-%d')}"
        all_quotes.append({
            'id': quote.id,
            'type': 'Email',
            'sort_date': quote.email.date_sent.date(),
            'title': f"{quote.email.subject} ({quote.email.date_sent.strftime('%Y-%m-%d')}) - {quote.quote_text[:50]}...",
            'value': f'<i>"{escape(quote.quote_text)}"</i> (<a href="{url}" style="color: black; text-decoration: none;" data-quote-id="{quote.id}" data-source="email">{source_text}</a>)'
        })

    # Sort all quotes by date (desc) and then by id (asc)
    all_quotes.sort(key=lambda x: (x['sort_date'], x['id']), reverse=True)

    # Group by type
    grouped_quotes = {}
    for quote in all_quotes:
        if quote['type'] not in grouped_quotes:
            grouped_quotes[quote['type']] = []
        grouped_quotes[quote['type']].append(quote)

    return JsonResponse(grouped_quotes, safe=False)


def ajax_search_emails(request):
    return JsonResponse({'emails': []})


class TrameNarrativeListView(ListView):
    model = TrameNarrative
    template_name = 'argument_manager/tiamenarrative_list.html'
    context_object_name = 'narratives'

    def get_queryset(self):
        return TrameNarrative.objects.order_by('titre')


class TrameNarrativeDetailView(DetailView):
    model = TrameNarrative
    context_object_name = 'narrative'
    def get_template_names(self):
        view_type = self.request.GET.get('view', 'accordion')
        if view_type == 'columns':
            return ['argument_manager/tiamenarrative_detail.html']
        return ['argument_manager/tiamenarrative_detail_accordion.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        narrative = self.get_object()
        narrative_data = {
            'events': [{'title': f'{e.date.strftime("%Y-%m-%d")}: {e.explanation[:50]}...', 'text': e.explanation, 'url': reverse('events:detail', args=[e.pk])} for e in narrative.evenements.all()],
            'emailQuotes': [{'title': f'{q.quote_text[:50]}...', 'text': q.quote_text, 'url': reverse('email_manager:thread_detail', args=[q.email.thread.pk])} for q in narrative.citations_courriel.select_related('email__thread').all()],
            'pdfQuotes': [{'title': f'{q.quote_text[:50]}...', 'text': q.quote_text, 'url': reverse('pdf_manager:pdf_detail', args=[q.pdf_document.pk])} for q in narrative.citations_pdf.select_related('pdf_document').all()]
        }
        context['narrative_data_json'] = json.dumps(narrative_data)
        allegations = narrative.targeted_statements.all()
        allegation_ids = [str(allegation.pk) for allegation in allegations]
        context['highlight_ids'] = ",".join(allegation_ids)
        context['allegations_with_docs'] = []
        return context


def get_grouped_allegations():
    statement_ct = ContentType.objects.get_for_model(Statement)
    nodes = LibraryNode.objects.filter(
        content_type=statement_ct,
        document__source_type=DocumentSource.REPRODUCED
    ).select_related('document').prefetch_related('content_object')
    
    grouped = defaultdict(list)
    for node in nodes:
        stmt = node.content_object
        if stmt and stmt.is_true is False and stmt.is_falsifiable is True:
            grouped[node.document].append(stmt)
            
    return dict(sorted(grouped.items(), key=lambda x: x[0].title))


class TrameNarrativeCreateView(CreateView):
    model = TrameNarrative
    form_class = TrameNarrativeForm
    template_name = 'argument_manager/tiamenarrative_form.html'
    success_url = reverse_lazy('argument_manager:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grouped_allegations'] = get_grouped_allegations()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Narrative created successfully.")
        response = super().form_valid(form)
        selected_events_str = self.request.POST.get('selected_events', '')
        if selected_events_str:
            self.object.evenements.set(selected_events_str.split(','))
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Error creating narrative. Please check the form.")
        return super().form_invalid(form)


class TrameNarrativeUpdateView(UpdateView):
    model = TrameNarrative
    form_class = TrameNarrativeForm
    template_name = 'argument_manager/tiamenarrative_form.html'
    def get_success_url(self):
        return reverse_lazy('argument_manager:detail', kwargs={'pk': self.object.pk})
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grouped_allegations'] = get_grouped_allegations()
        narrative = self.get_object()
        context['associated_events'] = narrative.evenements.all()
        context['associated_email_quotes'] = narrative.citations_courriel.select_related('email').all()
        context['associated_pdf_quotes'] = narrative.citations_pdf.select_related('pdf_document').all()
        context['associated_photo_documents'] = narrative.photo_documents.all()
        context['associated_statements'] = narrative.source_statements.all()
        context['associated_chat_sequences'] = narrative.citations_chat.all()
        return context
    def form_valid(self, form):
        messages.success(self.request, "Narrative updated successfully.")
        response = super().form_valid(form)
        self.object.evenements.set(self.request.POST.get('selected_events', '').split(',') if self.request.POST.get('selected_events') else [])
        self.object.citations_courriel.set(self.request.POST.get('selected_email_quotes', '').split(',') if self.request.POST.get('selected_email_quotes') else [])
        self.object.citations_pdf.set(self.request.POST.get('selected_pdf_quotes', '').split(',') if self.request.POST.get('selected_pdf_quotes') else [])
        self.object.photo_documents.set(self.request.POST.get('selected_photo_documents', '').split(',') if self.request.POST.get('selected_photo_documents') else [])
        self.object.source_statements.set(self.request.POST.get('selected_statements', '').split(',') if self.request.POST.get('selected_statements') else [])
        self.object.citations_chat.set(self.request.POST.get('selected_chat_sequences', '').split(',') if self.request.POST.get('selected_chat_sequences') else [])
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Error updating narrative. Please check the form.")
        return super().form_invalid(form)


class TrameNarrativeDeleteView(DeleteView):
    model = TrameNarrative
    template_name = 'argument_manager/tiamenarrative_confirm_delete.html'
    context_object_name = 'narrative'
    success_url = reverse_lazy('argument_manager:list')


@require_POST
def ajax_update_summary(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        data = json.loads(request.body)
        new_summary = data.get('resume')
        if new_summary is not None:
            narrative.resume = new_summary
            narrative.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'No summary provided.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def ajax_run_narrative_audit(request, pk):
    """
    Vue AJAX appelée par le bouton 'Analyser / Auditer' sur la page de Trame.
    """
    try:
        narrative = get_object_or_404(TrameNarrative, pk=pk)
        
        # Lancement de l'audit
        analysis_result = run_narrative_audit_service(narrative)
        
        # Check if the result contains an error key
        if isinstance(analysis_result, dict) and 'error' in analysis_result:
            return JsonResponse({'success': False, 'error': analysis_result['error'], 'raw': analysis_result.get('raw', '')}, status=500)

        # Sauvegarde
        narrative.ai_analysis_json = analysis_result
        narrative.analysis_date = timezone.now()
        narrative.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Audit forensique terminé avec succès.',
            'analysis': analysis_result
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def affidavit_generator_view(request, pk):
    narrative = get_object_or_404(TrameNarrative.objects.prefetch_related('targeted_statements', 'evenements__linked_photos', 'photo_documents__photos', 'citations_courriel__email', 'citations_pdf__pdf_document', 'source_statements', 'citations_chat__messages'), pk=pk)
    claims = [{'id': f'C-{s.pk}', 'text': s.text, 'obj': s} for s in narrative.targeted_statements.all()]
    all_evidence_source = []
    all_evidence_source.extend([{'type': 'Event', 'date': item.date, 'obj': item} for item in narrative.evenements.all()])
    all_evidence_source.extend([{'type': 'PhotoDocument', 'date': item.created_at.date(), 'obj': item} for item in narrative.photo_documents.all()])
    all_evidence_source.extend([{'type': 'Statement', 'date': item.created_at.date(), 'obj': item} for item in narrative.source_statements.all()])
    all_evidence_source.extend([{'type': 'ChatSequence', 'date': item.start_date.date() if item.start_date else None, 'obj': item} for item in narrative.citations_chat.all()])
    pdf_quotes = narrative.citations_pdf.select_related('pdf_document').order_by('pdf_document_id', 'page_number')
    for pdf_document, quotes in groupby(pdf_quotes, key=lambda q: q.pdf_document):
        if not pdf_document: continue
        quotes_list = list(quotes)
        if not quotes_list: continue
        pdf_date = getattr(pdf_document, 'document_date', None) or pdf_document.uploaded_at.date()
        all_evidence_source.append({'type': 'PDFDocument', 'date': pdf_date, 'obj': pdf_document, 'quotes': quotes_list})
    email_quotes = narrative.citations_courriel.select_related('email').order_by('email_id', 'id')
    for email, quotes in groupby(email_quotes, key=lambda q: q.email):
        if not email: continue
        quotes_list = list(quotes)
        if not quotes_list: continue
        all_evidence_source.append({'type': 'Email', 'date': email.date_sent.date(), 'obj': email, 'quotes': quotes_list})
    
    all_evidence_source.sort(key=lambda x: x['date'] if x['date'] is not None else date.max)

    exhibits = []
    exhibit_counter = 1
    for evidence in all_evidence_source:
        item_type = evidence['type']
        obj = evidence['obj']
        exhibit_id_base = f'P-{exhibit_counter}'
        exhibit_data = {}
        if item_type == 'Event':
            exhibit_data = {'type': 'Event', 'type_fr': 'Événement', 'title': obj.explanation, 'date': obj.date, 'main_id': exhibit_id_base, 'evidence_obj': obj, 'items': [{'id': f"{exhibit_id_base}-{i+1}", 'obj': photo, 'description': f"Photo {i+1} of event on {obj.date.strftime('%Y-%m-%d')}"} for i, photo in enumerate(obj.linked_photos.all())]}
        elif item_type == 'PhotoDocument':
            exhibit_data = {'type': 'PhotoDocument', 'type_fr': 'Document photographique', 'title': obj.title, 'description': obj.description, 'date': obj.created_at, 'main_id': exhibit_id_base, 'evidence_obj': obj, 'items': [{'id': f"{exhibit_id_base}-{i+1}", 'obj': photo, 'description': f"Page {i+1} of document '{obj.title}'"} for i, photo in enumerate(obj.photos.all())]}
        elif item_type == 'PDFDocument':
            exhibit_data = {'type': 'PDFDocument', 'type_fr': 'Document PDF', 'title': obj.title, 'date': evidence['date'], 'main_id': exhibit_id_base, 'evidence_obj': obj, 'items': [{'id': f"{exhibit_id_base}-{i+1}", 'obj': quote, 'description': quote.quote_text} for i, quote in enumerate(evidence['quotes'])]}
        elif item_type == 'Email':
            exhibit_data = {'type': 'Email', 'type_fr': 'Courriel', 'title': f"Courriel du {obj.date_sent.strftime('%Y-%m-%d')} - {obj.subject}", 'date': evidence['date'], 'main_id': exhibit_id_base, 'evidence_obj': obj, 'items': [{'id': f"{exhibit_id_base}-{i+1}", 'obj': quote, 'description': quote.quote_text} for i, quote in enumerate(evidence['quotes'])]}
        elif item_type == 'Statement':
            exhibit_data = {'type': 'Statement', 'type_fr': 'Déclaration', 'title': f"Déclaration du {obj.created_at.strftime('%Y-%m-%d')}", 'date': obj.created_at.date(), 'main_id': exhibit_id_base, 'evidence_obj': obj, 'items': [{'id': exhibit_id_base, 'obj': obj, 'description': obj.text}]}
        elif item_type == 'ChatSequence':
            exhibit_data = {'type': 'ChatSequence', 'type_fr': 'Séquence de clavardage', 'title': obj.title, 'date': obj.start_date, 'main_id': exhibit_id_base, 'evidence_obj': obj, 'items': [{'id': f"{exhibit_id_base}-{i+1}", 'obj': msg, 'description': msg.text_content} for i, msg in enumerate(obj.messages.all())]}
        if exhibit_data:
            exhibits.append(exhibit_data)
            exhibit_counter += 1
    summary_parts = [f"pièces {ex['items'][0]['id']} à {ex['items'][-1]['id']}" if len(ex['items']) > 1 else f"pièce {ex['items'][0]['id']}" if ex['items'] else f"pièce {ex['main_id']}" for ex in exhibits]
    summary_str = f"Voir {', '.join(summary_parts)}."
    context = {'narrative': narrative, 'claims': claims, 'exhibits': exhibits, 'summary_str': summary_str}
    return render(request, 'argument_manager/affidavit_generator.html', context)


def ajax_get_statements_list(request):
    statement_content_type = ContentType.objects.get_for_model(Statement)
    nodes_linking_to_statements = LibraryNode.objects.filter(content_type=statement_content_type).select_related('document').prefetch_related('content_object')
    grouped_statements = {}
    for node in nodes_linking_to_statements:
        if node.content_object:
            doc = node.document
            if doc not in grouped_statements:
                grouped_statements[doc] = set()
            grouped_statements[doc].add(node.content_object)
    final_grouped_statements = {doc: list(stmts) for doc, stmts in grouped_statements.items()}
    return render(request, 'argument_manager/_statement_selection_list.html', {'grouped_statements': final_grouped_statements.items()})


@require_POST
def ajax_update_narrative_statements(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        data = json.loads(request.body)
        narrative.source_statements.set(data.get('statement_ids', []))
        updated_statements = narrative.source_statements.all()
        return JsonResponse({'success': True, 'statements': [{'pk': s.pk, 'text': s.text} for s in updated_statements]})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def ajax_add_email_quote(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        data = json.loads(request.body)
        email = get_object_or_404(Email, pk=data.get('email_id'))
        new_quote = EmailQuote.objects.create(email=email, quote_text=data.get('quote_text'))
        narrative.citations_courriel.add(new_quote)
        return JsonResponse({'success': True, 'quote': {'id': new_quote.id, 'text': new_quote.quote_text, 'full_sentence': new_quote.full_sentence}})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def ajax_get_email_threads(request):
    threads = EmailThread.objects.prefetch_related(Prefetch('emails', queryset=Email.objects.order_by('date_sent')))
    processed_threads = [{'pk': t.pk, 'subject': t.subject, 'first_email_date': t.emails.first().date_sent if t.emails.first() else None, 'participants': ", ".join(filter(None, {e.sender for e in t.emails.all()}))} for t in threads]
    return render(request, 'argument_manager/_thread_list.html', {'threads': sorted([t for t in processed_threads if t['first_email_date']], key=lambda t: t['first_email_date'], reverse=True)})


def ajax_get_thread_emails(request, thread_pk):
    thread = get_object_or_404(EmailThread, pk=thread_pk)
    return render(request, 'argument_manager/_email_accordion.html', {'emails': thread.emails.order_by('date_sent')})


def ajax_get_events_list(request):
    return render(request, 'argument_manager/_event_selection_list.html', {'events': Event.objects.prefetch_related('linked_photos').order_by('-date')})


@require_POST
def ajax_update_narrative_events(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        narrative.evenements.set(json.loads(request.body).get('event_ids', []))
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def ajax_get_email_quotes_list(request):
    quotes = EmailQuote.objects.select_related('email__thread').order_by('-email__date_sent')
    grouped_quotes = OrderedDict((thread, list(quotes_in_thread)) for thread, quotes_in_thread in groupby(quotes, key=lambda q: q.email.thread))
    return render(request, 'argument_manager/_email_quote_selection_list.html', {'grouped_quotes': grouped_quotes.items()})


@require_POST
def ajax_update_narrative_email_quotes(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        narrative.citations_courriel.set(json.loads(request.body).get('quote_ids', []))
        return JsonResponse({'success': True, 'quotes': [{'pk': q.pk, 'text': q.quote_text, 'parent_url': q.email.get_absolute_url()} for q in narrative.citations_courriel.select_related('email').all()]})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def ajax_get_pdf_quotes_list(request):
    quotes = PDFQuote.objects.select_related('pdf_document').order_by('-pdf_document__document_date', 'page_number')
    grouped_quotes = OrderedDict((doc, list(quotes_in_doc)) for doc, quotes_in_doc in groupby(quotes, key=lambda q: q.pdf_document) if doc)
    return render(request, 'argument_manager/_pdf_quote_selection_list.html', {'grouped_quotes': grouped_quotes.items()})


@require_POST
def ajax_update_narrative_pdf_quotes(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        narrative.citations_pdf.set(json.loads(request.body).get('quote_ids', []))
        return JsonResponse({'success': True, 'quotes': [{'pk': q.pk, 'text': q.quote_text, 'page': q.page_number, 'parent_url': q.pdf_document.get_absolute_url()} for q in narrative.citations_pdf.select_related('pdf_document').all()]})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def ajax_get_source_pdfs(request):
    documents = PDFDocument.objects.select_related('document_type').order_by('document_type__name', 'title')
    grouped_documents = [{'type_name': key.name if key else "Uncategorized", 'documents': list(group)} for key, group in groupby(documents, key=lambda doc: doc.document_type)]
    return render(request, 'argument_manager/_pdf_source_list.html', {'grouped_documents': grouped_documents})


@require_POST
def ajax_add_pdf_quote(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        data = json.loads(request.body)
        pdf_doc = get_object_or_404(PDFDocument, pk=data.get('doc_id'))
        new_quote = PDFQuote.objects.create(pdf_document=pdf_doc, quote_text=data.get('quote_text'), page_number=data.get('page_number'))
        narrative.citations_pdf.add(new_quote)
        return JsonResponse({'success': True, 'quote': {'pk': new_quote.pk, 'text': new_quote.quote_text, 'page': new_quote.page_number, 'parent_url': pdf_doc.get_absolute_url()}})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def ajax_get_pdf_viewer(request, doc_pk):
    document = get_object_or_404(PDFDocument, pk=doc_pk)
    return render(request, 'argument_manager/_pdf_viewer_partial.html', {'pdf_url_with_params': f"{document.file.url}?v={int(time.time())}#view=Fit&layout=SinglePage"})


def ajax_get_photo_documents(request, narrative_pk):
    narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
    all_docs = PhotoDocument.objects.all().order_by('-created_at')
    associated_doc_ids = set(narrative.photo_documents.values_list('id', flat=True))
    return JsonResponse([{'id': doc.id, 'title': doc.title, 'is_associated': doc.id in associated_doc_ids} for doc in all_docs], safe=False)


@require_POST
def ajax_associate_photo_documents(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        narrative.photo_documents.set([int(id) for id in json.loads(request.body).get('photo_document_ids', [])])
        return JsonResponse({'success': True, 'photo_documents': [{'id': doc.id, 'title': doc.title} for doc in narrative.photo_documents.all().order_by('-created_at')]})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def ajax_get_chat_sequences_list(request, narrative_pk):
    narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
    all_sequences = ChatSequence.objects.all()
    associated_sequence_ids = set(narrative.citations_chat.values_list('id', flat=True))
    
    context = {
        'all_sequences': all_sequences,
        'associated_sequence_ids': associated_sequence_ids,
    }
    return render(request, 'argument_manager/_chat_sequence_selection_list.html', context)

@require_POST
def ajax_update_narrative_chat_sequences(request, narrative_pk):
    try:
        narrative = get_object_or_404(TrameNarrative, pk=narrative_pk)
        data = json.loads(request.body)
        sequence_ids = data.get('sequence_ids', [])
        narrative.citations_chat.set(sequence_ids)
        
        # Prepare data for the response
        updated_sequences = narrative.citations_chat.all()
        response_data = [{
            'pk': seq.pk,
            'title': seq.title,
            'message_count': seq.messages.count(),
            'start_date': seq.start_date.strftime('%Y-%m-%d') if seq.start_date else ''
        } for seq in updated_sequences]
        
        return JsonResponse({'success': True, 'sequences': response_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
