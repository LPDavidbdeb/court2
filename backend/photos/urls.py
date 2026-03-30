# your_project_root/photos/urls.py

from django.urls import path
from .views.photo import (
    PhotoListView,
    PhotoUploadView,
    PhotoCreateView,
    photo_processing_view,
    bulk_delete_photos,
    import_single_photo_view,
    timeline_entry_view,
    DayTimelineView,
    PhotoDetailView,
    PhotoUpdateView,
    PhotoDeleteView,
)
from .views.photodocument import (
    PhotoDocumentSingleUploadView,
    PhotoDocumentListView,
    PhotoDocumentDetailView,
    PhotoDocumentCreateView,
    PhotoDocumentUpdateView,
    PhotoDocumentDeleteView,
    author_search_view,
    add_protagonist_view,
    ajax_update_description,
)

app_name = 'photos'

urlpatterns = [
    # Photo URLs
    path('', PhotoListView.as_view(), name='list'),
    path('upload/', PhotoUploadView.as_view(), name='upload'),
    path('create/', PhotoCreateView.as_view(), name='create'),
    path('processing/', photo_processing_view, name='processing'),
    path('bulk_delete/', bulk_delete_photos, name='bulk_delete'),
    path('import_single_photo/', import_single_photo_view, name='import_single_photo'),
    path('timeline/', timeline_entry_view, name='timeline_entry'),
    path('timeline/<int:year>/<int:month>/<int:day>/', DayTimelineView.as_view(), name='day_timeline'),
    path('<int:pk>/', PhotoDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', PhotoUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', PhotoDeleteView.as_view(), name='delete'),

    # Photo Document URLs
    path('documents/', PhotoDocumentListView.as_view(), name='document_list'),
    path('document/create/', PhotoDocumentSingleUploadView.as_view(), name='document_create'), # New primary create view
    path('document/group/', PhotoDocumentCreateView.as_view(), name='document_group'), # Old view for grouping
    path('document/<int:pk>/', PhotoDocumentDetailView.as_view(), name='document_detail'),
    path('document/<int:pk>/update/', PhotoDocumentUpdateView.as_view(), name='document_update'),
    path('document/<int:pk>/delete/', PhotoDocumentDeleteView.as_view(), name='document_delete'),

    # AJAX URLs
    path('ajax/author-search/', author_search_view, name='author_search'),
    path('ajax/add-protagonist/', add_protagonist_view, name='add_protagonist'),
    path('document/<int:pk>/ajax_update_description/', ajax_update_description, name='ajax_update_description'),
]
