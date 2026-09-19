from django.shortcuts import render, redirect, get_object_or_404
from .models import BlogPost, CaseStudy, LocationPage, Page, SubService, Service, Testimonial
import logging
import re
from django.template import Engine, Context
from admin_app.models import GetTouchWithUs
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


# Home View
def home(request):
    pages = Page.objects.filter(page_tag='home').first()
    recent_posts = BlogPost.objects.filter(is_published=True)[:3]
    testimonials = Testimonial.objects.filter(is_published=True)
    return render(request, 'home/index.html', {
        'pages': pages,
        'recent_posts': recent_posts,
        'testimonials': testimonials,
    })


# Page Detail View (Handles both Service and Page)
def page_detail(request, page_tag):
    logger.debug(f"Requested page_tag: {page_tag}")

    # Determine if the page_tag belongs to a Service or SubService

    service = Service.objects.filter(page__page_tag=page_tag).first()
    subservice = SubService.objects.filter(page__page_tag=page_tag).first()
    pages = Page.objects.filter(page_tag=page_tag).first()
    logger.debug(f"page_detail pages: {pages}")

    if service:
        page = service.page
    elif subservice:
        page = subservice.page
    else:
        page = get_object_or_404(Page, page_tag=page_tag)

    # Load and render the HTML content dynamically via Django's template engine
    django_engine = Engine.get_default()  # Get the default Django template engine
    template = django_engine.from_string(page.page_content)  # Create a template from the HTML content
    rendered_content = template.render(Context({
        'service': service,
        'subservice': subservice,
    }))  # Render the content with context variables

    logger.debug(f"Rendered content: {rendered_content}")

    return render(request, 'home/dynamic_page.html', {
        'rendered_content': rendered_content,
        'pages': pages,
        'service': service,
        'subservice': subservice,
        'parent_service': service,
    })



def subservice_detail(request, service_slug, subservice_slug):
    page_tag = f"{service_slug}/{subservice_slug}"
    subservice = get_object_or_404(SubService, page__page_tag=page_tag)
    page = subservice.page

    # Load and render the HTML content dynamically via Django's template engine
    django_engine = Engine.get_default()  # Get the default Django template engine
    template = django_engine.from_string(page.page_content)  # Create a template from the HTML content
    rendered_content = template.render(Context({
        'subservice': subservice,
        
    }))  # Render the content with context variables
    return render(request, 'home/dynamic_page.html', {
        'rendered_content': rendered_content,
        'pages': page,
        'service_slug': service_slug,
        'subservice_slug': subservice_slug,
        'subservice': subservice,
        'parent_service': subservice.service,
    })


def about(request):
    return render(request, 'home/about.html', {
        'seo_title': 'About Rizen Digital | SEO & Digital Marketing Agency in Kolkata',
        'seo_description': 'Learn about Rizen Digital, a Kolkata-based digital marketing agency helping businesses grow through measurable SEO, PPC, social media, and web development.',
    })


def blog(request):
    posts = BlogPost.objects.filter(is_published=True)
    return render(request, 'home/blogs.html', {
        'posts': posts,
        'seo_title': 'Digital Marketing & SEO Blog | Rizen Digital',
        'seo_description': 'Insights, guides, and strategies on SEO, digital marketing, and web development from the Rizen Digital team.',
    })


def contact(request):
    return render(request, 'home/contact.html', {
        'seo_title': 'Contact Rizen Digital | Get a Free Digital Marketing Consultation',
        'seo_description': 'Get in touch with Rizen Digital for a free consultation on SEO, digital marketing, and web development services in Kolkata.',
    })

def terms_condition(request):
    return render(request, 'home/terms-condition.html', {
        'seo_title': 'Terms & Conditions | Rizen Digital',
        'seo_description': 'Read the terms and conditions for using Rizen Digital\'s website and services.',
    })

def privacy(request):
    return render(request, 'home/privacy-policy.html', {
        'seo_title': 'Privacy Policy | Rizen Digital',
        'seo_description': 'Read Rizen Digital\'s privacy policy to understand how we collect, use, and protect your data.',
    })

def blog_detail(request, page_tag):
    post = get_object_or_404(BlogPost, slug=page_tag, is_published=True)
    recent_posts = BlogPost.objects.filter(is_published=True).exclude(pk=post.pk)[:5]
    word_count = len(re.sub('<[^<]+?>', ' ', post.content).split())
    reading_time = max(1, round(word_count / 200))
    breadcrumb_items = [
        {'name': 'Home', 'url': request.build_absolute_uri('/')},
        {'name': 'Blog', 'url': request.build_absolute_uri(reverse('blog'))},
        {'name': post.title, 'url': request.build_absolute_uri(post.get_absolute_url())},
    ]
    return render(request, 'home/blog-details.html', {
        'post': post,
        'recent_posts': recent_posts,
        'reading_time': reading_time,
        'breadcrumb_items': breadcrumb_items,
        'seo_title': post.meta_title or post.title,
        'seo_description': post.meta_description or post.excerpt,
    })


def case_studies(request):
    studies = CaseStudy.objects.filter(is_published=True)
    return render(request, 'home/case-studies.html', {
        'studies': studies,
        'seo_title': 'Case Studies | Rizen Digital Results for Real Clients',
        'seo_description': 'See how Rizen Digital has helped businesses in Kolkata and beyond grow through SEO, digital marketing, and web development.',
    })


def case_study_detail(request, slug):
    study = get_object_or_404(CaseStudy, slug=slug, is_published=True)
    related_studies = CaseStudy.objects.filter(is_published=True).exclude(pk=study.pk)[:3]
    return render(request, 'home/case-study-detail.html', {
        'study': study,
        'related_studies': related_studies,
        'seo_title': study.meta_title or f'{study.client_name} Case Study | Rizen Digital',
        'seo_description': study.meta_description or study.summary,
    })


def location_detail(request, slug):
    location_page = get_object_or_404(
        LocationPage.objects.select_related('service').prefetch_related('faqs'),
        slug=slug,
        is_published=True,
    )
    return render(request, 'home/location_detail.html', {
        'location_page': location_page,
        'seo_title': location_page.meta_title,
        'seo_description': location_page.meta_description,
    })




def get_in_touch(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name') or request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        company_name = request.POST.get('company_name') or ''
        website_url = request.POST.get('website_url')
        select_service = request.POST.get('select_service')
        subject = request.POST.get('subject') or request.POST.get('msg_subject') or ''
        message = request.POST.get('message') or ''
        
        if full_name and email and phone_number and message:
            lead = GetTouchWithUs(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                company_name=company_name,
                website_url=website_url or None,
                select_service=select_service,
                subject=subject,
                message=message,
            )
            try:
                lead.full_clean()
                lead.save()
            except ValidationError:
                return JsonResponse({'success': False, 'message': 'Please enter a valid email and website URL.'}, status=400)

            try:
                company_display = lead.company_name or '-'
                website_display = lead.website_url or '-'
                service_display = lead.get_select_service_display() if lead.select_service else '-'
                subject_display = lead.subject or '-'
                send_mail(
                    subject=f'New enquiry from {lead.full_name} — Rizen Digital website',
                    message=(
                        f'Name: {lead.full_name}\n'
                        f'Email: {lead.email}\n'
                        f'Phone: {lead.phone_number}\n'
                        f'Company: {company_display}\n'
                        f'Website: {website_display}\n'
                        f'Service: {service_display}\n'
                        f'Subject: {subject_display}\n\n'
                        f'Message:\n{lead.message}'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.LEAD_NOTIFICATION_EMAIL],
                    fail_silently=False,
                )
            except Exception:
                logger.exception('Failed to send lead notification email for lead id=%s', lead.pk)

            return JsonResponse({'success': True, 'message': 'Form submitted successfully!'})
        else:
            return JsonResponse({'success': False, 'message': 'Please fill in your name, email, phone, and message.'}, status=400)
    
    return redirect('contact')








    


