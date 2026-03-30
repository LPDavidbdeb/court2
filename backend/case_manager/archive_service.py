# case_manager/archive_service.py

from django.db import transaction
from django.utils import timezone
from collections import defaultdict
from datetime import datetime

from .models import LegalCase, ProducedExhibit
from document_manager.models import LibraryNode, Document, DocumentSource
from email_manager.models import Email, Quote as EmailQuote
from events.models import Event
from photos.models import PhotoDocument
from pdf_manager.models import PDFDocument, Quote as PDFQuote
from googlechat_manager.models import ChatSequence

def rebuild_global_exhibits(target_case_id):
    """
    Populates the Master Archive case with ALL evidence, maintaining
    Parent-Child relationships (Email -> Quotes, Document -> Statements).
    """
    try:
        with transaction.atomic():
            case = LegalCase.objects.get(pk=target_case_id)
            ProducedExhibit.objects.filter(case=case).delete()

            # A. Email Quotes
            email_quotes_map = defaultdict(list)
            all_email_quotes = EmailQuote.objects.select_related('email').all()
            for q in all_email_quotes:
                if q.email_id:
                    email_quotes_map[q.email_id].append(q)

            # B. PDF Quotes
            pdf_quotes_map = defaultdict(list)
            all_pdf_quotes = PDFQuote.objects.select_related('pdf_document').all()
            for q in all_pdf_quotes:
                if q.pdf_document_id:
                    pdf_quotes_map[q.pdf_document_id].append(q)

            # C. Statements
            statement_map = defaultdict(list)
            linked_nodes = LibraryNode.objects.filter(
                content_type__model='statement',
                document__source_type=DocumentSource.REPRODUCED
            ).prefetch_related('content_object')
            
            for node in linked_nodes:
                if node.document_id and node.content_object:
                    statement_map[node.document_id].append(node.content_object)

            parent_items = []
            for obj in Email.objects.select_related('sender_protagonist').prefetch_related('recipient_protagonists').all():
                parent_items.append({'obj': obj, 'sort_date': get_sort_date(obj)})
            for obj in PDFDocument.objects.select_related('author').all():
                parent_items.append({'obj': obj, 'sort_date': get_sort_date(obj)})
            for obj in Document.objects.select_related('author').all():
                parent_items.append({'obj': obj, 'sort_date': get_sort_date(obj)})
            for obj in Event.objects.all():
                parent_items.append({'obj': obj, 'sort_date': get_sort_date(obj)})
            for obj in PhotoDocument.objects.select_related('author').all():
                parent_items.append({'obj': obj, 'sort_date': get_sort_date(obj)})
            for obj in ChatSequence.objects.all():
                parent_items.append({'obj': obj, 'sort_date': get_sort_date(obj)})

            parent_items.sort(key=lambda x: x['sort_date'])

            new_rows = []
            global_counter = 1

            for item in parent_items:
                parent_obj = item['obj']
                sort_date = item['sort_date']
                model_name = parent_obj._meta.model_name
                main_label = f"G-{global_counter}"
                exhibit_type, description, parties = get_item_metadata(parent_obj)
                date_display = sort_date.strftime('%Y-%m-%d')

                doc_url = None
                if hasattr(parent_obj, 'get_public_url'):
                    try:
                        doc_url = parent_obj.get_public_url()
                    except Exception:
                        doc_url = None

                new_rows.append(ProducedExhibit(
                    case=case, sort_order=len(new_rows) + 1, label=main_label, exhibit_type=exhibit_type,
                    date_display=date_display, description=description, parties=parties,
                    content_object=parent_obj, public_url=doc_url
                ))

                if model_name == 'email':
                    children = email_quotes_map.get(parent_obj.id, [])
                    children.sort(key=lambda x: x.created_at)
                    for idx, child in enumerate(children, 1):
                        short_desc = (child.quote_text[:200] + '..') if len(child.quote_text) > 200 else child.quote_text
                        new_rows.append(ProducedExhibit(
                            case=case, sort_order=len(new_rows) + 1, label=f"{main_label}-{idx}",
                            exhibit_type="Citation Courriel", date_display="",
                            description=f"« {short_desc} »", parties=f"Source: {main_label}", content_object=child
                        ))
                elif model_name == 'pdfdocument':
                    children = pdf_quotes_map.get(parent_obj.id, [])
                    children.sort(key=lambda x: (x.page_number, x.created_at))
                    for idx, child in enumerate(children, 1):
                        desc = f"« {child.quote_text} » (p. {child.page_number})"
                        new_rows.append(ProducedExhibit(
                            case=case, sort_order=len(new_rows) + 1, label=f"{main_label}-{idx}",
                            exhibit_type="Citation PDF", date_display="", description=desc,
                            parties=f"Source: {main_label}", content_object=child
                        ))
                elif model_name == 'document':
                    children = statement_map.get(parent_obj.id, [])
                    for idx, stmt in enumerate(children, 1):
                        new_rows.append(ProducedExhibit(
                            case=case, sort_order=len(new_rows) + 1, label=f"{main_label}-{idx}",
                            exhibit_type="Déclaration", date_display="", description=stmt.text,
                            parties=f"Source: {main_label}", content_object=stmt
                        ))

                global_counter += 1

            ProducedExhibit.objects.bulk_create(new_rows)
            return len(new_rows)

    except Exception as e:
        raise e

def get_item_metadata(obj):
    """Helper to keep the main loop clean."""
    model_name = obj._meta.model_name
    exhibit_type = "Autre"
    description = str(obj)
    parties = ""

    if model_name == 'email':
        exhibit_type = "Courriel"
        description = obj.subject or "[Sans sujet]"
        sender = obj.sender_protagonist.get_full_name_with_role() if obj.sender_protagonist else obj.sender
        recipients = ", ".join([p.get_full_name_with_role() for p in obj.recipient_protagonists.all()])
        parties = f"De: {sender}\nÀ: {recipients}"
    elif model_name == 'pdfdocument':
        exhibit_type = "Document PDF"
        description = obj.title
        if obj.author: parties = f"Auteur: {obj.author.get_full_name_with_role()}"
    elif model_name == 'document':
        exhibit_type = "Document (Général)"
        description = obj.title
        if obj.author: parties = f"Auteur: {obj.author.get_full_name_with_role()}"
    elif model_name == 'event':
        exhibit_type = "Événement"
        if ':' in (obj.explanation or ""):
             parts = obj.explanation.rsplit(':', 1)
             description = parts[1].strip()
        else:
             description = obj.explanation or ""
    elif model_name == 'photodocument':
        exhibit_type = "Document Photo"
        description = obj.title
        if obj.author: parties = f"Auteur: {obj.author.get_full_name_with_role()}"
    elif model_name == 'chatsequence':
        exhibit_type = "Extrait Chat"
        description = obj.title
        parties = f"{obj.messages.count()} messages"

    return exhibit_type, description, parties

def get_sort_date(obj):
    """Helper to extract a comparable datetime from any model."""
    dt = timezone.now()
    if hasattr(obj, 'date_sent') and obj.date_sent: dt = obj.date_sent
    elif hasattr(obj, 'document_original_date') and obj.document_original_date: dt = datetime.combine(obj.document_original_date, datetime.min.time())
    elif hasattr(obj, 'document_date') and obj.document_date: dt = datetime.combine(obj.document_date, datetime.min.time())
    elif hasattr(obj, 'date') and obj.date: dt = datetime.combine(obj.date, datetime.min.time())
    elif hasattr(obj, 'start_date') and obj.start_date: dt = obj.start_date
    elif hasattr(obj, 'created_at') and obj.created_at: dt = obj.created_at
    
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt
