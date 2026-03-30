from django.urls import path
from . import views

app_name = 'googlechat'

urlpatterns = [
    path('stream/', views.single_chat_stream, name='chat_stream'),
    path('api/load_more_messages/', views.load_more_messages, name='load_more_messages'),
    
    # CRUD URLs for Chat Sequences
    path('sequences/', views.chat_sequence_list, name='sequence_list'),
    path('sequences/<int:pk>/', views.chat_sequence_detail, name='sequence_detail'),
    path('api/create_sequence/', views.create_sequence_ajax, name='create_sequence_ajax'),
    path('api/sequences/<int:pk>/update/', views.update_sequence_ajax, name='update_sequence_ajax'), # New update view
    path('sequences/<int:pk>/delete/', views.delete_sequence, name='delete_sequence'),
]