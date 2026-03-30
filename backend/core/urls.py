from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('story/<int:pk>/', views.story_scrollytelling_view, name='story_detail'),
    path('histoire/cinematique/<int:pk>/', views.story_cinematic_view, name='story_cinematic'),
    
    # Public Document Views
    path('pdf/<int:pk>/', views.pdf_document_public_view, name='pdf_document_public'),
    path('email/<int:pk>/', views.email_public_view, name='email_public'),
    path('document/<int:pk>/', views.document_public_view, name='document_public'),
    
    # Global Evidence Timeline
    path('evidence/global/generate/', views.GenerateGlobalTimelineView.as_view(), name='generate_global_timeline'),
    
    # Semantic Search
    path('semantic-search/', views.semantic_search_view, name='semantic_search'),
]
