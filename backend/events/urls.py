from django.urls import path
from . import views

app_name = 'events'  # This defines the namespace

urlpatterns = [
    path('', views.EventListView.as_view(), name='list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='detail'),
    path('create/', views.EventCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.EventUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='delete'),
    # ADDED: URL for the AJAX explanation update
    path('<int:pk>/ajax_update_explanation/', views.ajax_update_explanation, name='ajax_update_explanation'),
]
