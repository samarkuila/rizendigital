from django.urls import path

from . import views

app_name = 'studio'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/search/', views.api_search, name='api_search'),
    path('api/media/', views.api_media, name='api_media'),
    path('api/keyword/', views.api_keyword, name='api_keyword'),
    path('api/links/', views.api_links, name='api_links'),
    path('settings/', views.site_settings, name='settings'),
    path('media/', views.media_library, name='media'),
    path('media/upload/', views.media_upload, name='media_upload'),
    path('media/delete/', views.media_delete, name='media_delete'),
    path('bulk/pages/', views.bulk_pages, name='bulk_pages'),
    path('bulk/pages/template.csv', views.bulk_pages_template, name='bulk_pages_template'),
    path('bulk/locations/', views.bulk_locations, name='bulk_locations'),
    path('<slug:kind>/', views.obj_list, name='list'),
    path('<slug:kind>/new/', views.obj_edit, name='new'),
    path('<slug:kind>/export.csv', views.obj_export, name='export'),
    path('<slug:kind>/bulk-action/', views.obj_bulk, name='bulk'),
    path('<slug:kind>/<int:pk>/', views.obj_edit, name='edit'),
    path('<slug:kind>/<int:pk>/delete/', views.obj_delete, name='delete'),
]
