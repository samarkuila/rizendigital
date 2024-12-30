from django.contrib import admin
from .models import Service, SubService, Page


# Register Service Model
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


# Register SubService Model
@admin.register(SubService)
class SubServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'description', 'page')
    search_fields = ('name', 'service__name')
    list_filter = ('service',)
    autocomplete_fields = ('service', 'page')


# Register Page Model (If not already registered)
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('page_name', 'post_type', 'post_date_time')
    search_fields = ('page_name', 'post_type')
