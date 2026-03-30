import html
import re
from datetime import date
from django.contrib.contenttypes.models import ContentType
from collections import defaultdict
from document_manager.models import LibraryNode, Statement
from django.utils import timezone

class EvidenceFormatter:
    
    @staticmethod
    def _xml_escape(text):
        if not text: return ""
        return html.escape(str(text))

    @classmethod
    def format_narrative_context_xml(cls, narrative):
        """
        Génère le dossier XML strict pour une seule Trame Narrative.
        Utilisé par l'Auditeur IA.
        """
        xml_output = [f'<dossier_analyse id="TRAME-{narrative.pk}">']

        # 1. LES ALLÉGATIONS (La Thèse Adverse)
        xml_output.append('  <theses_adverses>')
        for stmt in narrative.targeted_statements.all():
            clean_text = cls._xml_escape(stmt.text)
            xml_output.append(f'    <allegation id="A-{stmt.pk}">{clean_text}</allegation>')
        xml_output.append('  </theses_adverses>')

        # 2. LES PREUVES (La Chronologie Factuelle)
        timeline = narrative.get_chronological_evidence()
        xml_output.append('  <elements_preuve>')
        
        for item in timeline:
            obj = item['object']
            date_str = item['date'].isoformat() if item['date'] else "ND"
            type_ref = item['type']
            
            # Gestion des différents types
            if type_ref == 'email':
                # Pour les emails, on veut l'extrait cité
                quote_text = cls._xml_escape(obj.quote_text)
                subject = cls._xml_escape(obj.email.subject)
                sender = cls._xml_escape(obj.email.sender)
                xml_output.append(f'    <preuve type="email" date="{date_str}" id="P-EMAIL-{obj.pk}">')
                xml_output.append(f'      <meta de="{sender}" sujet="{subject}" />')
                xml_output.append(f'      <contenu>{quote_text}</contenu>')
                xml_output.append('    </preuve>')

            elif type_ref == 'event':
                desc = cls._xml_escape(obj.explanation)
                xml_output.append(f'    <preuve type="evenement" date="{date_str}" id="P-EVENT-{obj.pk}">')
                xml_output.append(f'      <description>{desc}</description>')
                xml_output.append('    </preuve>')

            elif type_ref == 'photo':
                desc = cls._xml_escape(obj.description or obj.ai_analysis or "Photo sans description")
                title = cls._xml_escape(obj.title)
                xml_output.append(f'    <preuve type="photo" date="{date_str}" id="P-PHOTO-{obj.pk}">')
                xml_output.append(f'      <titre>{title}</titre>')
                xml_output.append(f'      <analyse_visuelle>{desc}</analyse_visuelle>')
                xml_output.append('    </preuve>')
            
            elif type_ref == 'chat':
                title = cls._xml_escape(obj.title)
                xml_output.append(f'    <preuve type="chat" date="{date_str}" id="P-CHAT-{obj.pk}">')
                xml_output.append(f'      <titre>{title}</titre>')
                for msg in obj.messages.all():
                    sender = cls._xml_escape(msg.sender.name)
                    content = cls._xml_escape(msg.text_content)
                    xml_output.append(f'      <message de="{sender}">{content}</message>')
                xml_output.append('    </preuve>')

        xml_output.append('  </elements_preuve>')
        xml_output.append('</dossier_analyse>')
        
        return "\n".join(xml_output)

    @classmethod
    def format_police_context_xml(cls, narratives_queryset):
        """
        Génère le dossier XML pour le service de police.
        """
        # --- Pre-fetch statement documents to avoid N+1 queries ---
        statement_ids = set()
        for narrative in narratives_queryset:
            statement_ids.update(narrative.targeted_statements.values_list('id', flat=True))
        
        stmt_content_type = ContentType.objects.get_for_model(Statement)
        
        nodes = LibraryNode.objects.filter(
            content_type=stmt_content_type,
            object_id__in=statement_ids,
            document__source_type='REPRODUCED'
        ).select_related('document')
        
        statement_to_doc_title = {node.object_id: node.document.title for node in nodes}
        # --- End pre-fetch ---

        xml_output = ['<dossier_police>']

        # 1. Allégations
        xml_output.append('  <declarations_suspectes>')
        # Use a set to track added statements and prevent duplicates
        added_statements = set()
        for narrative in narratives_queryset:
            for stmt in narrative.targeted_statements.all():
                if stmt.id not in added_statements:
                    clean_text = cls._xml_escape(stmt.text)
                    doc_title = cls._xml_escape(statement_to_doc_title.get(stmt.id, "Source Inconnue"))
                    xml_output.append(f'    <declaration source="{doc_title}">{clean_text}</declaration>')
                    added_statements.add(stmt.id)
        xml_output.append('  </declarations_suspectes>')

        # 2. Chronologie des preuves
        full_timeline = []
        seen_evidence = set() # Use a set to track evidence by (type, pk)

        for narrative in narratives_queryset:
            for item in narrative.get_chronological_evidence():
                evidence_key = (item['type'], item['object'].pk)
                if evidence_key not in seen_evidence:
                    full_timeline.append(item)
                    seen_evidence.add(evidence_key)
        
        sorted_timeline = sorted([item for item in full_timeline if item['date']], key=lambda x: x['date'])
        
        xml_output.append('  <chronologie_faits>')
        for item in sorted_timeline:
            date_str = item['date'].isoformat()
            obj = item['object']
            item_type = item['type']
            
            line = f'<fait date="{date_str}" type="{item_type}">'
            if item_type == 'email':
                line += f"EMAIL: De {cls._xml_escape(obj.email.sender)}, Sujet: {cls._xml_escape(obj.email.subject)}, Citation: '{cls._xml_escape(obj.quote_text)}'"
            elif item_type == 'pdf':
                line += f"PDF: '{cls._xml_escape(obj.pdf_document.title)}', Page {obj.page_number}, Citation: '{cls._xml_escape(obj.quote_text)}'"
            elif item_type == 'event':
                line += f"ÉVÉNEMENT: {cls._xml_escape(obj.explanation)}"
            elif item_type == 'photo':
                line += f"PHOTO: '{cls._xml_escape(obj.title)}' - {cls._xml_escape(obj.description or obj.ai_analysis or '')}"
            elif item_type == 'chat':
                line += f"CHAT: '{cls._xml_escape(obj.title)}'"
            line += '</fait>'
            xml_output.append(f'    {line}')
        xml_output.append('  </chronologie_faits>')
        
        xml_output.append('</dossier_police>')
        return "\n".join(xml_output)

    @staticmethod
    def get_label(obj, exhibit_map):
        """
        Helper to find the P-Number (e.g., 'P-12') for an object.
        """
        if not obj or not exhibit_map:
            return None
        ct = ContentType.objects.get_for_model(obj)
        key = (ct.id, obj.id)
        return exhibit_map.get(key)
    
    @staticmethod
    def get_date(obj):
        if hasattr(obj, 'document_original_date') and obj.document_original_date:
            return obj.document_original_date
        elif hasattr(obj, 'document_date') and obj.document_date:
            return obj.document_date
        elif hasattr(obj, 'date'): return obj.date
        elif hasattr(obj, 'date_sent'): return obj.date_sent.date() if obj.date_sent else date.min
        elif hasattr(obj, 'pdf_document'):
            if obj.pdf_document and hasattr(obj.pdf_document, 'document_original_date') and obj.pdf_document.document_original_date:
                return obj.pdf_document.document_original_date
            elif obj.pdf_document and hasattr(obj.pdf_document, 'document_date') and obj.pdf_document.document_date:
                return obj.pdf_document.document_date
            return date.min
        elif hasattr(obj, 'created_at'): return obj.created_at.date()
        return date.min

    @staticmethod
    def _get_protagonist_display(protagonist, fallback_name):
        if not protagonist:
            return fallback_name
        name = protagonist.get_full_name()
        if protagonist.role:
            return f"{name} [{protagonist.role}]"
        return name

    @classmethod
    def collect_global_evidence(cls, narratives):
        timeline = []
        unique_documents = set()
        narrative_summaries = []

        prefetched_narratives = narratives.prefetch_related(
            'citations_chat__messages__sender'
        )

        for narrative in prefetched_narratives:
            # ... (existing loops for emails, events, etc.)

            # === CHAT EVIDENCE (REVISED) ===
            for chat_seq in narrative.citations_chat.all():
                unique_documents.add(chat_seq)
                
                messages_by_date = defaultdict(list)
                for msg in chat_seq.messages.all():
                    if not msg.timestamp: continue
                    message_date = msg.timestamp.date()
                    messages_by_date[message_date].append(msg)

                for msg_date, msgs_on_day in sorted(messages_by_date.items()):
                    content_preview = "\n".join([f"- {m.sender.name if m.sender else 'Inconnu'}: {m.text_content}" for m in msgs_on_day])
                    
                    timeline.append({
                        'date': msg_date,
                        'type': 'chat_entry',
                        'obj': chat_seq,
                        'parent_doc': chat_seq,
                        'content': content_preview,
                        'narrative_ref': narrative.titre,
                        'title': chat_seq.title
                    })
            # ========================

            narrative_summaries.append(narrative.resume)

        timeline.sort(key=lambda x: x['date'] if x['date'] else timezone.now().date())
        
        return {
            'summaries': narrative_summaries,
            'timeline': timeline,
            'unique_documents': unique_documents
        }

    @classmethod
    def format_timeline_item(cls, item, exhibit_label=None):
        """
        Generates a concise timeline entry. 
        Focuses on the 'Action' or 'Quote', referencing the Exhibit ID.
        """
        obj = item['obj']
        item_date = item.get('date') or cls.get_date(obj)
        
        if not item_date or item_date.year < 1950:
            date_str = "DATE NON SPÉCIFIÉE"
        else:
            date_str = item_date.strftime("%d %B %Y")

        label_str = f" (Pièce {exhibit_label})" if exhibit_label else ""

        if item['type'] == 'email_entry':
            sender = cls._get_protagonist_display(obj.sender_protagonist, obj.sender)
            if obj.recipient_protagonists.exists():
                recipients = [cls._get_protagonist_display(p, "") for p in obj.recipient_protagonists.all()]
                recipient_display = ", ".join(recipients)
            else:
                recipient_display = obj.recipients_to or "Destinataire inconnu"

            text = f"[ {date_str} ] COURRIEL{label_str} : De {sender} à {recipient_display} — Sujet : « {obj.subject} »\n"
            if item.get('quotes'):
                for q in item['quotes']:
                    text += f"    -> CITATION CLÉ : « {q.quote_text} »\n"
            return text

        elif item['type'] == 'pdf_entry':
            text = f"[ {date_str} ] DOCUMENT{label_str} : « {obj.title} »\n"
            if item.get('quotes'):
                for q in item['quotes']:
                    text += f"    -> EXTRAIT (Page {q.page_number}) : « {q.quote_text} »\n"
            return text

        elif item['type'] == 'event_entry':
            return f"[ {date_str} ] ÉVÉNEMENT : {obj.explanation}\n"

        elif item['type'] == 'photo_entry':
            text = f"[ {date_str} ] PHOTO{label_str} : « {obj.title} »\n"
            
            if hasattr(obj, 'ai_analysis') and obj.ai_analysis:
                analysis_preview = (obj.ai_analysis[:400] + '...') if len(obj.ai_analysis) > 400 else obj.ai_analysis
                analysis_preview = analysis_preview.replace('\n', ' ').replace('\r', '')
                text += f"    -> CONTENU VISUEL/TEXTUEL : {analysis_preview}\n"
            
            elif obj.description:
                 text += f"    -> DESCRIPTION : {obj.description}\n"
                 
            return text
        
        elif item['type'] == 'statement_entry':
            parent_doc = item.get('parent_doc')
            doc_title = parent_doc.title if parent_doc else "Document inconnu"
            text = f"[ {date_str} ] DÉCLARATION{label_str} (Source: {doc_title}) : « {obj.text} »\n"
            return text

        elif item['type'] == 'chat_entry':
            return (
                f"[ {date_str} ] ÉCHANGE CLAVARDAGE{label_str} : « {item['title']} »\n"
                f"{item['content']}\n"
            )

        return f"{date_str} | {label_str} PREUVE : {item.get('content', '')}\n"

    @classmethod
    def format_document_reference(cls, obj, exhibit_label=None):
        """
        Generates the detailed context for the 'Reference' section.
        This contains the full body text, AI analysis, etc.
        """
        header = f"--- PIÈCE {exhibit_label if exhibit_label else 'Non classée'} ---"
        
        if hasattr(obj, 'messages') and hasattr(obj, 'title'):
            all_messages = obj.messages.all()
            participants = sorted(list(set(m.sender.name for m in all_messages if m.sender)))
            participants_str = f"PARTICIPANTS : {', '.join(participants)}\n" if participants else ""

            messages_by_date = defaultdict(list)
            for msg in all_messages:
                if msg.timestamp:
                    messages_by_date[msg.timestamp.date()].append(msg)

            full_transcript = []
            for msg_date in sorted(messages_by_date.keys()):
                full_transcript.append(f"\n--- Conversation du {msg_date.strftime('%d %B %Y')} ---")
                for m in messages_by_date[msg_date]:
                    sender_name = m.sender.name if m.sender else 'Inconnu'
                    timestamp_str = m.timestamp.strftime('%H:%M')
                    full_transcript.append(f"[{timestamp_str}] {sender_name}: {m.text_content}")
            
            return (
                f"{header}\n"
                f"TYPE : Transcription de Clavardage (« {obj.title} »)\n"
                f"{participants_str}"
                f"CONTENU COMPLET :\n{''.join(full_transcript)}\n"
            )

        elif hasattr(obj, 'subject') and hasattr(obj, 'body_plain_text'):
            body_lines = obj.body_plain_text.splitlines() if obj.body_plain_text else []
            cleaned_lines = [line for line in body_lines if not line.strip().startswith('>')]
            cleaned_body = "\n".join(cleaned_lines)

            return (
                f"{header}\n"
                f"TYPE : Courriel complet\n"
                f"DE : {obj.sender}\n"
                f"À : {obj.recipients_to}\n"
                f"DATE : {obj.date_sent}\n"
                f"CONTENU :\n{cleaned_body}\n"
            )
        
        elif hasattr(obj, 'title'):
            doc_type = "Document PDF" if hasattr(obj, 'page_count') else "Photo"
            analysis = getattr(obj, 'ai_analysis', None) or getattr(obj, 'description', '')
            
            return (
                f"{header}\n"
                f"TYPE : {doc_type} (« {obj.title} »)\n"
                f"DESCRIPTION / ANALYSE IA :\n{analysis}\n"
            )
            
        return ""
