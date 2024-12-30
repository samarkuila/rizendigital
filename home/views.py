from django.shortcuts import render, get_object_or_404
from .models import Page, SubService, Service
import logging
from django.template import Engine, Context

logger = logging.getLogger(__name__)


# Home View
def home(request):
    pages = Page.objects.filter(page_tag='home').first()    
    return render(request, 'home/index.html',{'pages': pages})


# Page Detail View (Handles both Service and Page)
# def page_detail(request, page_tag):
#     logger.debug(f"Requested page_tag: {page_tag}")

#     service = Service.objects.filter(page__page_tag=page_tag).first()
#     subservice = SubService.objects.filter(page__page_tag=page_tag).first()

#     if service:
#         page = service.page
#     elif subservice:
#         page = subservice.page
#     else:
#         page = get_object_or_404(Page, page_tag=page_tag)

#     return render(request, 'home/dynamic_page.html', {
#         'page': page,
#         'service': service,
#         'subservices': subservice,
#     })

def page_detail(request, page_tag):
    logger.debug(f"Requested page_tag: {page_tag}")

    # Determine if the page_tag belongs to a Service or SubService
    service = Service.objects.filter(page__page_tag=page_tag).first()
    subservice = SubService.objects.filter(page__page_tag=page_tag).first()

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
        'page_tag': page_tag,
        'service': service,
        'subservice': subservice,
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

    print(rendered_content )

    return render(request, 'home/dynamic_page.html', {
        'rendered_content': rendered_content,        
        
        'service_slug': service_slug,
        'subservice_slug': subservice_slug,
    })
    


    # return render(request, 'home/dynamic_page.html', {
    #     'page': page,
    #     'subservice': subservice,
    #     'service_slug': service_slug,
    #     'subservice_slug': subservice_slug,
    # })


def about(request):
    return render(request,'home/about.html')

def blog(request):
    print("Blog")
     
     #posts = BlogPost.objects.all()
    return render(request, 'home/blogs.html')  


def contact(request):
    return render(request,'home/contact.html')

def terms_condition(request):
    return render(request,'home/terms-condition.html')

def privacy(request):
    return render(request,'home/privacy-policy.html')

def blog_detail(request, page_tag):
    # post = get_object_or_404(BlogPost, page_tag=page_tag)
    # recent_posts = BlogPost.objects.all().order_by('-created_at')[:5]
    # return render(request, 'home/blog-details.html', {'post': post,'recent_posts':recent_posts})
    return render(request, 'home/blog-details.html')








    


