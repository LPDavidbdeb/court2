from .model_views import (
    ProtagonistListView,
    ProtagonistDetailView,
    ProtagonistUpdateView,
    ProtagonistDeleteView,
    ProtagonistEmailCreateView,
    ProtagonistEmailUpdateView,
    ProtagonistEmailDeleteView,
    MergeProtagonistView,
)
from .ProtagonistCreateWithEmailsView import ProtagonistCreateWithEmailsView
from .ajax_views import search_protagonists_ajax, update_protagonist_role_ajax, update_protagonist_linkedin_ajax

__all__ = [
    'ProtagonistListView',
    'ProtagonistDetailView',
    'ProtagonistUpdateView',
    'ProtagonistDeleteView',
    'ProtagonistEmailCreateView',
    'ProtagonistEmailUpdateView',
    'ProtagonistEmailDeleteView',
    'ProtagonistCreateWithEmailsView',
    'search_protagonists_ajax',
    'update_protagonist_role_ajax',
    'update_protagonist_linkedin_ajax',
    'MergeProtagonistView',
]
