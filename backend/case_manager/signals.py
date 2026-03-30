from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from argument_manager.models import TrameNarrative
from case_manager.models import PerjuryContestation
from case_manager.services import refresh_case_exhibits
import sys

# List of ManyToMany fields in TrameNarrative that constitute "Evidence"
EVIDENCE_FIELDS = [
    'evenements',
    'citations_courriel',
    'citations_pdf',
    'photo_documents',
    'source_statements',
    'citations_chat',
]

def trigger_case_refresh(narrative):
    """
    Finds all LegalCases linked to this narrative (via PerjuryContestation)
    and refreshes their exhibits.
    """
    # Find all contestations that use this narrative
    linked_contestations = narrative.supported_contestations.all()
    
    # Get unique cases from these contestations
    cases_to_refresh = set(c.case for c in linked_contestations)
    
    for case in cases_to_refresh:
        print(f"Signal: Refreshing exhibits for Case {case.id} due to update in Narrative {narrative.id}")
        refresh_case_exhibits(case.id)

@receiver(m2m_changed, sender=TrameNarrative.evenements.through)
@receiver(m2m_changed, sender=TrameNarrative.citations_courriel.through)
@receiver(m2m_changed, sender=TrameNarrative.citations_pdf.through)
@receiver(m2m_changed, sender=TrameNarrative.photo_documents.through)
@receiver(m2m_changed, sender=TrameNarrative.source_statements.through)
@receiver(m2m_changed, sender=TrameNarrative.citations_chat.through)
def evidence_changed(sender, instance, action, **kwargs):
    """
    Triggered when evidence is added/removed from a TrameNarrative.
    """
    # Prevent signal execution during loaddata
    if 'loaddata' in sys.argv:
        return

    # We only care about actions that change the DB content
    if action in ["post_add", "post_remove", "post_clear"]:
        # 'instance' is the TrameNarrative object being modified
        trigger_case_refresh(instance)

@receiver(m2m_changed, sender=PerjuryContestation.supporting_narratives.through)
def narrative_link_changed(sender, instance, action, **kwargs):
    """
    Triggered when a TrameNarrative is linked/unlinked to a PerjuryContestation.
    """
    # Prevent signal execution during loaddata
    if 'loaddata' in sys.argv:
        return

    if action in ["post_add", "post_remove", "post_clear"]:
        # In this specific m2m relation:
        # If instance is PerjuryContestation, we refresh its case.
        if isinstance(instance, PerjuryContestation):
            refresh_case_exhibits(instance.case.id)
        # If instance is TrameNarrative (reverse relation), we use the helper
        elif isinstance(instance, TrameNarrative):
            trigger_case_refresh(instance)
