from django.db import models
from document_manager.models import Statement, LibraryNode, Document, DocumentSource
from events.models import Event
from email_manager.models import Quote as EmailQuote
from pdf_manager.models import Quote as PDFQuote
from photos.models import PhotoDocument
from googlechat_manager.models import ChatSequence
from datetime import datetime, date
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

class TrameNarrative(models.Model):
    """
    Construit un dossier d'argumentation qui lie un ensemble de preuves 
    à un ensemble d'allégations cibles, dans le but de les supporter ou 
    de les contredire. This is the 'Evidence Collector'.
    """
    
    class TypeArgument(models.TextChoices):
        CONTRADICTION = 'CONTRADICTION', 'Vise à contredire les allégations'
        SUPPORT = 'SUPPORT', 'Vise à supporter les allégations'

    titre = models.CharField(
        max_length=255, 
        help_text="Un titre descriptif pour ce dossier d'argumentation (ex: 'Preuve de l'implication parentale')."
    )
    resume = models.TextField(
        help_text="Le résumé expliquant comment les preuves assemblées forment un argument cohérent contre (ou pour) les allégations ciblées."
    )
    type_argument = models.CharField(
        max_length=20,
        choices=TypeArgument.choices
    )

    targeted_statements = models.ManyToManyField(
        Statement,
        related_name='narratives_targeting_this_statement',
        blank=True,
        help_text="The specific statements targeted by this narrative."
    )

    # --- L'ensemble des preuves documentaires ---
    source_statements = models.ManyToManyField(
        Statement,
        related_name='narratives_using_this_statement_as_evidence',
        blank=True,
        help_text="Statements from other documents used as evidence."
    )
    evenements = models.ManyToManyField(
        Event,
        blank=True,
        related_name='trames_narratives'
    )
    citations_courriel = models.ManyToManyField(
        EmailQuote,
        blank=True,
        related_name='trames_narratives'
    )
    citations_pdf = models.ManyToManyField(
        PDFQuote,
        blank=True,
        related_name='trames_narratives'
    )
    photo_documents = models.ManyToManyField(
        PhotoDocument,
        blank=True,
        related_name='trames_narratives'
    )
    citations_chat = models.ManyToManyField(
        ChatSequence,
        blank=True,
        related_name='trames_narratives',
        help_text="Sequences of chat messages used as evidence."
    )

    # === NOUVEAUX CHAMPS POUR L'AUDITEUR IA ===
    ai_analysis_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Analyse objective générée par l'IA confrontant preuves vs allégations."
    )
    analysis_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.titre

    def get_chronological_evidence(self):
        timeline = []

        def to_datetime(d):
            if d is None: return None
            if isinstance(d, datetime): return timezone.make_aware(d) if timezone.is_naive(d) else d
            if isinstance(d, date): return timezone.make_aware(datetime.combine(d, datetime.min.time()))
            return None

        # Helper pour récupérer nom ET rôle
        def get_author_info(protagonist, default_name="Auteur inconnu"):
            if protagonist:
                return {
                    'name': protagonist.get_full_name(),
                    'role': protagonist.role
                }
            return {'name': default_name, 'role': ''}

        # 1. PDF Quotes
        for quote in self.citations_pdf.select_related('pdf_document', 'pdf_document__author'):
            auth_info = get_author_info(quote.pdf_document.author if quote.pdf_document else None, "Document officiel")
            doc_date = to_datetime(quote.pdf_document.document_date if quote.pdf_document else None)
            timeline.append({
                'type': 'pdf',
                'date': doc_date,
                'object': quote,
                'content': quote.quote_text,
                'author_name': auth_info['name'],
                'author_role': auth_info['role'],
                'source_title': quote.pdf_document.title if quote.pdf_document else "Document",
                'sort_key': quote.created_at.timestamp() if quote.created_at else 0
            })

        # 2. Emails
        for quote in self.citations_courriel.select_related('email', 'email__sender_protagonist'):
            email_date = to_datetime(quote.email.date_sent if quote.email else None)
            
            name = "Inconnu"
            role = ""
            if quote.email:
                if quote.email.sender_protagonist:
                    name = quote.email.sender_protagonist.get_full_name()
                    role = quote.email.sender_protagonist.role
                else:
                    name = quote.email.sender
                    role = "Expéditeur"

            timeline.append({
                'type': 'email',
                'date': email_date,
                'object': quote,
                'content': quote.quote_text,
                'author_name': name,
                'author_role': role,
                'source_title': f"Objet : {quote.email.subject}",
                'sort_key': email_date.timestamp() if email_date else 0
            })

        # 3. Statements
        statements = self.source_statements.all()
        if statements.exists():
            statement_ct = ContentType.objects.get_for_model(statements.first())
            nodes = LibraryNode.objects.filter(
                content_type=statement_ct,
                object_id__in=statements.values_list('pk', flat=True),
                document__source_type=DocumentSource.REPRODUCED
            ).select_related('document', 'document__author').order_by('path')

            node_map = {node.object_id: node for node in nodes}

            for statement in statements:
                node = node_map.get(statement.pk)
                
                doc_date = None
                name = "Analyse"
                role = ""
                title = "Constat"
                sort_path = ""

                if node:
                    doc = node.document
                    doc_date = doc.document_original_date
                    if doc.author:
                        name = doc.author.get_full_name()
                        role = doc.author.role
                    
                    title = doc.title
                    sort_path = node.path

                timeline.append({
                    'type': 'statement',
                    'date': to_datetime(doc_date),
                    'object': statement,
                    'content': statement.text,
                    'author_name': name,
                    'author_role': role,
                    'source_title': title,
                    'sort_key': sort_path
                })

        # Other evidence types
        for event in self.evenements.all():
            timeline.append({
                'type': 'event',
                'date': to_datetime(event.date),
                'object': event,
                'content': event.explanation,
                'author_name': "Observateur",
                'author_role': "Témoin",
                'source_title': 'Événement',
                'sort_key': ''
            })
            
        for photo in self.photo_documents.all():
             timeline.append({
                'type': 'photo',
                'date': to_datetime(photo.created_at),
                'object': photo,
                'content': photo.title,
                'author_name': "Photographe",
                'author_role': "Preuve Visuelle",
                'source_title': 'Document Photo',
                'sort_key': ''
            })
        
        for seq in self.citations_chat.all():
            timeline.append({
                'type': 'chat',
                'date': to_datetime(seq.start_date),
                'object': seq,
                'content': seq.title,
                'author_name': "Participants",
                'author_role': "Conversation",
                'source_title': 'Conversation',
                'sort_key': ''
            })

        # TRI FINAL :
        # 1. Par Date (Full Timestamp)
        # 2. Par Clé secondaire (Path ou Timestamp)
        # Note: On ne trie plus par 'author_name' en second pour respecter l'ordre chronologique strict (ex: réponses par email le même jour)
        return sorted(
            [item for item in timeline if item['date']], 
            key=lambda x: (x['date'], x.get('sort_key', ''))
        )

    def get_source_documents(self):
        """
        Collecte et retourne une liste unique de tous les documents sources
        (PDFs, Emails, Documents de Statements) référencés dans cette trame.
        """
        source_docs = {}

        # 1. PDF Documents from PDF Quotes
        for quote in self.citations_pdf.select_related('pdf_document'):
            doc = quote.pdf_document
            if doc:
                source_docs[f"pdf-{doc.pk}"] = {
                    'type': 'PDF',
                    'title': doc.title,
                    'url': doc.get_public_url()
                }

        # 2. Emails from Email Quotes
        for quote in self.citations_courriel.select_related('email'):
            email = quote.email
            if email:
                source_docs[f"email-{email.pk}"] = {
                    'type': 'Courriel',
                    'title': email.subject,
                    'url': email.get_public_url()
                }

        # 3. Documents from Statements
        statements = self.source_statements.all()
        if statements.exists():
            statement_ct = ContentType.objects.get_for_model(statements.first())
            nodes = LibraryNode.objects.filter(
                content_type=statement_ct,
                object_id__in=statements.values_list('pk', flat=True),
                document__source_type=DocumentSource.REPRODUCED
            ).select_related('document')

            for node in nodes:
                doc = node.document
                if doc:
                    source_docs[f"document-{doc.pk}"] = {
                        'type': 'Document',
                        'title': doc.title,
                        'url': doc.get_public_url()
                    }
        
        return list(source_docs.values())

    def get_structured_analysis(self):
        if self.ai_analysis_json and 'constats_objectifs' in self.ai_analysis_json:
            return self.ai_analysis_json
        
        return {
            "analyse_id": f"MANUAL-{self.pk}",
            "constats_objectifs": [{
                "fait_identifie": "Résumé narratif (Manuel)",
                "description_factuelle": self.resume,
                "contradiction_directe": "Non spécifié (Mode manuel)"
            }]
        }

    class Meta:
        verbose_name = "Trame Narrative"
        verbose_name_plural = "Trames Narratives"

class PerjuryArgument(models.Model):
    trame = models.OneToOneField(
        TrameNarrative, 
        on_delete=models.CASCADE, 
        related_name='perjury_argument',
        null=True
    )
    text_declaration = models.TextField(verbose_name="1. Déclaration faite sous serment", help_text="Contextualise the lie.", blank=True)
    text_proof = models.TextField(verbose_name="2. Preuve de la fausseté", help_text="Demonstrate why it is false.", blank=True)
    text_mens_rea = models.TextField(verbose_name="3. Connaissance de la fausseté (Mens Rea)", help_text="Demonstrate that they KNEW it was false.", blank=True)
    text_legal_consequence = models.TextField(verbose_name="4. Intention de tromper le tribunal", help_text="What did they hope to gain?", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Argument: {self.trame.titre}"