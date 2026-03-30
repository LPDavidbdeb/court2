from django.urls import path
from . import views

app_name = 'argument_manager'

urlpatterns = [
    path('', views.TrameNarrativeListView.as_view(), name='list'),
    path('grouped/', views.grouped_narrative_view, name='grouped-list'),
    path('<int:pk>/', views.TrameNarrativeDetailView.as_view(), name='detail'),
    path('create/', views.TrameNarrativeCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.TrameNarrativeUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.TrameNarrativeDeleteView.as_view(), name='delete'),
    path('<int:pk>/affidavit/', views.affidavit_generator_view, name='affidavit_generator'),

    # New URLs for the "Sidecar" model
    path('narrative/<int:narrative_pk>/manage-perjury/', views.manage_perjury_argument, name='manage_perjury'),
    path('perjury-argument/<int:pk>/update/', views.PerjuryArgumentUpdateView.as_view(), name='perjury_update'),

    # AJAX handlers
    path('<int:narrative_pk>/ajax_update_summary/', views.ajax_update_summary, name='ajax_update_summary'),
    path('<int:narrative_pk>/ajax_remove_evidence/', views.ajax_remove_evidence, name='ajax_remove_evidence'),
    path('<int:narrative_pk>/ajax_remove_allegation/', views.ajax_remove_allegation, name='ajax_remove_allegation'),
    path('ajax/get-statements-list/', views.ajax_get_statements_list, name='ajax_get_statements_list'),
    path('<int:narrative_pk>/ajax_update_narrative_statements/', views.ajax_update_narrative_statements, name='ajax_update_narrative_statements'),
    path('<int:narrative_pk>/ajax/add-email-quote/', views.ajax_add_email_quote, name='ajax_add_email_quote'),
    path('ajax/get-email-quotes-list/', views.ajax_get_email_quotes_list, name='ajax_get_email_quotes_list'),
    path('<int:narrative_pk>/ajax_update_email_quotes/', views.ajax_update_narrative_email_quotes, name='ajax_update_narrative_email_quotes'),
    path('ajax/get-email-threads/', views.ajax_get_email_threads, name='ajax_get_email_threads'),
    path('ajax/get-thread-emails/<int:thread_pk>/', views.ajax_get_thread_emails, name='ajax_get_thread_emails'),
    path('ajax/get-events-list/', views.ajax_get_events_list, name='ajax_get_events_list'),
    path('<int:narrative_pk>/ajax_update_events/', views.ajax_update_narrative_events, name='ajax_update_narrative_events'),
    path('ajax/get-pdf-quotes-list/', views.ajax_get_pdf_quotes_list, name='ajax_get_pdf_quotes_list'),
    path('<int:narrative_pk>/ajax_update_pdf_quotes/', views.ajax_update_narrative_pdf_quotes, name='ajax_update_narrative_pdf_quotes'),
    path('ajax/get-source-pdfs/', views.ajax_get_source_pdfs, name='ajax_get_source_pdfs'),
    path('<int:narrative_pk>/ajax/add-pdf-quote/', views.ajax_add_pdf_quote, name='ajax_add_pdf_quote'),
    path('ajax/get-pdf-viewer/<int:doc_pk>/', views.ajax_get_pdf_viewer, name='ajax_get_pdf_viewer'),
    path('ajax/pdf-quotes-for-tinymce/', views.pdf_quote_list_for_tinymce, name='pdf_quote_list_for_tinymce'),
    path('ajax/all-quotes-for-tinymce/', views.all_quotes_list_for_tinymce, name='all_quotes_list_for_tinymce'),
    path('<int:narrative_pk>/ajax_get_photo_documents/', views.ajax_get_photo_documents, name='ajax_get_photo_documents'),
    path('<int:narrative_pk>/ajax_associate_photo_documents/', views.ajax_associate_photo_documents, name='ajax_associate_photo_documents'),
    
    # New Chat Sequence AJAX URLs
    path('<int:narrative_pk>/ajax_get_chat_sequences/', views.ajax_get_chat_sequences_list, name='ajax_get_chat_sequences'),
    path('<int:narrative_pk>/ajax_update_chat_sequences/', views.ajax_update_narrative_chat_sequences, name='ajax_update_chat_sequences'),
    
    # New Audit URL
    path('narrative/<int:pk>/audit/', views.ajax_run_narrative_audit, name='ajax_run_audit'),
]
