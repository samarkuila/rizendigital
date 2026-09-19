"""Which content types Rizen Studio can manage, and how each one is listed."""
from django.urls import reverse

from admin_app.models import GetTouchWithUs
from home.models import BlogPost, CaseStudy, LocationPage, Page, POST_TYPES, Service, SubService, Testimonial


def _date(v):
    return v.strftime('%d %b %Y') if v else '—'


def _page_url(p):
    return '/' if p.page_tag == 'home' else '/%s/' % p.page_tag.strip('/')


def _svc_choices():
    return [(str(s.pk), s.name) for s in Service.objects.order_by('name')]


def _country_choices():
    vals = LocationPage.objects.exclude(country='').values_list('country', flat=True).distinct().order_by('country')
    return [(v, v) for v in vals]


KINDS = {
    'pages': {
        'model': Page, 'label': 'Page', 'plural': 'Pages', 'icon': 'file', 'group': 'Content',
        'blurb': 'Service pages, landing pages and the home page.',
        'title': lambda o: o.page_name, 'subtitle': lambda o: '/' if o.page_tag == 'home' else '/%s/' % o.page_tag,
        'search': ('page_name', 'page_tag', 'page_meta_title', 'page_meta_description'),
        'order': '-post_date_time', 'has_status': False, 'public': _page_url,
        'sortable': {'title': 'page_name', 'date': 'post_date_time', 'type': 'post_type'},
        'columns': [('Type', lambda o: o.post_type.replace('_', ' ')), ('Created', lambda o: _date(o.post_date_time))],
        'filters': [{'param': 'type', 'label': 'Type', 'field': 'post_type', 'choices': lambda: list(POST_TYPES)}],
        'serp': {'title': 'page_meta_title', 'desc': 'page_meta_description', 'slug': 'page_tag'},
    },
    'blog': {
        'model': BlogPost, 'label': 'Blog post', 'plural': 'Blog posts', 'icon': 'pen', 'group': 'Content',
        'blurb': 'Articles that build organic traffic.',
        'title': lambda o: o.title, 'subtitle': lambda o: '/blog/%s/' % o.slug,
        'search': ('title', 'excerpt', 'slug', 'author'),
        'order': '-created_at', 'has_status': True, 'public': lambda o: o.get_absolute_url(),
        'sortable': {'title': 'title', 'date': 'created_at', 'updated': 'updated_at'},
        'columns': [('Author', lambda o: o.author), ('Published', lambda o: _date(o.published_at))],
        'filters': [],
        'serp': {'title': 'meta_title', 'desc': 'meta_description', 'slug': 'slug', 'fallback_title': 'title'},
    },
    'locations': {
        'model': LocationPage, 'label': 'Location page', 'plural': 'Location pages', 'icon': 'pin', 'group': 'Content',
        'blurb': 'Service pages for each city you target.',
        'title': lambda o: '%s in %s' % (o.service.name, o.city), 'subtitle': lambda o: '/locations/%s/' % o.slug,
        'search': ('city', 'country', 'slug', 'headline', 'service__name'),
        'order': 'city', 'has_status': True, 'public': lambda o: o.get_absolute_url(), 'select_related': ('service',),
        'sortable': {'title': 'city', 'date': 'created_at', 'updated': 'updated_at'},
        'columns': [('Country', lambda o: o.country or '—'), ('Updated', lambda o: _date(o.updated_at))],
        'filters': [
            {'param': 'service', 'label': 'Service', 'field': 'service_id', 'choices': _svc_choices},
            {'param': 'country', 'label': 'Country', 'field': 'country', 'choices': _country_choices},
        ],
        'serp': {'title': 'meta_title', 'desc': 'meta_description', 'slug': 'slug'},
    },
    'cases': {
        'model': CaseStudy, 'label': 'Case study', 'plural': 'Case studies', 'icon': 'trophy', 'group': 'Content',
        'blurb': 'Proof of results for prospects.',
        'title': lambda o: o.client_name, 'subtitle': lambda o: '/case-studies/%s/' % o.slug,
        'search': ('client_name', 'industry', 'summary', 'slug'),
        'order': '-created_at', 'has_status': True, 'public': lambda o: o.get_absolute_url(), 'select_related': ('service',),
        'sortable': {'title': 'client_name', 'date': 'created_at'},
        'columns': [('Industry', lambda o: o.industry or '—'), ('Service', lambda o: o.service.name if o.service else '—')],
        'filters': [{'param': 'service', 'label': 'Service', 'field': 'service_id', 'choices': _svc_choices}],
        'serp': {'title': 'meta_title', 'desc': 'meta_description', 'slug': 'slug', 'fallback_title': 'client_name'},
    },
    'testimonials': {
        'model': Testimonial, 'label': 'Testimonial', 'plural': 'Testimonials', 'icon': 'quote', 'group': 'Content',
        'blurb': 'Client quotes shown on the home page.',
        'title': lambda o: o.client_name, 'subtitle': lambda o: (o.role + (' · ' + o.company_name if o.company_name else '')) or '',
        'search': ('client_name', 'company_name', 'quote'),
        'order': 'order', 'has_status': True, 'public': None,
        'sortable': {'title': 'client_name', 'date': 'created_at', 'order': 'order'},
        'columns': [('Order', lambda o: str(o.order)), ('Added', lambda o: _date(o.created_at))],
        'filters': [],
    },
    'services': {
        'model': Service, 'label': 'Service', 'plural': 'Services', 'icon': 'layers', 'group': 'Content',
        'blurb': 'Top-level services (each gets its own page).',
        'title': lambda o: o.name, 'subtitle': lambda o: '/%s/' % (o.page.page_tag if o.page else ''),
        'search': ('name', 'description'), 'order': 'name', 'has_status': False,
        'public': lambda o: _page_url(o.page) if o.page else None, 'select_related': ('page',),
        'sortable': {'title': 'name'},
        'columns': [('Sub-services', lambda o: str(o.subservices.count())), ('Location pages', lambda o: str(o.location_pages.count()))],
        'filters': [],
    },
    'subservices': {
        'model': SubService, 'label': 'Sub-service', 'plural': 'Sub-services', 'icon': 'layers', 'group': 'Content',
        'blurb': 'Pages that sit under a service.',
        'title': lambda o: o.name, 'subtitle': lambda o: '/%s/' % (o.page.page_tag if o.page else ''),
        'search': ('name', 'description', 'service__name'), 'order': 'service__name', 'has_status': False,
        'public': lambda o: o.get_absolute_url() if o.page else None, 'select_related': ('service', 'page'),
        'sortable': {'title': 'name'},
        'columns': [('Service', lambda o: o.service.name)],
        'filters': [{'param': 'service', 'label': 'Service', 'field': 'service_id', 'choices': _svc_choices}],
    },
    'leads': {
        'model': GetTouchWithUs, 'label': 'Enquiry', 'plural': 'Enquiries', 'icon': 'mail', 'group': 'Inbox',
        'blurb': 'Messages from your contact forms.',
        'title': lambda o: o.full_name, 'subtitle': lambda o: o.email,
        'search': ('full_name', 'email', 'phone_number', 'company_name', 'message'),
        'order': '-added_date_time', 'has_status': False, 'public': None, 'readonly': True,
        'sortable': {'title': 'full_name', 'date': 'added_date_time'},
        'columns': [('Service', lambda o: o.get_select_service_display() or '—'), ('Phone', lambda o: o.phone_number), ('Received', lambda o: o.added_date_time.strftime('%d %b %Y, %H:%M'))],
        'filters': [{'param': 'service', 'label': 'Service', 'field': 'select_service', 'choices': lambda: list(GetTouchWithUs.SERVICE_CHOICES)}],
    },
}


def urls_for(kind, obj):
    return {
        'edit': reverse('studio:edit', args=[kind, obj.pk]),
        'delete': reverse('studio:delete', args=[kind, obj.pk]),
    }
