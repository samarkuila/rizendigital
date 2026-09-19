from django.contrib import admin
from .models import GetTouchWithUs

@admin.register(GetTouchWithUs)
class GetTouchWithUsAdmin(admin.ModelAdmin):
    # Optional: Customize the admin panel display
    list_display = ('full_name', 'email', 'phone_number', 'subject', 'select_service', 'added_date_time')
    search_fields = ('full_name', 'email', 'phone_number', 'subject', 'message', 'select_service')
    list_filter = ('select_service', 'added_date_time')
