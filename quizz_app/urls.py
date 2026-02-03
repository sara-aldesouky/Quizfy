"""
URL configuration for quizz_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import Http404
import os


def safe_serve_media(request, path, document_root=None):
    """Serve media files, return 404 if file doesn't exist (instead of 500)"""
    if document_root is None:
        document_root = settings.MEDIA_ROOT
    
    # Check if file exists
    full_path = os.path.join(document_root, path)
    if not os.path.exists(full_path):
        raise Http404(f"Media file not found: {path}")
    
    return serve(request, path, document_root=document_root)


urlpatterns = [
    path('admin/', admin.site.urls),
    path("",include("quizzes.urls")),
]

# Serve media files - needed for both DEBUG and production
# In production with Cloudinary, files uploaded AFTER Cloudinary setup will have Cloudinary URLs
# but files uploaded BEFORE need local serving fallback
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', safe_serve_media, {'document_root': settings.MEDIA_ROOT}),
]

# Additional static serving in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
