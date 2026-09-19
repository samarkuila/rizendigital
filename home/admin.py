from django.contrib import admin
from .models import BlogPost, CaseStudy, LocationPage, LocationFAQ, Service, SubService, Page, Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'company_name', 'role', 'is_published', 'order')
    list_filter = ('is_published',)
    search_fields = ('client_name', 'company_name', 'quote')
    list_editable = ('order', 'is_published')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_at', 'is_published')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'industry', 'service', 'is_published', 'published_at')
    list_filter = ('is_published', 'industry', 'service')
    search_fields = ('client_name', 'summary', 'challenge', 'solution', 'results')
    prepopulated_fields = {'slug': ('client_name',)}
    autocomplete_fields = ('service',)


class LocationFAQInline(admin.TabularInline):
    model = LocationFAQ
    extra = 1


@admin.register(LocationPage)
class LocationPageAdmin(admin.ModelAdmin):
    list_display = ('city', 'country', 'service', 'is_published', 'updated_at')
    list_filter = ('is_published', 'country', 'city', 'service')
    search_fields = ('city', 'country', 'headline', 'content')
    prepopulated_fields = {'slug': ('city',)}
    inlines = [LocationFAQInline]


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
