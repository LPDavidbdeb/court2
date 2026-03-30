from django.urls import path
from . import views

app_name = 'case_manager'

urlpatterns = [
    # LegalCase URLs
    path('', views.LegalCaseListView.as_view(), name='case_list'),
    path('create/', views.LegalCaseCreateView.as_view(), name='case_create'),
    path('<int:pk>/', views.LegalCaseDetailView.as_view(), name='case_detail'),
    path('<int:pk>/export/', views.LegalCaseExportView.as_view(), name='case_export'),
    path('<int:pk>/export-police/', views.PoliceComplaintExportView.as_view(), name='case_export_police'),
    path('<int:pk>/export-llm/', views.LegalCaseLLMExportView.as_view(), name='case_export_llm'),
    path('<int:pk>/generate-production/', views.generate_exhibit_production, name='case_generate_production'),
    path('<int:pk>/download-zip/', views.download_exhibits_zip, name='case_download_zip'),
    path('<int:pk>/protagonists/', views.case_protagonists_list, name='case_protagonists'),

    # PerjuryContestation URLs
    path('<int:case_pk>/contestations/create/', views.PerjuryContestationCreateView.as_view(), name='contestation_create'),
    path('contestations/<int:pk>/', views.PerjuryContestationDetailView.as_view(), name='contestation_detail'),
    path('contestations/<int:pk>/update-title/', views.update_contestation_title_ajax, name='update_contestation_title'),
    path('contestations/<int:pk>/manage-narratives/', views.ManageContestationNarrativesView.as_view(), name='manage_narratives'),
    path('contestations/<int:pk>/manage-statements/', views.ManageContestationStatementsView.as_view(), name='manage_statements'),
    
    # AI Suggestion and Debugging URLs
    path('contestations/<int:contestation_pk>/generate-suggestion/', views.generate_ai_suggestion, name='generate_suggestion'),
    path('contestation/<int:contestation_pk>/gen-police/', views.generate_police_report, name='gen_police_report'),
    path('contestations/<int:contestation_pk>/preview/', views.preview_ai_context, name='preview_context'),
    path('contestations/<int:contestation_pk>/preview-police/', views.preview_police_prompt, name='preview_police_prompt'),
    path('suggestions/<int:suggestion_pk>/retry-parse/', views.retry_parse_suggestion, name='retry_parse_suggestion'),
]
