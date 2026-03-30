from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('ai/', include('ai_services.urls', namespace='ai_services')),
    path('cases/', include('case_manager.urls')),
    path('accounts/', include('allauth.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('events/', include('events.urls')), 
    path('arguments/', include('argument_manager.urls')),
    path('photos/', include('photos.urls')),
    path('emails/', include('email_manager.urls')),
    path('protagonists/', include('protagonist_manager.urls')),
    path('documents/', include('document_manager.urls')),
    path('pdfs/', include('pdf_manager.urls')),
    path('chat/', include('googlechat_manager.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
