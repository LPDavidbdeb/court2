from django.urls import path
from . import views

app_name = 'ai_services'

urlpatterns = [
    path('analyze/<str:doc_type>/<int:pk>/', views.trigger_ai_analysis, name='trigger_analysis'),
    path('clear/<str:doc_type>/<int:pk>/', views.clear_ai_analysis, name='clear_analysis'),
]
