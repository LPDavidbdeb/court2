from django.urls import path
from . import views

app_name = 'protagonist_manager'

urlpatterns = [
    # Protagonist list and detail
    path('', views.ProtagonistListView.as_view(), name='protagonist_list'),
    path('<int:pk>/', views.ProtagonistDetailView.as_view(), name='protagonist_detail'),

    # Protagonist CRUD
    path('create/', views.ProtagonistCreateWithEmailsView.as_view(), name='protagonist_create'),
    path('<int:pk>/update/', views.ProtagonistUpdateView.as_view(), name='protagonist_update'),
    path('<int:pk>/delete/', views.ProtagonistDeleteView.as_view(), name='protagonist_delete'),

    # ProtagonistEmail CRUD
    path('<int:protagonist_pk>/add-email/', views.ProtagonistEmailCreateView.as_view(), name='add_email'),
    path('email/<int:pk>/update/', views.ProtagonistEmailUpdateView.as_view(), name='update_email'),
    path('email/<int:pk>/delete/', views.ProtagonistEmailDeleteView.as_view(), name='delete_email'),

    # AJAX views
    path('ajax/search/', views.search_protagonists_ajax, name='search_protagonists_ajax'),
    path('ajax/update-role/', views.update_protagonist_role_ajax, name='update_protagonist_role'),
    path('ajax/update-linkedin/', views.update_protagonist_linkedin_ajax, name='update_protagonist_linkedin'),
    
    # Merge view
    path('merge/', views.MergeProtagonistView.as_view(), name='merge_protagonist'),
]
