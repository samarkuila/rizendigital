from django.conf import settings
from .models import Service, SubService

def canonical_url(request):
    """Absolute URL for the current path, stripped of query strings (UTM tags,
    pagination params, etc.) so tracking links don't create duplicate canonical
    targets."""
    return {'canonical_url': request.build_absolute_uri(request.path)}


def services_and_subservices(request):
    services = Service.objects.all().prefetch_related('subservices')
    return {
        'services': services,
    }


def breadcrumbs(request):
    """Build a generic BreadcrumbList from the request path for JSON-LD."""
    base_url = request.build_absolute_uri('/').rstrip('/')
    path = request.path.strip('/')

    items = [{'name': 'Home', 'url': f'{base_url}/'}]
    if path:
        segments = path.split('/')
        accumulated = ''
        for segment in segments:
            accumulated += f'/{segment}'
            name = segment.replace('-', ' ').title()
            items.append({'name': name, 'url': f'{base_url}{accumulated}/'})

    if len(items) < 2:
        return {'breadcrumb_items': None}

    return {'breadcrumb_items': items}


def site_contact(request):
    """Phone and social links from settings; templates show them only if set."""
    social = {k: v for k, v in settings.SITE_SOCIAL_LINKS.items() if v}
    phone = settings.SITE_PHONE
    return {
        'site_phone': phone,
        'site_phone_display': phone,
        'site_social': social,
        'site_same_as': list(social.values()),
    }
