import csv
import json
import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from admin_app.models import GetTouchWithUs
from home.models import BlogPost, CaseStudy, LocationPage, Page, Service, SubService, Testimonial

from . import bulk
from .forms import FORMS, FORM_GROUPS, LocationFAQFormSet, SEO_ADVANCED, SEO_PANELS, SEO_SOCIAL, SiteSettingsForm
from .models import SiteSettings
from .registry import KINDS
from .utils import IMAGE_EXTS, MAX_UPLOAD, SEO_FUNCS, sniff_image, staff_required


def _cfg(kind):
    cfg = KINDS.get(kind)
    if not cfg:
        raise Http404('Unknown content type')
    return cfg


# ------------------------------------------------------------------ auth
LOGIN_LIMIT, LOGIN_WINDOW = 8, 600


def _client_ip(request):
    return (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', ''))


def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('studio:dashboard')
    key = 'studio_login_fail:%s' % _client_ip(request)
    blocked = (cache.get(key) or 0) >= LOGIN_LIMIT
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if blocked:
            form.errors['__all__'] = form.error_class(['Too many attempts. Please wait a few minutes and try again.'])
        elif form.is_valid():
            user = form.get_user()
            if user.is_staff:
                cache.delete(key)
                auth_login(request, user)
                nxt = request.POST.get('next') or request.GET.get('next') or ''
                if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    nxt = reverse('studio:dashboard')
                return redirect(nxt)
            form.errors['__all__'] = form.error_class(['This account does not have access to Studio.'])
        if form.errors:
            cache.set(key, (cache.get(key) or 0) + 1, LOGIN_WINDOW)
    response = render(request, 'studio/login.html', {'form': form, 'next': request.GET.get('next', '')})
    response['X-Robots-Tag'] = 'noindex, nofollow'
    response['Cache-Control'] = 'no-store'
    return response


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('studio:login')


# ------------------------------------------------------------------ dashboard
def _health():
    rows = []
    for kind in ('pages', 'blog', 'locations', 'cases'):
        cfg = KINDS[kind]
        qs = cfg['model'].objects.all()
        if cfg.get('select_related'):
            qs = qs.select_related(*cfg['select_related'])
        for o in qs:
            r = SEO_FUNCS[kind](o)
            rows.append({'kind': kind, 'obj': o, 'title': cfg['title'](o), 'label': cfg['label'], **r})
    return rows


@staff_required
def dashboard(request):
    now = timezone.now()
    week = now - timedelta(days=7)
    leads = GetTouchWithUs.objects
    days = [(now - timedelta(days=13 - i)).date() for i in range(14)]
    per_day = {d: 0 for d in days}
    for dt in leads.filter(added_date_time__gte=now - timedelta(days=14)).values_list('added_date_time', flat=True):
        d = timezone.localtime(dt).date()
        if d in per_day:
            per_day[d] += 1
    peak = max(per_day.values()) or 1
    spark = [{'day': d, 'n': n, 'h': round(n / peak * 100) if n else 4} for d, n in per_day.items()]

    health = _health()
    avg = round(sum(h['score'] for h in health) / len(health)) if health else 100
    worst = sorted([h for h in health if h['issues']], key=lambda h: h['score'])[:8]

    recent = []
    for o in BlogPost.objects.order_by('-updated_at')[:5]:
        recent.append({'kind': 'blog', 'title': o.title, 'label': 'Blog post', 'when': o.updated_at, 'pk': o.pk, 'live': o.is_published})
    for o in LocationPage.objects.select_related('service').order_by('-updated_at')[:5]:
        recent.append({'kind': 'locations', 'title': '%s in %s' % (o.service.name, o.city), 'label': 'Location', 'when': o.updated_at, 'pk': o.pk, 'live': o.is_published})
    for o in CaseStudy.objects.order_by('-updated_at')[:3]:
        recent.append({'kind': 'cases', 'title': o.client_name, 'label': 'Case study', 'when': o.updated_at, 'pk': o.pk, 'live': o.is_published})
    for o in Page.objects.order_by('-post_date_time')[:5]:
        recent.append({'kind': 'pages', 'title': o.page_name, 'label': 'Page', 'when': o.post_date_time, 'pk': o.pk, 'live': True})
    recent.sort(key=lambda r: r['when'], reverse=True)

    stats = [
        {'label': 'Pages', 'value': Page.objects.count(), 'icon': 'file', 'url': reverse('studio:list', args=['pages']), 'tone': 'blue', 'note': '%d services' % Service.objects.count()},
        {'label': 'Blog posts', 'value': BlogPost.objects.count(), 'icon': 'pen', 'url': reverse('studio:list', args=['blog']), 'tone': 'violet', 'note': '%d published' % BlogPost.objects.filter(is_published=True).count()},
        {'label': 'Location pages', 'value': LocationPage.objects.count(), 'icon': 'pin', 'url': reverse('studio:list', args=['locations']), 'tone': 'teal', 'note': '%d live' % LocationPage.objects.filter(is_published=True).count()},
        {'label': 'Enquiries', 'value': leads.count(), 'icon': 'mail', 'url': reverse('studio:list', args=['leads']), 'tone': 'orange', 'note': '%d this week' % leads.filter(added_date_time__gte=week).count()},
    ]
    drafts = BlogPost.objects.filter(is_published=False).count() + LocationPage.objects.filter(is_published=False).count() + CaseStudy.objects.filter(is_published=False).count()
    return render(request, 'studio/dashboard.html', {
        'stats': stats, 'spark': spark, 'spark_total': sum(per_day.values()),
        'recent_leads': leads.order_by('-added_date_time')[:5], 'recent': recent[:8],
        'health_avg': avg, 'health_worst': worst, 'health_total': len(health),
        'drafts': drafts, 'cases': CaseStudy.objects.count(), 'testimonials': Testimonial.objects.count(),
        'hour': timezone.localtime().hour,
    })


# ------------------------------------------------------------------ list
def _stored_score(obj, heuristic):
    """Prefer the score saved from the Studio SEO analyzer (Rank-Math style) when there is one."""
    score = getattr(obj, 'seo_score', None)
    if score is None:
        return heuristic
    grade = 'good' if score >= 81 else 'ok' if score >= 51 else 'bad'
    return {**heuristic, 'score': score, 'grade': grade}


def _apply_filters(request, cfg, qs):
    q = (request.GET.get('q') or '').strip()
    if q:
        cond = Q()
        for f in cfg['search']:
            cond |= Q(**{f + '__icontains': q})
        qs = qs.filter(cond)
    status = request.GET.get('status')
    if cfg['has_status'] and status in ('published', 'draft'):
        qs = qs.filter(is_published=(status == 'published'))
    active = {}
    for f in cfg.get('filters', []):
        v = request.GET.get(f['param'])
        if v:
            qs = qs.filter(**{f['field']: v})
            active[f['param']] = v
    return qs, q, status, active


@staff_required
def obj_list(request, kind):
    cfg = _cfg(kind)
    qs = cfg['model'].objects.all()
    if cfg.get('select_related'):
        qs = qs.select_related(*cfg['select_related'])
    qs, q, status, active = _apply_filters(request, cfg, qs)
    sort = request.GET.get('sort') or ''
    allowed = {v: v for v in cfg['sortable'].values()}
    allowed.update({'-' + v: '-' + v for v in cfg['sortable'].values()})
    qs = qs.order_by(allowed.get(sort, cfg['order']))
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    seo_fn = SEO_FUNCS.get(kind)
    rows = []
    for o in page.object_list:
        rows.append({
            'obj': o, 'title': cfg['title'](o), 'subtitle': cfg['subtitle'](o),
            'live': getattr(o, 'is_published', None),
            'cells': [c[1](o) for c in cfg['columns']],
            'seo': _stored_score(o, seo_fn(o)) if seo_fn else None,
            'public': cfg['public'](o) if cfg.get('public') else None,
        })
    filters = [{'param': f['param'], 'label': f['label'], 'choices': f['choices'](), 'value': active.get(f['param'], '')} for f in cfg.get('filters', [])]
    keep = request.GET.copy()
    keep.pop('page', None)
    counts = None
    if cfg['has_status']:
        base = cfg['model'].objects
        counts = {'all': base.count(), 'published': base.filter(is_published=True).count(), 'draft': base.filter(is_published=False).count()}
    return render(request, 'studio/list.html', {
        'kind': kind, 'cfg': cfg, 'rows': rows, 'page': page, 'q': q, 'status': status or '', 'filters': filters,
        'columns': [c[0] for c in cfg['columns']], 'sort': sort, 'querystring': keep.urlencode(), 'counts': counts,
        'total': page.paginator.count,
    })


# ------------------------------------------------------------------ create / edit
@staff_required
def obj_edit(request, kind, pk=None):
    cfg = _cfg(kind)
    obj = get_object_or_404(cfg['model'], pk=pk) if pk else None
    if cfg.get('readonly'):
        if not obj:
            raise Http404
        return render(request, 'studio/lead_detail.html', {'kind': kind, 'cfg': cfg, 'obj': obj})
    Form = FORMS[kind]
    form = Form(request.POST or None, request.FILES or None, instance=obj)
    formset = None
    if kind == 'locations':
        formset = LocationFAQFormSet(request.POST or None, instance=obj or LocationPage(), prefix='faqs')
    if request.method == 'POST' and form.is_valid() and (formset is None or formset.is_valid()):
        try:
            saved = form.save()
        except ValueError as exc:  # e.g. a service page slug already exists
            form.add_error(None, str(exc))
        else:
            if formset is not None:
                formset.instance = saved
                for i, f in enumerate(formset.forms):
                    if f.instance is not None:
                        f.instance.order = i
                formset.save()
            messages.success(request, '%s saved.' % cfg['label'])
            if '_continue' in request.POST:
                return redirect('studio:edit', kind=kind, pk=saved.pk)
            return redirect('studio:list', kind=kind)
    if request.method == 'POST' and form.errors:
        messages.error(request, 'Please fix the highlighted fields.')
    seo = SEO_FUNCS[kind](obj) if obj and kind in SEO_FUNCS else None
    panel = None
    if kind in SEO_PANELS:
        p = SEO_PANELS[kind]
        og_url = obj.og_image.url if obj and getattr(obj, 'og_image', None) and obj.og_image.name else ''
        panel = {
            'general': [form[f] for f in p['general']], 'social': [form[f] for f in SEO_SOCIAL], 'advanced': [form[f] for f in SEO_ADVANCED],
            'focus': form['focus_keyword'], 'score': form['seo_score'],
            'config': json.dumps({
                'kind': kind, 'pk': obj.pk if obj else None, 'title': p['title'], 'seoTitle': p['seoTitle'], 'desc': p['desc'], 'slug': p['slug'],
                'content': p['content'], 'minWords': p['minWords'], 'prefix': p['prefix'], 'keyword': 'focus_keyword', 'score': 'seo_score',
                'ogTitle': 'og_title', 'ogDesc': 'og_description', 'ogImage': 'og_image', 'ogImageUrl': og_url,
                'host': request.get_host(), 'urls': {'keyword': reverse('studio:api_keyword'), 'links': reverse('studio:api_links')},
            }),
        }
    editing_tags = bool(obj and kind == 'pages' and '{%' in (obj.page_content or ''))
    return render(request, 'studio/form.html', {
        'kind': kind, 'cfg': cfg, 'obj': obj, 'form': form, 'formset': formset, 'is_new': obj is None,
        'seo': seo, 'seo_panel': panel, 'public': cfg['public'](obj) if obj and cfg.get('public') else None,
        'serp': cfg.get('serp'), 'raw_html': editing_tags, 'serp_prefix': {'pages': '', 'blog': 'blog/', 'locations': 'locations/', 'cases': 'case-studies/'}.get(kind, ''),
        'groups': [{'title': t, 'side': side, 'fields': [form[f] for f in fields]} for t, fields, side in FORM_GROUPS[kind]],
        'title': cfg['title'](obj) if obj else 'New %s' % cfg['label'].lower(),
    })


def _delete_guard(kind, obj):
    """Return a reason the object must not be deleted, else None."""
    if kind == 'pages':
        if obj.page_tag == 'home':
            return 'The home page cannot be deleted.'
        for rel in ('service', 'subservice'):
            try:
                getattr(obj, rel)
                return 'This page belongs to a %s. Delete the %s instead.' % (rel, rel.replace('subservice', 'sub-service'))
            except ObjectDoesNotExist:
                pass
    return None


@staff_required
@require_POST
def obj_delete(request, kind, pk):
    cfg = _cfg(kind)
    obj = get_object_or_404(cfg['model'], pk=pk)
    reason = _delete_guard(kind, obj)
    if reason:
        messages.error(request, reason)
    else:
        name = cfg['title'](obj)
        obj.delete()
        messages.success(request, '%s "%s" deleted.' % (cfg['label'], name))
    return redirect('studio:list', kind=kind)


@staff_required
@require_POST
def obj_bulk(request, kind):
    cfg = _cfg(kind)
    action = request.POST.get('action')
    ids = [int(i) for i in request.POST.getlist('ids') if i.isdigit()]
    if not ids:
        messages.error(request, 'Select at least one item first.')
        return redirect('studio:list', kind=kind)
    qs = cfg['model'].objects.filter(pk__in=ids)
    if action in ('publish', 'unpublish') and cfg['has_status']:
        flag = action == 'publish'
        n = 0
        for o in qs:
            o.is_published = flag
            if flag and hasattr(o, 'published_at') and not o.published_at:
                o.published_at = timezone.now()
            o.save()
            n += 1
        messages.success(request, '%d item%s %s.' % (n, '' if n == 1 else 's', 'published' if flag else 'moved to draft'))
    elif action == 'delete':
        n, skipped = 0, 0
        for o in qs:
            if _delete_guard(kind, o):
                skipped += 1
                continue
            o.delete()
            n += 1
        messages.success(request, '%d deleted.' % n + (' %d protected item(s) skipped.' % skipped if skipped else ''))
    elif action == 'export':
        return _csv_response(kind, cfg, qs)
    else:
        messages.error(request, 'Unknown action.')
    return redirect(request.POST.get('next') or reverse('studio:list', args=[kind]))


def _safe_cell(v):
    s = '' if v is None else str(v)
    return "'" + s if s[:1] in ('=', '+', '-', '@', '\t', '\r') else s  # block spreadsheet formula injection


def _csv_response(kind, cfg, qs):
    fields = [f for f in cfg['model']._meta.concrete_fields]
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="rizen-%s-%s.csv"' % (kind, timezone.now().strftime('%Y%m%d'))
    resp.write('﻿')
    w = csv.writer(resp)
    w.writerow([f.name for f in fields])
    for o in qs:
        w.writerow([_safe_cell(getattr(o, f.attname)) for f in fields])
    return resp


@staff_required
def obj_export(request, kind):
    cfg = _cfg(kind)
    qs, *_ = _apply_filters(request, cfg, cfg['model'].objects.all())
    return _csv_response(kind, cfg, qs.order_by(cfg['order']))


# ------------------------------------------------------------------ search palette
@staff_required
def api_search(request):
    q = (request.GET.get('q') or '').strip()
    out = []
    if len(q) < 2:
        return JsonResponse({'results': []})
    def add(kind, qs, title, sub):
        for o in qs[:5]:
            out.append({'group': KINDS[kind]['plural'], 'title': title(o), 'sub': sub(o), 'url': reverse('studio:edit', args=[kind, o.pk])})
    add('pages', Page.objects.filter(Q(page_name__icontains=q) | Q(page_tag__icontains=q)), lambda o: o.page_name, lambda o: '/' + o.page_tag)
    add('blog', BlogPost.objects.filter(Q(title__icontains=q) | Q(slug__icontains=q)), lambda o: o.title, lambda o: 'Published' if o.is_published else 'Draft')
    add('locations', LocationPage.objects.select_related('service').filter(Q(city__icontains=q) | Q(slug__icontains=q) | Q(headline__icontains=q)), lambda o: '%s in %s' % (o.service.name, o.city), lambda o: o.country)
    add('cases', CaseStudy.objects.filter(Q(client_name__icontains=q) | Q(summary__icontains=q)), lambda o: o.client_name, lambda o: o.industry)
    add('services', Service.objects.filter(name__icontains=q), lambda o: o.name, lambda o: 'Service')
    add('leads', GetTouchWithUs.objects.filter(Q(full_name__icontains=q) | Q(email__icontains=q) | Q(company_name__icontains=q)), lambda o: o.full_name, lambda o: o.email)
    return JsonResponse({'results': out})


# ------------------------------------------------------------------ SEO helper APIs
_SEO_MODELS = (('pages', Page), ('blog', BlogPost), ('locations', LocationPage), ('cases', CaseStudy))


@staff_required
def api_keyword(request):
    """Which other items already target this focus keyword? (keyword cannibalisation check)"""
    kw = (request.GET.get('kw') or '').strip()
    kind = request.GET.get('kind') or ''
    pk = request.GET.get('pk') or ''
    used = []
    if kw:
        for k, model in _SEO_MODELS:
            qs = model.objects.filter(focus_keyword__iexact=kw)
            if k == kind and pk.isdigit():
                qs = qs.exclude(pk=int(pk))
            for o in qs[:5]:
                used.append({'title': KINDS[k]['title'](o), 'kind': KINDS[k]['label'], 'url': reverse('studio:edit', args=[k, o.pk])})
    return JsonResponse({'used_by': used})


@staff_required
def api_links(request):
    """Internal-link suggestions: live pages whose title matches the focus keyword."""
    q = (request.GET.get('q') or '').strip().lower()
    kind = request.GET.get('kind') or ''
    pk = request.GET.get('pk') or ''
    terms = [t for t in set(w for w in q.replace('-', ' ').split() if len(w) > 2)][:6]
    if not terms:
        return JsonResponse({'results': []})
    out = []
    def scan(k, qs, title_fields, url, label):
        cond = Q()
        for t in terms:
            for f in title_fields:
                cond |= Q(**{f + '__icontains': t})
        qs = qs.filter(cond)
        if k == kind and pk.isdigit():
            qs = qs.exclude(pk=int(pk))
        for o in qs[:12]:
            title = KINDS[k]['title'](o)
            hits = sum(1 for t in terms if t in title.lower())
            out.append({'title': title, 'url': url(o), 'kind': label, 'hits': hits})
    scan('pages', Page.objects.exclude(page_tag='home'), ('page_name', 'page_meta_title'), lambda o: '/%s/' % o.page_tag, 'Page')
    scan('blog', BlogPost.objects.filter(is_published=True), ('title',), lambda o: o.get_absolute_url(), 'Post')
    scan('locations', LocationPage.objects.select_related('service').filter(is_published=True), ('headline', 'city'), lambda o: o.get_absolute_url(), 'Location')
    scan('cases', CaseStudy.objects.filter(is_published=True), ('client_name', 'summary'), lambda o: o.get_absolute_url(), 'Case study')
    out.sort(key=lambda r: -r['hits'])
    return JsonResponse({'results': out[:8]})


# ------------------------------------------------------------------ site settings
@staff_required
def site_settings(request):
    obj = SiteSettings.load()
    form = SiteSettingsForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Site settings saved. Changes are live on the site.')
        return redirect('studio:settings')
    return render(request, 'studio/settings.html', {'form': form, 'env_phone': settings.SITE_PHONE})


# ------------------------------------------------------------------ media library
def _media_root():
    return os.path.realpath(settings.MEDIA_ROOT)


def _media_items(limit=400):
    root = _media_root()
    items = []
    if not os.path.isdir(root):
        return items
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, root).replace(os.sep, '/')
                st = os.stat(full)
                items.append({'name': f, 'path': rel, 'url': settings.MEDIA_URL + rel, 'size': st.st_size, 'mtime': st.st_mtime, 'folder': os.path.dirname(rel) or '/'})
    items.sort(key=lambda i: i['mtime'], reverse=True)
    return items[:limit]


@staff_required
def media_library(request):
    items = _media_items()
    q = (request.GET.get('q') or '').lower()
    if q:
        items = [i for i in items if q in i['path'].lower()]
    total = sum(i['size'] for i in items)
    return render(request, 'studio/media.html', {'items': items, 'q': q, 'total_kb': round(total / 1024)})


@staff_required
def api_media(request):
    return JsonResponse({'items': [{'name': i['name'], 'url': i['url'], 'path': i['path']} for i in _media_items(120)]})


@staff_required
@require_POST
def media_upload(request):
    root = _media_root()
    folder = os.path.join(root, 'library')
    os.makedirs(folder, exist_ok=True)
    saved, rejected = [], []
    for up in request.FILES.getlist('files'):
        name = (up.name or '').lower()
        ext = os.path.splitext(name)[1]
        if ext not in IMAGE_EXTS or up.size > MAX_UPLOAD or not sniff_image(up.read(16), ext):
            up.seek(0)
            rejected.append(up.name)
            continue
        up.seek(0)
        base = slugify(os.path.splitext(name)[0])[:60] or 'image'
        fname = '%s-%s%s' % (base, uuid.uuid4().hex[:6], ext)
        with open(os.path.join(folder, fname), 'wb') as fh:
            for chunk in up.chunks():
                fh.write(chunk)
        saved.append(fname)
    if saved:
        messages.success(request, '%d image%s uploaded.' % (len(saved), '' if len(saved) == 1 else 's'))
    if rejected:
        messages.error(request, 'Skipped (not a valid image or over 8 MB): %s' % ', '.join(rejected[:5]))
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'saved': saved, 'rejected': rejected})
    return redirect('studio:media')


@staff_required
@require_POST
def media_delete(request):
    rel = (request.POST.get('path') or '').replace('\\', '/')
    full = os.path.realpath(os.path.join(_media_root(), rel))
    if not full.startswith(_media_root() + os.sep) or not os.path.isfile(full) or os.path.splitext(full)[1].lower() not in IMAGE_EXTS:
        messages.error(request, 'That file could not be found.')
    else:
        os.remove(full)
        messages.success(request, 'Image deleted. Any page still using it will show a broken image.')
    return redirect('studio:media')


# ------------------------------------------------------------------ bulk pages
PAGE_SAMPLE = (
    'page_name,page_tag,meta_title,meta_description,content\n'
    'SEO Services in Kolkata,seo-services-kolkata,SEO Services in Kolkata | Rizen Digital,"Grow organic traffic with practical, measurable SEO from a Kolkata-based team.","<h2>SEO that drives enquiries</h2><p>Explain the service in your own words here.</p>"\n'
)
PAGE_TPL_DEFAULTS = {
    'content_tpl': '<h2>{name}</h2>\n<p>Introduce {name} in one clear paragraph: who it is for and the problem it solves.</p>\n<h2>How we help</h2>\n<p>Describe your process, deliverables and what makes your approach different.</p>',
    'title_tpl': '{name} | Rizen Digital',
    'desc_tpl': 'Learn how Rizen Digital delivers {keyword}: clear strategy, transparent reporting and measurable results.',
}


def _summary(items):
    s = {'new': 0, 'update': 0, 'skip': 0, 'error': 0, 'warn': 0}
    for it in items:
        s[it['status']] += 1
        s['warn'] += bool(it['warnings'])
    return s


@staff_required
def bulk_pages(request):
    ctx = {
        'mode': 'paste', 'table': '', 'names': '', 'on_conflict': 'skip', 'sample': PAGE_SAMPLE,
        **PAGE_TPL_DEFAULTS, 'items': None, 'result': None, 'summary': None, 'error': None,
    }
    if request.method == 'POST':
        post = request.POST
        ctx.update({k: post.get(k, ctx[k]) for k in ('mode', 'table', 'names', 'content_tpl', 'title_tpl', 'desc_tpl', 'on_conflict')})
        if ctx['mode'] == 'template':
            rows = bulk.generate_page_rows(ctx['names'], ctx['content_tpl'], ctx['title_tpl'], ctx['desc_tpl'])
            err = None if rows else 'Add at least one page name (one per line).'
        else:
            rows, err = bulk.parse_table(ctx['table'])
        if err:
            ctx['error'] = err
        else:
            items, truncated = bulk.build_page_items(rows, ctx['on_conflict'])
            if truncated:
                messages.warning(request, 'Only the first %d rows are processed per run.' % bulk.MAX_ROWS)
            ctx['items'], ctx['summary'] = items, _summary(items)
            if post.get('action') == 'create':
                res = bulk.apply_page_items(items)
                ctx['result'] = res
                messages.success(request, 'Created %d and updated %d pages.' % (len(res['created']), len(res['updated'])))
    return render(request, 'studio/bulk_pages.html', ctx)


@staff_required
def bulk_pages_template(request):
    resp = HttpResponse(PAGE_SAMPLE, content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="rizen-bulk-pages-template.csv"'
    return resp


# ------------------------------------------------------------------ bulk location pages
@staff_required
def bulk_locations(request):
    services = list(Service.objects.order_by('name'))
    d = bulk.DEFAULTS
    ctx = {
        'services': services, 'selected': [], 'cities': '', 'slug_pattern': d['slug_pattern'], 'headline': d['headline'],
        'intro_variants': d['intro_variants'], 'meta_title': d['meta_title'], 'meta_description': d['meta_description'],
        'content': d['content'], 'faqs': d['faqs'], 'on_conflict': 'skip', 'publish': False,
        'items': None, 'result': None, 'summary': None, 'errors': [], 'thin': 0,
    }
    if request.method == 'POST':
        p = request.POST
        for k in ('cities', 'slug_pattern', 'headline', 'intro_variants', 'meta_title', 'meta_description', 'content', 'faqs', 'on_conflict'):
            ctx[k] = p.get(k, ctx[k])
        ctx['publish'] = p.get('publish') == 'on'
        ctx['selected'] = [int(i) for i in p.getlist('services') if i.isdigit()]
        cfg = {k: ctx[k] for k in ('slug_pattern', 'headline', 'intro_variants', 'meta_title', 'meta_description', 'content', 'faqs')}
        items, errors, ok = bulk.build_location_items(ctx['selected'], ctx['cities'], cfg, ctx['on_conflict'])
        ctx['errors'] = errors
        if ok:
            ctx['items'], ctx['summary'] = items, _summary(items)
            ctx['thin'] = sum(1 for it in items if not it['has_note'] and it['status'] in ('new', 'update'))
            if p.get('action') == 'create':
                res = bulk.apply_location_items(items, publish=ctx['publish'])
                ctx['result'] = res
                messages.success(request, 'Created %d and updated %d location pages%s.' % (len(res['created']), len(res['updated']), ' and published them' if ctx['publish'] else ' as drafts'))
    return render(request, 'studio/bulk_locations.html', ctx)
