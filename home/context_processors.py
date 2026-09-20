import re
from urllib.parse import quote

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
    """Public contact details: values saved in Rizen Studio win over the environment defaults."""
    try:
        from studio.models import SiteSettings
        db = SiteSettings.as_dict()
    except Exception:  # table not migrated yet, or DB unavailable
        db = {}
    phone = db.get('phone') or settings.SITE_PHONE
    social = {}
    for key, env_value in settings.SITE_SOCIAL_LINKS.items():
        value = db.get(key) or env_value
        if value:
            social[key] = value
    wa_digits = re.sub(r'\D', '', settings.SITE_WHATSAPP or phone or '')
    wa_message = quote('Hi Rizen Digital, I would like to know more about your services.')
    return {
        'site_whatsapp_url': 'https://wa.me/%s?text=%s' % (wa_digits, wa_message) if wa_digits else '',
        'site_phone': phone,
        'site_phone_display': phone,
        'site_email': db.get('email') or 'admin@rizendigital.com',
        'site_address': db.get('address') or 'Kolkata, West Bengal, India',
        'site_social': social,
        'ga_id': settings.SITE_GA_ID,
        'site_same_as': list(social.values()),
    }
