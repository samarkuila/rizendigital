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
    path('case-studies/', views.case_studies, name='case_studies'),
    path('google-algorithm-updates/', views.google_updates, name='google_updates'),
    path('ai-agents/', views.ai_agents, name='ai_agents'),
    path('ai-agents/scout/', views.scout_demo, name='scout_demo'),
    path('ai-agents/<slug:slug>/', views.agent_demo, name='agent_demo'),
    path('case-studies/<slug:slug>/', views.case_study_detail, name='case_study_detail'),
    path('locations/<slug:slug>/', views.location_detail, name='location_detail'),
    path('digital-marketing/', views.page_detail, {'page_tag': 'digital-marketing'}, name='digital-marketing'),
    path("get-in-touch/", views.get_in_touch, name="get_in_touch"),
    # SubService Dynamic Route
    path('<slug:service_slug>/<slug:subservice_slug>/', views.subservice_detail, name='subservice_detail'),

    # Catch-All Dynamic Route for Pages (Place Last)
    path('<slug:page_tag>/', views.page_detail, name='page_detail'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)