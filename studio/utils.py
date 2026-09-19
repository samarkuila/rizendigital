"""Access control, SEO scoring and upload validation for Rizen Studio."""
import functools
import re

from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode

from .bulk import words

MAX_UPLOAD = 8 * 1024 * 1024
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif'}


def staff_required(view):
    """Only signed-in staff users may use Studio; everyone else goes to the Studio login."""
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not (user.is_authenticated and user.is_active and user.is_staff):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/studio/api/'):
                return HttpResponseForbidden('Sign in required')
            return redirect('%s?%s' % (reverse('studio:login'), urlencode({'next': request.get_full_path()})))
        response = view(request, *args, **kwargs)
        response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
        response['Cache-Control'] = 'no-store'
        return response
    return wrapper


def sniff_image(head, ext):
    """Check the file's real signature matches an allowed image type (no SVG: it can carry scripts)."""
    if head.startswith(b'\xff\xd8\xff'):
        return ext in ('.jpg', '.jpeg')
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return ext == '.png'
    if head[:6] in (b'GIF87a', b'GIF89a'):
        return ext == '.gif'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return ext == '.webp'
    if head[4:12] in (b'ftypavif', b'ftypavis'):
        return ext == '.avif'
    return False


def validate_image(upload):
    name = (upload.name or '').lower()
    ext = '.' + name.rsplit('.', 1)[-1] if '.' in name else ''
    if ext not in IMAGE_EXTS:
        raise ValidationError('Upload a JPG, PNG, WebP, GIF or AVIF image.')
    if upload.size > MAX_UPLOAD:
        raise ValidationError('Image is larger than 8 MB.')
    head = upload.read(16)
    upload.seek(0)
    if not sniff_image(head, ext):
        raise ValidationError('This file does not look like a real %s image.' % ext.strip('.').upper())
    return upload


# ------------------------------------------------------------------ SEO scoring
def _issue(issues, cond, penalty, text, level='warn'):
    if cond:
        issues.append({'text': text, 'level': level, 'penalty': penalty})


def _finish(issues):
    score = max(0, 100 - sum(i['penalty'] for i in issues))
    return {'score': score, 'issues': issues, 'grade': 'good' if score >= 85 else 'ok' if score >= 60 else 'bad'}


def seo_page(p):
    i = []
    t, d = (p.page_meta_title or '').strip(), (p.page_meta_description or '').strip()
    _issue(i, not t, 25, 'Missing meta title', 'bad')
    _issue(i, t and not 30 <= len(t) <= 60, 8, 'Meta title works best at 30–60 characters (now %d)' % len(t))
    _issue(i, not d, 25, 'Missing meta description', 'bad')
    _issue(i, d and not 70 <= len(d) <= 160, 8, 'Meta description works best at 70–160 characters (now %d)' % len(d))
    wc = words(p.page_content)
    _issue(i, wc < 150, 15, 'Thin content: only %d words' % wc)
    _issue(i, not (p.page_meta_keyword or '').strip(), 3, 'No meta keywords')
    _issue(i, p.image and not (p.image_alt or '').strip(), 5, 'Image has no alt text')
    return _finish(i)


def seo_blog(b):
    i = []
    t, d = (b.meta_title or b.title or '').strip(), (b.meta_description or '').strip()
    _issue(i, not (b.meta_title or '').strip(), 8, 'No custom meta title (the post title is used)')
    _issue(i, t and len(t) > 60, 8, 'Meta title over 60 characters')
    _issue(i, not d, 20, 'Missing meta description', 'bad')
    _issue(i, d and not 70 <= len(d) <= 160, 6, 'Meta description works best at 70–160 characters (now %d)' % len(d))
    wc = words(b.content)
    _issue(i, wc < 300, 15, 'Short article: %d words' % wc)
    _issue(i, not b.featured_image, 8, 'No featured image')
    _issue(i, not (b.excerpt or '').strip(), 10, 'No excerpt')
    return _finish(i)


def seo_location(l):
    i = []
    t, d = (l.meta_title or '').strip(), (l.meta_description or '').strip()
    _issue(i, not t, 25, 'Missing meta title', 'bad')
    _issue(i, not d, 25, 'Missing meta description', 'bad')
    _issue(i, d and len(d) > 160, 6, 'Meta description over 160 characters')
    wc = words(l.content)
    _issue(i, wc < 120, 15, 'Thin content: only %d words' % wc)
    try:
        nfaq = l.faqs.count()
    except Exception:
        nfaq = 0
    _issue(i, nfaq == 0, 8, 'No FAQs')
    _issue(i, not l.map_embed_url, 3, 'No map embed')
    return _finish(i)


def seo_case(c):
    i = []
    _issue(i, not (c.meta_description or '').strip(), 20, 'Missing meta description', 'bad')
    _issue(i, not (c.metric_1_value or '').strip(), 8, 'No headline metric')
    _issue(i, not c.featured_image, 8, 'No featured image')
    _issue(i, words(c.results) < 25, 10, 'Results section is very short')
    return _finish(i)


SEO_FUNCS = {'pages': seo_page, 'blog': seo_blog, 'locations': seo_location, 'cases': seo_case}

_tag = re.compile(r'\{%')


def has_template_tags(text):
    return bool(_tag.search(text or ''))
