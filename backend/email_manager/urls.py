from django.urls import path
from .views import (
    # Thread Views
    EmailThreadListView,
    EmailThreadDetailView,
    EmailSearchView,
    EmailThreadDeleteView,
    EmailThreadSaveView,
    
    # Email Views
    EmailDetailView,
    DownloadEmlView,
    EmailPrintableView,
    EmlUploadView,
    
    # Quote Views
    QuoteDetailView,
    AddQuoteView,
    QuoteListView,
    QuoteDeleteView,
    QuoteUpdateView,
)

app_name = 'email_manager'

urlpatterns = [
    # Thread URLs
    path('threads/', EmailThreadListView.as_view(), name='thread_list'),
    path('thread/<int:pk>/', EmailThreadDetailView.as_view(), name='thread_detail'),
    path('thread/search/', EmailSearchView.as_view(), name='thread_search'),
    path('thread/<int:pk>/delete/', EmailThreadDeleteView.as_view(), name='thread_delete'),
    path('thread/save/', EmailThreadSaveView.as_view(), name='thread_save'),

    # Email URLs
    path('email/<int:pk>/', EmailDetailView.as_view(), name='email_detail'),
    path('email/<int:pk>/download/', DownloadEmlView.as_view(), name='email_download'),
    path('email/<int:pk>/print/', EmailPrintableView.as_view(), name='email_printable'),
    path('email/upload/', EmlUploadView.as_view(), name='email_upload'),

    # Quote URLs
    path('quotes/', QuoteListView.as_view(), name='quote_list'),
    path('quote/<int:pk>/', QuoteDetailView.as_view(), name='quote_detail'),
    path('quote/add/<int:email_pk>/', AddQuoteView.as_view(), name='add_quote'),
    path('quote/<int:pk>/update/', QuoteUpdateView.as_view(), name='quote_update'),
    path('quote/<int:pk>/delete/', QuoteDeleteView.as_view(), name='quote_delete'),
]
