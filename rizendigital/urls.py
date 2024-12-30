from django.contrib import admin
from django.urls import re_path
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from django.views.generic.base import TemplateView
from home import views
from django.conf.urls import handler404



urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('admin/', admin.site.urls),
    path('', include('home.urls')),    
    path("robots.txt", TemplateView.as_view(template_name="home/robots.txt", content_type="text/plain")),    
    
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)