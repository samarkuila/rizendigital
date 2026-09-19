from django.contrib import admin
from django.urls import re_path
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from django.views.generic.base import TemplateView
from home import views
from home.sitemaps import BlogSitemap, CaseStudySitemap, LocationSitemap, PageSitemap, StaticViewSitemap


urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('admin/', admin.site.urls),
    path('', include('home.urls')),    
    path('sitemap.xml', sitemap, {
        'sitemaps': {
            'static': StaticViewSitemap,
            'pages': PageSitemap,
            'blogs': BlogSitemap,
            'case_studies': CaseStudySitemap,
            'locations': LocationSitemap,
        },
    }, name='sitemap'),
    path("robots.txt", TemplateView.as_view(template_name="home/robots.txt", content_type="text/plain")),
    path("llms.txt", TemplateView.as_view(template_name="home/llms.txt", content_type="text/plain")),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)