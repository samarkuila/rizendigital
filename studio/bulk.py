"""Bulk page / bulk location engines for Rizen Studio.

Pure functions where possible: parse -> build preview items -> apply. The views run the same
build step for both "preview" and "create", so what you preview is exactly what is created.
"""
import csv
import io
import re
from html import escape

from django.db import transaction
from django.utils.text import slugify

from home.models import LocationFAQ, LocationPage, Page, Service

MAX_ROWS = 300
RESERVED_TAGS = {
    'admin', 'studio', 'static', 'media', 'sitemap.xml', 'robots.txt', 'llms.txt', 'about', 'contact', 'blog',
    'privacy-policy', 'terms-condition', 'case-studies', 'google-algorithm-updates', 'ai-agents', 'locations',
    'get-in-touch', 'home',
}
_TAG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
_TEMPLATE_TAG_RE = re.compile(r'\{%|\{#')

PAGE_ALIASES = {
    'name': 'page_name', 'title': 'page_name', 'page': 'page_name', 'page_name': 'page_name', 'pagename': 'page_name',
    'slug': 'page_tag', 'url': 'page_tag', 'tag': 'page_tag', 'page_tag': 'page_tag', 'pagetag': 'page_tag',
    'meta_title': 'meta_title', 'seo_title': 'meta_title', 'page_meta_title': 'meta_title',
    'meta_description': 'meta_description', 'description': 'meta_description', 'seo_description': 'meta_description', 'page_meta_description': 'meta_description',
    'keywords': 'keywords', 'meta_keywords': 'keywords', 'keyword': 'keywords', 'page_meta_keyword': 'keywords',
    'content': 'content', 'body': 'content', 'html': 'content', 'page_content': 'content',
    'short_content': 'short_content', 'summary': 'short_content', 'excerpt': 'short_content',
    'post_type': 'post_type', 'type': 'post_type',
    'image_alt': 'image_alt',
}


# ---------------------------------------------------------------- generic helpers
def words(text):
    return len(re.findall(r'\w+', re.sub(r'<[^>]+>', ' ', text or '')))


def plain(text):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text or '')).strip()


def truncate(text, limit):
    """Trim to <= limit characters on a word boundary."""
    text = (text or '').strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(' ', 1)[0].rstrip(' ,;:-|')
    return cut or text[:limit]


def fill(template, ctx):
    """Replace {placeholders} we know about; leave any other braces untouched."""
    return re.sub(r'\{(\w+)\}', lambda m: str(ctx.get(m.group(1), m.group(0))), template or '')


def as_html(text):
    """Plain text -> paragraphs; text that already contains tags is left alone."""
    text = (text or '').strip()
    if not text or re.search(r'<[a-zA-Z][^>]*>', text):
        return text
    parts = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    return ''.join('<p>%s</p>' % escape(p).replace('\n', '<br>') for p in parts)


def parse_table(text):
    """Parse pasted CSV/TSV text. Returns (rows_as_dicts_with_raw_headers, error)."""
    text = (text or '').strip('﻿\r\n ')
    if not text:
        return [], 'Nothing to import yet: paste rows or upload a CSV file.'
    sample = text[:4096]
    delim = ','
    first = sample.splitlines()[0] if sample.splitlines() else ''
    if first.count('\t') >= 1:
        delim = '\t'
    elif first.count('|') >= 1 and first.count(',') == 0:
        delim = '|'
    elif first.count(';') > first.count(','):
        delim = ';'
    reader = csv.reader(io.StringIO(text), delimiter=delim, skipinitialspace=True)
    try:
        rows = [r for r in reader if any((c or '').strip() for c in r)]
    except csv.Error as exc:
        return [], 'Could not read the table: %s' % exc
    if len(rows) < 2:
        return [], 'Include a header row and at least one data row.'
    headers = [re.sub(r'[^a-z0-9]+', '_', h.strip().lower()).strip('_') for h in rows[0]]
    out = []
    for r in rows[1:]:
        out.append({headers[i]: (r[i].strip() if i < len(r) else '') for i in range(len(headers)) if headers[i]})
    return out, None


# ---------------------------------------------------------------- bulk pages
def build_page_items(rows, on_conflict='skip', default_type='Custom_Page'):
    """Turn parsed rows into preview items with status, values and messages."""
    items, seen = [], set()
    existing = {p.page_tag: p for p in Page.objects.only('id', 'page_tag', 'page_name')}
    if len(rows) > MAX_ROWS:
        rows = rows[:MAX_ROWS]
        truncated = True
    else:
        truncated = False
    for n, raw in enumerate(rows, start=1):
        row = {}
        for k, v in raw.items():
            key = PAGE_ALIASES.get(k)
            if key and key not in row:
                row[key] = (v or '').strip()
        msgs, warns, status = [], [], 'new'
        name = row.get('page_name', '')
        if not name:
            msgs.append('Missing page name.')
        tag = row.get('page_tag') or slugify(name)
        tag = tag.strip('/').lower()
        tag = re.sub(r'\s+', '-', tag)
        if name and not tag:
            msgs.append('Could not build a URL slug from the name.')
        elif tag and not _TAG_RE.match(tag):
            msgs.append('URL slug "%s" may only contain lowercase letters, numbers and hyphens.' % tag)
        elif tag in RESERVED_TAGS:
            msgs.append('URL slug "%s" is reserved by the site.' % tag)
        if tag in seen:
            msgs.append('Duplicate slug "%s" earlier in this list.' % tag)
        seen.add(tag)
        content = as_html(row.get('content', ''))
        if _TEMPLATE_TAG_RE.search(content) or _TEMPLATE_TAG_RE.search(row.get('meta_title', '') + row.get('meta_description', '')):
            msgs.append('Template tags ({% ... %}) are not allowed in imported content.')
        meta_title = row.get('meta_title') or name
        meta_desc = row.get('meta_description') or truncate(plain(content), 155)
        if len(meta_title) > 80:
            meta_title = truncate(meta_title, 80)
            warns.append('Meta title shortened to 80 characters.')
        elif len(meta_title) > 60:
            warns.append('Meta title is over 60 characters and may be cut off in search results.')
        if not meta_desc:
            warns.append('No meta description.')
        elif len(meta_desc) > 160:
            warns.append('Meta description is over 160 characters.')
        wc = words(content)
        if wc < 150:
            warns.append('Only %d words: thin pages rarely rank. Add more original, useful content.' % wc)
        if not msgs and tag in existing:
            status = 'update' if on_conflict == 'update' else 'skip'
            msgs_note = 'A page with this URL already exists (%s).' % existing[tag].page_name
            warns.append(msgs_note + (' It will be updated.' if status == 'update' else ' It will be skipped.'))
        if msgs:
            status = 'error'
        ptype = row.get('post_type') or default_type
        if ptype not in ('Page', 'Blog', 'Custom_Page'):
            ptype = default_type
        items.append({
            'n': n, 'status': status, 'errors': msgs, 'warnings': warns,
            'values': {
                'page_name': name[:500], 'page_tag': tag, 'post_type': ptype,
                'page_meta_title': meta_title, 'page_meta_description': meta_desc,
                'page_meta_keyword': row.get('keywords') or name,
                'page_content': content, 'page_short_content': (row.get('short_content') or '')[:500] or None,
                'image_alt': (row.get('image_alt') or '')[:100],
            },
            'words': wc,
        })
    return items, truncated


def generate_page_rows(names_text, content_tpl, title_tpl, desc_tpl, keywords_tpl=''):
    """Template mode: one page per line ('Name' or 'Name | slug'), placeholders {name} {slug}."""
    rows = []
    for line in (names_text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split('|')]
        name = parts[0]
        slug = parts[1] if len(parts) > 1 and parts[1] else slugify(name)
        ctx_text = {'name': name, 'slug': slug, 'keyword': name.lower(), 'Name': name}
        ctx_html = {k: escape(v) for k, v in ctx_text.items()}
        rows.append({
            'page_name': name, 'page_tag': slug,
            'meta_title': fill(title_tpl, ctx_text), 'meta_description': fill(desc_tpl, ctx_text),
            'keywords': fill(keywords_tpl or '{keyword}', ctx_text),
            'content': fill(content_tpl, ctx_html),
        })
    return rows


@transaction.atomic
def apply_page_items(items):
    created, updated, skipped, failed = [], [], 0, 0
    for it in items:
        if it['status'] in ('error', 'skip'):
            skipped += it['status'] == 'skip'
            failed += it['status'] == 'error'
            continue
        v = it['values']
        if it['status'] == 'update':
            page = Page.objects.get(page_tag=v['page_tag'])
            for f, val in v.items():
                setattr(page, f, val)
            page.save()
            updated.append(page)
        else:
            created.append(Page.objects.create(**v))
    return {'created': created, 'updated': updated, 'skipped': skipped, 'failed': failed}


# ---------------------------------------------------------------- bulk locations
DEFAULTS = {
    'slug_pattern': '{service_slug}-{city_slug}',
    'headline': '{service} for businesses in {city}',
    'intro_variants': (
        'Rizen Digital helps {city} businesses grow with practical, measurable {service_lower}.\n'
        'Looking for {service_lower} in {city}? Rizen Digital builds clear, results-focused plans for local businesses.\n'
        'Reach more customers in {city} with {service_lower} that is planned around your goals and tracked month by month.'
    ),
    'meta_title': '{service} in {city} | Rizen Digital',
    'meta_description': 'Rizen Digital provides {service_lower} for {city} businesses: clear strategy, transparent reporting and measurable growth.',
    'content': (
        '<h2>{service} for {city} businesses</h2>\n'
        '<p>We help businesses in {city}, {country} strengthen their online presence with focused {service_lower}, built around what your customers actually search for.</p>\n'
        '{local_note_block}\n'
        '<h2>What we focus on</h2>\n'
        '<ul><li>Research into how {city} customers search and buy</li><li>Clear service pages that answer real questions</li>'
        '<li>Technical health and page experience that hold up in search</li><li>Monthly reporting tied to enquiries, not vanity metrics</li></ul>\n'
        '<h2>Why work with Rizen Digital</h2>\n'
        '<p>You get a specialist team, honest recommendations and reporting you can understand, with people-first work that follows Google’s quality guidance.</p>'
    ),
    'faqs': (
        'How much does {service_lower} cost in {city}? | Pricing depends on your goals, competition and scope. Contact Rizen Digital for a free quote tailored to your {city} business.\n'
        'Does Rizen Digital work with businesses in {city}? | Yes. We work with businesses in {city} and across India, with regular calls and transparent monthly reporting.'
    ),
}


def parse_cities(text):
    """Lines: 'City | Country | local note | lat | lng' (pipe) or 'City, Country, local note' (comma)."""
    out = []
    for line in (text or '').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
        else:
            parts = [p.strip() for p in line.split(',', 2)]
        parts += [''] * (5 - len(parts))
        out.append({'city': parts[0], 'country': parts[1], 'note': parts[2], 'lat': parts[3], 'lng': parts[4]})
    return out


def _dec(value):
    try:
        return round(float(value), 6) if value not in ('', None) else None
    except ValueError:
        return 'bad'


def build_location_items(service_ids, cities_text, cfg, on_conflict='skip'):
    cities = parse_cities(cities_text)
    services = list(Service.objects.filter(pk__in=service_ids).order_by('name'))
    items = []
    if not services:
        return items, ['Select at least one service.'], False
    if not cities:
        return items, ['Add at least one city (one per line).'], False
    errors = []
    if len(cities) * len(services) > MAX_ROWS:
        cities = cities[: max(1, MAX_ROWS // len(services))]
        errors.append('Limited to %d pages per run.' % MAX_ROWS)
    variants = [v.strip() for v in (cfg.get('intro_variants') or DEFAULTS['intro_variants']).splitlines() if v.strip()] or [DEFAULTS['intro_variants']]
    faq_lines = [l for l in (cfg.get('faqs') or '').splitlines() if '|' in l]
    existing = {p.slug: p for p in LocationPage.objects.only('id', 'slug')}
    seen, i = set(), 0
    for svc in services:
        for c in cities:
            i += 1
            city, country = c['city'], c['country'] or 'India'
            ctx = {
                'city': city, 'country': country, 'service': svc.name, 'service_lower': svc.name.lower(),
                'service_slug': slugify(svc.name), 'city_slug': slugify(city),
            }
            html_ctx = {k: escape(v) for k, v in ctx.items()}
            note = c['note']
            html_ctx['local_note_block'] = '<p>%s</p>' % escape(note) if note else ''
            ctx['local_note_block'] = ''
            errs, warns, status = [], [], 'new'
            if not city:
                errs.append('Missing city name.')
            slug = slugify(fill(cfg.get('slug_pattern') or DEFAULTS['slug_pattern'], ctx))
            if not slug:
                errs.append('Could not build a slug.')
            if slug in seen:
                errs.append('Duplicate slug "%s" in this run.' % slug)
            seen.add(slug)
            lat, lng = _dec(c['lat']), _dec(c['lng'])
            if lat == 'bad' or lng == 'bad':
                errs.append('Latitude/longitude must be numbers.')
                lat = lng = None
            intro_tpl = variants[(i - 1) % len(variants)]
            headline = truncate(fill(cfg.get('headline') or DEFAULTS['headline'], ctx), 180)
            intro = truncate(fill(intro_tpl, ctx), 700)
            content = fill(cfg.get('content') or DEFAULTS['content'], html_ctx)
            meta_title = fill(cfg.get('meta_title') or DEFAULTS['meta_title'], ctx)
            meta_desc = fill(cfg.get('meta_description') or DEFAULTS['meta_description'], ctx)
            if len(meta_title) > 60:
                meta_title = truncate(meta_title, 60)
                warns.append('Meta title shortened to 60 characters.')
            if len(meta_desc) > 160:
                meta_desc = truncate(meta_desc, 160)
                warns.append('Meta description shortened to 160 characters.')
            if _TEMPLATE_TAG_RE.search(content):
                errs.append('Template tags ({% ... %}) are not allowed.')
            if not note:
                warns.append('No local note: pages that only swap the city name are thin, near-duplicate content.')
            if not errs and slug in existing:
                status = 'update' if on_conflict == 'update' else 'skip'
                warns.append('A location page with this slug exists. ' + ('It will be updated.' if status == 'update' else 'It will be skipped.'))
            if errs:
                status = 'error'
            faqs = []
            for line in faq_lines:
                q, a = line.split('|', 1)
                faqs.append((truncate(fill(q.strip(), ctx), 200), truncate(fill(a.strip(), ctx), 600)))
            items.append({
                'n': i, 'status': status, 'errors': errs, 'warnings': warns, 'service': svc, 'city': city,
                'has_note': bool(note), 'words': words(content),
                'values': {
                    'service_id': svc.pk, 'city': city[:120], 'country': country[:120], 'slug': slug[:160],
                    'headline': headline, 'introduction': intro, 'content': content,
                    'meta_title': meta_title, 'meta_description': meta_desc,
                    'latitude': lat, 'longitude': lng,
                },
                'faqs': faqs,
            })
    return items, errors, True


@transaction.atomic
def apply_location_items(items, publish=False):
    created, updated, skipped, failed = [], [], 0, 0
    for it in items:
        if it['status'] in ('error', 'skip'):
            skipped += it['status'] == 'skip'
            failed += it['status'] == 'error'
            continue
        v = dict(it['values'])
        if it['status'] == 'update':
            obj = LocationPage.objects.get(slug=v['slug'])
            for f, val in v.items():
                setattr(obj, f, val)
            obj.is_published = publish or obj.is_published
            obj.save()
            obj.faqs.all().delete()
            updated.append(obj)
        else:
            obj = LocationPage.objects.create(is_published=publish, **v)
            created.append(obj)
        for order, (q, a) in enumerate(it['faqs']):
            LocationFAQ.objects.create(location_page=obj, question=q, answer=a, order=order)
    return {'created': created, 'updated': updated, 'skipped': skipped, 'failed': failed}
