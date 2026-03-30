from django.urls import path
from .views import new_views, produced_views, library_node_ajax, ajax_views

app_name = 'document_manager'

urlpatterns = [
    # Document List and Detail Views
    path('list/', new_views.new_document_list_view, name='document_list'),
    path('detail/<int:pk>/', new_views.new_document_detail_view, name='document_detail'),
    path('update/<int:pk>/', new_views.DocumentUpdateView.as_view(), name='document_update'),
    path('interactive/<int:pk>/', new_views.new_interactive_detail_view, name='interactive_detail'),
    path('clean/<int:pk>/', new_views.new_clean_detail_view, name='clean_detail'),
    path('perjury-elements/', new_views.NewPerjuryElementListView.as_view(), name='perjury_element_list'),
    path('cinematic/<int:pk>/', new_views.reproduced_cinematic_view, name='reproduced_cinematic_view'),

    # Produced (Manually Created) Document Workflow
    path('produced/', produced_views.ProducedDocumentListView.as_view(), name='produced_list'),
    path('produced/create/', produced_views.ProducedDocumentCreateView.as_view(), name='produced_create'),
    path('produced/editor/<int:pk>/', produced_views.ProducedDocumentEditorView.as_view(), name='produced_editor'),
    
    # AJAX Endpoints
    path('ajax/author-search/', new_views.author_search_view, name='author_search'),
    path('ajax/update-statement-flags/', ajax_views.update_statement_flags, name='update_statement_flags'),
    path('ajax/analyze/<str:doc_type>/<int:pk>/', ajax_views.trigger_ai_analysis, name='trigger_ai_analysis'),
    path('ajax/correct-text/', ajax_views.ajax_correct_text_with_ai, name='ajax_correct_text_with_ai'),
    path('ajax/get-persona-prompt/', ajax_views.get_ai_persona_prompt, name='get_ai_persona_prompt'),
    path('ajax/library-node/add/<int:document_pk>/', library_node_ajax.add_library_node_ajax, name='add_library_node_ajax'),
    path('ajax/search-evidence/', library_node_ajax.search_evidence_ajax, name='search_evidence_ajax'),
    path('ajax/produced/add-node/<int:node_pk>/', produced_views.ajax_add_node, name='ajax_add_node'),
    path('ajax/produced/edit-node/<int:node_pk>/', produced_views.ajax_edit_node, name='ajax_edit_node'),
    path('ajax/produced/delete-node/<int:node_pk>/', produced_views.ajax_delete_node, name='ajax_delete_node'),
]
