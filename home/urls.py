from django.urls import path
from . import views
from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

from django.urls import path

urlpatterns = [
    # Static Routes First
    path('', views.home, name='home'),
    path('terms-condition/', views.terms_condition, name='terms_condition'),
    path('privacy-policy/', views.privacy, name='privacy'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('blog/', views.blog, name='blog'),
    path('blog/<str:page_tag>/', views.blog_detail, name='blog-detail'),
    path('digital-marketing/', RedirectView.as_view(url='/', permanent=False), name='digital-marketing'),

    # SubService Dynamic Route
    path('<slug:service_slug>/<slug:subservice_slug>/', views.subservice_detail, name='subservice_detail'),

    # Catch-All Dynamic Route for Pages (Place Last)
    path('<slug:page_tag>/', views.page_detail, name='page_detail'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)