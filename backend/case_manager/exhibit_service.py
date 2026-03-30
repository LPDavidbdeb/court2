# case_manager/exhibit_service.py

from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Min
from django.utils import timezone
from collections import defaultdict
from datetime import datetime

from .models import LegalCase, ExhibitRegistry, ProducedExhibit
from document_manager.models import LibraryNode, Statement, Document, DocumentSource
from email_manager.models import Email, Quote as EmailQuote
from events.models import Event
from photos.models import PhotoDocument
from pdf_manager.models import PDFDocument, Quote as PDFQuote
from googlechat_manager.models import ChatSequence

def refresh_case_exhibits(case_id):
    """
    Analyzes all contestations within a case, finds all unique pieces of evidence,
    assigns numbers to new ones, AND REMOVES orphans that are no longer used.
    """
    try:
        case = LegalCase.objects.get(pk=case_id)
    except LegalCase.DoesNotExist:
        return 0

    # 1. Gather ALL unique evidence objects currently in use
    all_evidence_objects = set()
    prefetch_args = [
        'supporting_narratives__evenements',
        'supporting_narratives__citations_courriel__email',
        'supporting_narratives__citations_pdf__pdf_document',
        'supporting_narratives__photo_documents',
        'supporting_narratives__citations_chat',
        'supporting_narratives__source_statements'
    ]
    for contestation in case.contestations.prefetch_related(*prefetch_args).all():
        for narrative in contestation.supporting_narratives.all():
            for event in narrative.evenements.all():
                all_evidence_objects.add(event)
            for email_quote in narrative.citations_courriel.all():
                if email_quote.email:
                    all_evidence_objects.add(email_quote.email)
            for pdf_quote in narrative.citations_pdf.all():
                if pdf_quote.pdf_document:
                    all_evidence_objects.add(pdf_quote.pdf_document)
            for photo_doc in narrative.photo_documents.all():
                all_evidence_objects.add(photo_doc)
            
            for chat_seq in narrative.citations_chat.all():
                all_evidence_objects.add(chat_seq)
            
            # Handle statements / library nodes
            statement_ids = narrative.source_statements.values_list('id', flat=True)
            if statement_ids:
                stmt_content_type = ContentType.objects.get_for_model(Statement)
                nodes = LibraryNode.objects.filter(
                    content_type=stmt_content_type,
                    object_id__in=statement_ids
                ).select_related('document')
                for node in nodes:
                    if node.document:
                        all_evidence_objects.add(node.document)

    # 2. Identify "Valid" Keys (ContentType ID + Object ID)
    valid_keys = set()
    for item in all_evidence_objects:
        if item is None: continue
        ct = ContentType.objects.get_for_model(item)
        valid_keys.add((ct.id, item.pk))

    # 3. DELETE Orphans: Remove registry entries that are no longer in valid_keys
    existing_exhibits = ExhibitRegistry.objects.filter(case=case)
    for exhibit in existing_exhibits:
        if (exhibit.content_type_id, exhibit.object_id) not in valid_keys:
            exhibit.delete()

    # 4. ADD New Items
    current_max = case.exhibits.aggregate(max_num=models.Max('exhibit_number'))['max_num'] or 0
    
    for item in all_evidence_objects:
        if item is None: continue
        ct = ContentType.objects.get_for_model(item)
        
        obj, created = ExhibitRegistry.objects.get_or_create(
            case=case,
            content_type=ct,
            object_id=item.pk,
            defaults={'exhibit_number': current_max + 1}
        )
        
        if created:
            current_max += 1

    return current_max

def get_datetime_for_sorting(exhibit, exhibit_objects):
    """
    Helper to extract a comparable datetime from pre-fetched evidence objects.
    """
    obj = exhibit_objects.get((exhibit.content_type_id, exhibit.object_id))
    if not obj:
        return timezone.now()

    dt = None
    model_name = exhibit.content_type.model
    
    if model_name == 'email' and obj.date_sent:
        dt = obj.date_sent
    elif model_name == 'event' and obj.date:
        dt = datetime.combine(obj.date, datetime.min.time())
    elif model_name == 'document':
        if obj.document_original_date:
            dt = datetime.combine(obj.document_original_date, datetime.min.time())
    elif model_name == 'librarynode' and hasattr(obj, 'document') and obj.document.document_original_date:
        dt = datetime.combine(obj.document.document_original_date, datetime.min.time())
    elif model_name == 'photodocument':
        if hasattr(obj, 'real_date') and obj.real_date:
            dt = obj.real_date
        else:
            dt = obj.created_at
    elif model_name == 'pdfdocument' and obj.document_date:
        dt = datetime.combine(obj.document_date, datetime.min.time())
    elif model_name == 'quote' and hasattr(obj, 'pdf_document') and obj.pdf_document and obj.pdf_document.document_date:
        dt = datetime.combine(obj.pdf_document.document_date, datetime.min.time())
    elif model_name == 'chatsequence':
        if obj.start_date:
            dt = obj.start_date
        elif obj.messages.exists():
            dt = obj.messages.order_by('timestamp').first().timestamp

    if not dt and hasattr(obj, 'created_at') and obj.created_at:
        dt = obj.created_at

    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    
    return dt or timezone.now()

def rebuild_produced_exhibits(case_id):
    """
    Wipes and repopulates the ProducedExhibit table for a case atomically
    and with optimized database queries.
    """
    try:
        with transaction.atomic():
            case = LegalCase.objects.get(pk=case_id)
            ProducedExhibit.objects.filter(case=case).delete()
            
            email_quotes_map = defaultdict(list)
            all_email_quotes = EmailQuote.objects.filter(
                trames_narratives__supported_contestations__case=case
            ).select_related('email', 'email__sender_protagonist').prefetch_related('email__recipient_protagonists').distinct()
            for quote in all_email_quotes:
                if quote.email_id:
                    email_quotes_map[quote.email_id].append(quote)

            pdf_quotes_map = defaultdict(list)
            all_pdf_quotes = PDFQuote.objects.filter(
                trames_narratives__supported_contestations__case=case
            ).select_related('pdf_document', 'pdf_document__author').distinct()
            for quote in all_pdf_quotes:
                if quote.pdf_document_id:
                    pdf_quotes_map[quote.pdf_document_id].append(quote)

            refresh_case_exhibits(case_id) 
            initial_exhibits = list(case.exhibits.all().select_related('content_type'))

            library_node_ct = ContentType.objects.get_for_model(LibraryNode)
            ln_exhibit_ids_to_check = [
                ex.object_id for ex in initial_exhibits if ex.content_type_id == library_node_ct.id
            ]

            valid_ln_ids = set()
            if ln_exhibit_ids_to_check:
                valid_ln_ids = set(
                    LibraryNode.objects.filter(
                        pk__in=ln_exhibit_ids_to_check,
                        document__source_type=DocumentSource.REPRODUCED
                    ).values_list('pk', flat=True)
                )

            all_exhibits = []
            for ex in initial_exhibits:
                if ex.content_type_id == library_node_ct.id:
                    if ex.object_id in valid_ln_ids:
                        all_exhibits.append(ex)
                else:
                    all_exhibits.append(ex)
            
            exhibits_by_type = defaultdict(list)
            for ex in all_exhibits:
                exhibits_by_type[ex.content_type_id].append(ex.object_id)

            content_types = ContentType.objects.in_bulk(exhibits_by_type.keys())

            exhibit_objects = {}
            for ct_id, obj_ids in exhibits_by_type.items():
                ct = content_types.get(ct_id)
                if not ct: continue
                
                model_class = ct.model_class()
                queryset = model_class.objects.filter(pk__in=obj_ids)
                
                if model_class == LibraryNode:
                    queryset = queryset.select_related('document', 'document__author', 'content_type').prefetch_related('content_object')
                elif model_class == Email:
                    queryset = queryset.select_related('sender_protagonist').prefetch_related('recipient_protagonists')
                elif model_class == PhotoDocument:
                    queryset = queryset.select_related('author').annotate(
                        real_date=Min('photos__datetime_original')
                    )
                elif model_class == PDFDocument:
                    queryset = queryset.select_related('author')
                elif model_class == PDFQuote:
                    queryset = queryset.select_related('pdf_document', 'pdf_document__author')
                elif model_class == ChatSequence:
                    queryset = queryset.prefetch_related(
                        'messages', 
                        'messages__sender', 
                        'messages__sender__protagonist'
                    )

                for obj in queryset:
                    exhibit_objects[(ct_id, obj.id)] = obj
            
            exhibits_with_sort_date = []
            
            for ex in all_exhibits:
                obj = exhibit_objects.get((ex.content_type_id, ex.object_id))
                if not obj: continue
                
                model_name = ex.content_type.model
                
                if model_name == 'chatsequence':
                    if not obj.messages.exists():
                        continue
                    msgs = obj.messages.all().order_by('timestamp')
                    sessions_map = defaultdict(list)
                    for m in msgs:
                        date_key = m.timestamp.date()
                        sessions_map[date_key].append(m)
                    
                    for date_key, session_msgs in sessions_map.items():
                        sort_dt = session_msgs[0].timestamp
                        exhibits_with_sort_date.append({
                            'exhibit': ex,
                            'sort_date': sort_dt,
                            'virtual_msgs': session_msgs,
                            'is_virtual': True
                        })
                else:
                    sort_date = get_datetime_for_sorting(ex, exhibit_objects)
                    exhibits_with_sort_date.append({
                        'exhibit': ex,
                        'sort_date': sort_date,
                        'virtual_msgs': None,
                        'is_virtual': False
                    })

            exhibits_with_sort_date.sort(key=lambda x: x['sort_date'])

            new_rows = []
            global_counter = 1
            processed_parent_docs = set()

            for item in exhibits_with_sort_date:
                exhibit = item['exhibit']
                virtual_msgs = item.get('virtual_msgs')
                obj = exhibit_objects.get((exhibit.content_type_id, exhibit.object_id))
                if not obj: continue

                model_name = exhibit.content_type.model
                sort_date = item['sort_date']

                if model_name == 'chatsequence':
                    main_label = f"P-{global_counter}"
                    exhibit_type_str = "Extrait Clavardage"
                    first_msg = virtual_msgs[0]
                    last_msg = virtual_msgs[-1]
                    date_str = first_msg.timestamp.strftime('%Y-%m-%d')
                    start_time = first_msg.timestamp.strftime('%H:%M')
                    end_time = last_msg.timestamp.strftime('%H:%M')
                    date_text = f"Le {date_str} de {start_time} à {end_time}"
                    header = f"SÉQUENCE : {obj.title} (Suite...)" if item.get('is_virtual') and len(virtual_msgs) < obj.messages.count() else obj.title
                    transcript_lines = [header, ""]
                    
                    last_sender = None
                    last_time = None
                    for msg in virtual_msgs:
                        sender_name = msg.sender.name if msg.sender else "Inconnu"
                        msg_time = msg.timestamp
                        minutes_diff = (msg_time - last_time).total_seconds() / 60 if last_time else 0
                        if sender_name != last_sender or minutes_diff > 20:
                            if last_sender is not None:
                                transcript_lines.append("") 
                            header_time = msg_time.strftime('%H:%M')
                            transcript_lines.append(f"[{sender_name} à {header_time}] :")
                            last_sender = sender_name
                        transcript_lines.append(f"- {msg.text_content}")
                        last_time = msg_time
                    desc_text = "\n".join(transcript_lines)
                    
                    participants = set()
                    for m in virtual_msgs:
                        if m.sender:
                            participants.add(m.sender)
                    parties_lines = []
                    for p in participants:
                        name = p.name or p.email or "Inconnu"
                        role = f" [{p.protagonist.role}]" if p.protagonist else ""
                        parties_lines.append(f"{name}{role}")
                    parties_str = "Entre:\n" + "\nEt:\n".join(parties_lines)

                    new_rows.append(ProducedExhibit(
                        case=case, sort_order=len(new_rows) + 1, label=main_label, exhibit_type=exhibit_type_str,
                        date_display=date_text, description=desc_text, parties=parties_str, content_object=obj
                    ))
                    global_counter += 1
                    continue

                if model_name == 'document':
                    main_label = f"P-{global_counter}"
                    date_text = obj.document_original_date.strftime('%Y-%m-%d') if obj.document_original_date else "Date Inconnue"
                    desc_text = obj.title
                    parties_str = f"Auteur: {obj.author.get_full_name_with_role()}" if obj.author else ""
                    new_rows.append(ProducedExhibit(
                        case=case, sort_order=len(new_rows) + 1, label=main_label, exhibit_type="Document (Général)",
                        date_display=date_text, description=desc_text, parties=parties_str, content_object=obj
                    ))
                    global_counter += 1
                    continue

                if model_name == 'librarynode':
                    parent_doc = obj.document
                    if parent_doc.id in processed_parent_docs:
                        continue
                    main_label = f"P-{global_counter}"
                    date_text = parent_doc.document_original_date.strftime('%Y-%m-%d') if parent_doc.document_original_date else "Date Inconnue"
                    desc_text = parent_doc.title
                    parties_str = f"Auteur: {parent_doc.author.get_full_name_with_role()}" if parent_doc.author else ""
                    new_rows.append(ProducedExhibit(
                        case=case, sort_order=len(new_rows) + 1, label=main_label, exhibit_type="Document (Général)",
                        date_display=date_text, description=desc_text, parties=parties_str, content_object=parent_doc
                    ))
                    statement_nodes_for_this_doc = []
                    for other_item in exhibits_with_sort_date:
                        other_exhibit = other_item['exhibit']
                        if other_exhibit.content_type.model == 'librarynode':
                            other_node = exhibit_objects.get((other_exhibit.content_type_id, other_exhibit.object_id))
                            if other_node and other_node.document_id == parent_doc.id:
                                if other_node.content_object and isinstance(other_node.content_object, Statement):
                                    statement_nodes_for_this_doc.append(other_node.content_object)
                    for idx, statement_obj in enumerate(statement_nodes_for_this_doc, 1):
                        new_rows.append(ProducedExhibit(
                            case=case, sort_order=len(new_rows) + 1, label=f"{main_label}-{idx}", exhibit_type="Déclaration",
                            date_display="", description=statement_obj.text, parties="", content_object=statement_obj
                        ))
                    processed_parent_docs.add(parent_doc.id)
                    global_counter += 1
                    continue

                main_label = f"P-{global_counter}"
                exhibit_type_str, date_text, desc_text, parties_str = "", "", "", ""
                if model_name == 'email':
                    exhibit_type_str = "Courriel"
                    date_text = obj.date_sent.strftime('%Y-%m-%d %H:%M') if obj.date_sent else "Date Inconnue"
                    desc_text = obj.subject or '[Sans sujet]'
                    sender = obj.sender_protagonist.get_full_name_with_role() if obj.sender_protagonist else obj.sender
                    recipients = ", ".join([p.get_full_name_with_role() for p in obj.recipient_protagonists.all()])
                    parties_str = f"De: {sender}\nÀ: {recipients}"
                elif model_name == 'event':
                    exhibit_type_str = "Événement"
                    if ':' in (obj.explanation or ""):
                        parts = obj.explanation.rsplit(':', 1)
                        date_text, desc_text = parts[0].strip(), parts[1].strip()
                    else:
                        date_text = obj.date.strftime('%Y-%m-%d') if obj.date else "Date Inconnue"
                        desc_text = obj.explanation or ""
                elif model_name == 'photodocument':
                    exhibit_type_str = "Document Photo"
                    date_text = sort_date.strftime('%Y-%m-%d %H:%M') if sort_date else "Date Inconnue"
                    desc_text = obj.title
                    if obj.description: desc_text += f"\n{obj.description}"
                    if obj.author: parties_str = f"Auteur: {obj.author.get_full_name_with_role()}"
                elif model_name == 'pdfdocument':
                    exhibit_type_str = "Document PDF"
                    date_text = obj.document_date.strftime('%Y-%m-%d') if obj.document_date else "Date Inconnue"
                    desc_text = obj.title
                    if obj.author: parties_str = f"Auteur: {obj.author.get_full_name_with_role()}"
                else: 
                    exhibit_type_str = "Autre"
                    date_text = sort_date.strftime('%Y-%m-%d') if sort_date else "Date Inconnue"
                    desc_text = str(obj)

                new_rows.append(ProducedExhibit(case=case, sort_order=len(new_rows) + 1, label=main_label, exhibit_type=exhibit_type_str, date_display=date_text, description=desc_text, parties=parties_str, content_object=obj))
                
                if model_name == 'email':
                    quotes = sorted(email_quotes_map.get(obj.id, []), key=lambda q: q.created_at)
                    for idx, quote_obj in enumerate(quotes, 1):
                        quote_email = quote_obj.email
                        quote_date_text = quote_email.date_sent.strftime('%Y-%m-%d %H:%M') if quote_email.date_sent else ""
                        sender = quote_email.sender_protagonist.get_full_name_with_role() if quote_email.sender_protagonist else quote_email.sender
                        recipients = ", ".join([p.get_full_name_with_role() for p in quote_email.recipient_protagonists.all()])
                        quote_parties_str = f"De: {sender}\nÀ: {recipients}"
                        short_q = (quote_obj.quote_text[:200] + '..') if len(quote_obj.quote_text) > 20000 else quote_obj.quote_text
                        new_rows.append(ProducedExhibit(case=case, sort_order=len(new_rows) + 1, label=f"{main_label}-{idx}", exhibit_type="Citation Courriel", date_display=quote_date_text, description=f"« {short_q} »", parties=quote_parties_str, content_object=quote_obj))
                
                if model_name == 'pdfdocument':
                    quotes = sorted(pdf_quotes_map.get(obj.id, []), key=lambda q: q.created_at)
                    for idx, quote_obj in enumerate(quotes, 1):
                        quote_doc = quote_obj.pdf_document
                        quote_date_text = quote_doc.document_date.strftime('%Y-%m-%d') if quote_doc.document_date else ""
                        quote_parties_str = f"Auteur: {quote_doc.author.get_full_name_with_role()}" if quote_doc.author else ""
                        desc = f"« {quote_obj.quote_text} » (p. {quote_obj.page_number})"
                        new_rows.append(ProducedExhibit(case=case, sort_order=len(new_rows) + 1, label=f"{main_label}-{idx}", exhibit_type="Citation PDF", date_display=quote_date_text, description=desc, parties=quote_parties_str, content_object=quote_obj))

                global_counter += 1

            ProducedExhibit.objects.bulk_create(new_rows)
            return len(new_rows)

    except Exception as e:
        raise e
