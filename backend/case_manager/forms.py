from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from .models import LegalCase, PerjuryContestation
# Make sure to import DocumentSource here
from document_manager.models import Statement, LibraryNode, DocumentSource
from argument_manager.models import TrameNarrative

class LegalCaseForm(forms.ModelForm):
    class Meta:
        model = LegalCase
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Divorce Proceedings 2025'}),
        }

class PerjuryContestationNarrativeForm(forms.ModelForm):
    class Meta:
        model = PerjuryContestation
        fields = ['supporting_narratives']
        widgets = {
            'supporting_narratives': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supporting_narratives'].queryset = TrameNarrative.objects.all().order_by('titre')
        self.fields['supporting_narratives'].label = "Select Supporting Narratives"

class PerjuryContestationStatementsForm(forms.ModelForm):
    class Meta:
        model = PerjuryContestation
        fields = ['targeted_statements']
        widgets = {
            'targeted_statements': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['targeted_statements'].queryset = Statement.objects.filter(is_true=False, is_falsifiable=True)
        self.fields['targeted_statements'].label = "Select Targeted Statements"


class PerjuryContestationForm(forms.ModelForm):
    class Meta:
        model = PerjuryContestation
        fields = ['title', 'targeted_statements', 'supporting_narratives']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            # The CheckboxSelectMultiple widget is used for manual rendering in the template
            'targeted_statements': forms.CheckboxSelectMultiple,
            'supporting_narratives': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ---------------------------------------------------------
        # 1. INTEGRITY FILTER: EXCLUDE ALREADY CONTESTED ALLEGATIONS
        # ---------------------------------------------------------
        base_qs = Statement.objects.filter(is_true=False, is_falsifiable=True)
        
        # The filter for already contested allegations has been removed.
        self.fields['targeted_statements'].queryset = base_qs

        # ---------------------------------------------------------
        # 2. PREPARE SUPPORTING NARRATIVES
        # ---------------------------------------------------------
        self.fields['supporting_narratives'].queryset = TrameNarrative.objects.all().order_by('titre')

        # ---------------------------------------------------------
        # 3. GROUPING LOGIC: BY "REPRODUCED" DOCUMENT ONLY
        # ---------------------------------------------------------
        self.statements_by_doc = {}
        
        # Get the final list of available allegations
        available_statements = self.fields['targeted_statements'].queryset
        
        if available_statements.exists():
            ct = ContentType.objects.get_for_model(Statement)
            
            # --- THE CRUCIAL CHANGE IS HERE ---
            # We search for LibraryNodes that link these statements, BUT...
            # We only keep those whose parent document is of type 'REPRODUCED'.
            # This eliminates working documents ("PRODUCED") from the grouping equation.
            nodes = LibraryNode.objects.filter(
                content_type=ct, 
                object_id__in=available_statements.values_list('id', flat=True),
                document__source_type=DocumentSource.REPRODUCED 
            ).select_related('document')

            # Create a dictionary: Allegation ID -> REPRODUCED Document Object
            stmt_to_doc = {node.object_id: node.document for node in nodes}

            for stmt in available_statements:
                # Try to find the original source document
                doc = stmt_to_doc.get(stmt.id)
                
                if doc:
                    # If found, use the title of the original document (e.g., "Requete")
                    doc_title = doc.title
                else:
                    # If the allegation ONLY exists in a produced document (rare but possible)
                    # We put it in a separate group to avoid polluting the display
                    doc_title = "Internal / Unclassified Documents (Source not found)"
                
                if doc_title not in self.statements_by_doc:
                    self.statements_by_doc[doc_title] = []
                self.statements_by_doc[doc_title].append(stmt)
