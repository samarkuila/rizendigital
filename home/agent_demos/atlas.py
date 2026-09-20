"""Atlas: a real technical/on-page SEO check of a public URL."""
import json
from html.parser import HTMLParser
from urllib.parse import urlsplit

from . import _fetch, ai_slot, rate_limited

HOURLY_LIMIT = 8


class _Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ''
        self._in_title = False
        self.meta = {}
        self.canonical = ''
        self.lang = ''
        self.h = {1: 0, 2: 0, 3: 0}
        self.imgs = self.imgs_no_alt = self.imgs_no_dims = 0
        self.links_int = self.links_ext = 0
        self.jsonld = []
        self._in_ld = False
        self._ld_buf = ''
        self.scripts_blocking = 0
        self.stylesheets = 0
        self.host = ''
        self.hreflang = 0

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        if tag == 'html':
            self.lang = a.get('lang', '')
        elif tag == 'title':
            self._in_title = True
        elif tag == 'meta':
            key = (a.get('name') or a.get('property') or '').lower()
            if key:
                self.meta[key] = a.get('content', '')
        elif tag == 'link':
            rel = a.get('rel', '').lower()
            if 'canonical' in rel:
                self.canonical = a.get('href', '')
            if 'stylesheet' in rel:
                self.stylesheets += 1
            if 'alternate' in rel and a.get('hreflang'):
                self.hreflang += 1
        elif tag in ('h1', 'h2', 'h3'):
            self.h[int(tag[1])] += 1
        elif tag == 'img':
            self.imgs += 1
            if 'alt' not in a:
                self.imgs_no_alt += 1
            if not (a.get('width') and a.get('height')):
                self.imgs_no_dims += 1
        elif tag == 'a':
            href = a.get('href', '')
            if href.startswith(('http://', 'https://')) and urlsplit(href).hostname not in ('', self.host):
                self.links_ext += 1
            elif href and not href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                self.links_int += 1
        elif tag == 'script':
            if a.get('type', '').lower() == 'application/ld+json':
                self._in_ld, self._ld_buf = True, ''
            elif a.get('src') and 'async' not in a and 'defer' not in a and a.get('type', '') != 'module':
                self.scripts_blocking += 1

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        elif tag == 'script' and self._in_ld:
            self._in_ld = False
            self.jsonld.append(self._ld_buf)

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self._ld_buf += data


def _chk(status, name, detail, fix='', weight=1):
    return {'status': status, 'name': name, 'detail': detail, 'fix': fix, 'weight': weight}


def _schema_types(blocks):
    types, bad = [], 0
    for raw in blocks:
        try:
            data = json.loads(raw)
        except ValueError:
            bad += 1
            continue
        items = data if isinstance(data, list) else data.get('@graph', [data]) if isinstance(data, dict) else []
        for it in items:
            t = it.get('@type') if isinstance(it, dict) else None
            types += t if isinstance(t, list) else [t] if t else []
    return sorted(set(types)), bad


def _audit(res, robots, sitemap):
    host = urlsplit(res['url']).hostname
    html = res['body'].decode('utf-8', 'replace')
    p = _Page()
    p.host = host
    p.feed(html)
    h = res['headers']
    checks = []
    title = ' '.join(p.title.split())
    if not title:
        checks.append(_chk('fail', 'Page title', 'No <title> found.', 'Add a unique title of 30-60 characters with your main keyword.', 3))
    elif 30 <= len(title) <= 60:
        checks.append(_chk('pass', 'Page title', '%d characters: "%s"' % (len(title), title[:80]), weight=3))
    else:
        checks.append(_chk('warn', 'Page title', '%d characters (best 30-60): "%s"' % (len(title), title[:80]), 'Rewrite so it is 30-60 characters and still reads naturally.', 3))
    desc = p.meta.get('description', '').strip()
    if not desc:
        checks.append(_chk('fail', 'Meta description', 'Missing.', 'Write a 70-160 character summary that earns the click.', 2))
    elif 70 <= len(desc) <= 160:
        checks.append(_chk('pass', 'Meta description', '%d characters.' % len(desc), weight=2))
    else:
        checks.append(_chk('warn', 'Meta description', '%d characters (best 70-160).' % len(desc), 'Trim or expand it to fit the snippet.', 2))
    if p.h[1] == 1:
        checks.append(_chk('pass', 'Main heading (H1)', 'Exactly one H1.', weight=2))
    elif p.h[1] == 0:
        checks.append(_chk('fail', 'Main heading (H1)', 'No H1 found.', 'Add one H1 that states what the page is about.', 2))
    else:
        checks.append(_chk('warn', 'Main heading (H1)', '%d H1 headings.' % p.h[1], 'Use a single H1 and H2/H3 for sections.', 2))
    checks.append(_chk('pass' if p.canonical else 'warn', 'Canonical tag', p.canonical or 'Not set.', '' if p.canonical else 'Add a canonical link to stop duplicate-URL issues.', 1))
    checks.append(_chk('pass' if 'viewport' in p.meta else 'fail', 'Mobile viewport', 'Present.' if 'viewport' in p.meta else 'Missing.', '' if 'viewport' in p.meta else 'Add <meta name="viewport" content="width=device-width, initial-scale=1">.', 2))
    checks.append(_chk('pass' if p.lang else 'warn', 'Language attribute', p.lang or 'No lang on <html>.', '' if p.lang else 'Set <html lang="en"> so browsers and search engines know the language.', 1))
    robots_meta = p.meta.get('robots', '').lower()
    if 'noindex' in robots_meta or 'noindex' in h.get('x-robots-tag', '').lower():
        checks.append(_chk('fail', 'Indexable', 'This page tells search engines NOT to index it.', 'Remove noindex if you want this page to rank.', 3))
    else:
        checks.append(_chk('pass', 'Indexable', 'No noindex directive.', weight=3))
    checks.append(_chk('pass' if res['https'] else 'fail', 'HTTPS', 'Served over HTTPS.' if res['https'] else 'Served over plain HTTP.', '' if res['https'] else 'Install a certificate and redirect all HTTP to HTTPS.', 3))
    if 'strict-transport-security' in h:
        checks.append(_chk('pass', 'HSTS header', 'Present.', weight=1))
    elif res['https']:
        checks.append(_chk('warn', 'HSTS header', 'Not sent.', 'Add Strict-Transport-Security to lock browsers to HTTPS.', 1))
    hops = len(res['chain']) - 1
    checks.append(_chk('pass' if hops <= 1 else 'warn', 'Redirects', '%d redirect%s before the final page.' % (hops, '' if hops == 1 else 's'), '' if hops <= 1 else 'Link straight to the final URL to save crawl time.', 1))
    ms = res['ms']
    checks.append(_chk('pass' if ms < 800 else 'warn' if ms < 2000 else 'fail', 'Server response', '%d ms for the HTML.' % ms, '' if ms < 800 else 'Add caching or upgrade hosting to get under 800 ms.', 2))
    kb = len(res['body']) // 1024
    checks.append(_chk('pass' if kb < 500 else 'warn', 'HTML size', '%d KB%s.' % (kb, ' (truncated at limit)' if res['truncated'] else ''), '' if kb < 500 else 'Very large HTML slows parsing; trim inline data.', 1))
    if p.imgs:
        ok = p.imgs_no_alt == 0
        checks.append(_chk('pass' if ok else 'warn', 'Image alt text', '%d of %d images have alt text.' % (p.imgs - p.imgs_no_alt, p.imgs) if not ok else 'All %d images have alt text.' % p.imgs, '' if ok else 'Describe each meaningful image; use alt="" for decoration.', 2))
        d = p.imgs_no_dims == 0
        checks.append(_chk('pass' if d else 'warn', 'Image dimensions', 'All images declare width and height.' if d else '%d images lack width/height.' % p.imgs_no_dims, '' if d else 'Set width and height to prevent layout shift (CLS).', 1))
    if p.scripts_blocking:
        checks.append(_chk('warn', 'Render-blocking scripts', '%d script(s) without async/defer.' % p.scripts_blocking, 'Add defer to scripts that do not need to run first.', 1))
    types, bad = _schema_types(p.jsonld)
    if bad:
        checks.append(_chk('fail', 'Structured data', '%d JSON-LD block(s) contain invalid JSON.' % bad, 'Fix the JSON syntax so search engines can read it.', 2))
    elif types:
        checks.append(_chk('pass', 'Structured data', 'Found: %s.' % ', '.join(types[:8]), weight=2))
    else:
        checks.append(_chk('warn', 'Structured data', 'No JSON-LD found.', 'Add Organization / LocalBusiness / FAQ / Article schema where it applies.', 2))
    checks.append(_chk('pass' if p.meta.get('og:title') else 'warn', 'Social sharing tags', 'Open Graph title present.' if p.meta.get('og:title') else 'No Open Graph tags.', '' if p.meta.get('og:title') else 'Add og:title, og:description and og:image for better link previews.', 1))
    checks.append(_chk('pass' if robots else 'warn', 'robots.txt', 'Found.' if robots else 'Not found at /robots.txt.', '' if robots else 'Publish a robots.txt that references your sitemap.', 1))
    checks.append(_chk('pass' if sitemap else 'warn', 'XML sitemap', 'Found at /sitemap.xml.' if sitemap else 'Not found at /sitemap.xml.', '' if sitemap else 'Publish a sitemap and submit it in Search Console.', 2))
    scored = [c for c in checks if c['weight']]
    total = sum(c['weight'] for c in scored)
    got = sum(c['weight'] * {'pass': 1, 'warn': 0.5, 'fail': 0}[c['status']] for c in scored)
    facts = {'h2': p.h[2], 'h3': p.h[3], 'links_int': p.links_int, 'links_ext': p.links_ext, 'images': p.imgs,
             'hreflang': p.hreflang, 'stylesheets': p.stylesheets}
    return checks, round(got / total * 100) if total else 0, facts


def run(request):
    ctx = {'url': (request.GET.get('url') or '').strip()[:300], 'ran': False, 'error': ''}
    if not ctx['url']:
        return ctx
    ctx['ran'] = True
    if rate_limited(request, 'atlas', HOURLY_LIMIT):
        ctx['error'] = 'You have run several audits this hour. Please try again a little later.'
        return ctx
    try:
        res = _fetch.fetch(ctx['url'])
        base = '%s://%s' % (urlsplit(res['url']).scheme, urlsplit(res['url']).netloc)

        def exists(path):
            try:
                r = _fetch.fetch(base + path, cap=200_000)
                return r['status'] == 200 and b'<html' not in r['body'][:500].lower()
            except _fetch.FetchError:
                return False
        robots, sitemap = exists('/robots.txt'), exists('/sitemap.xml')
    except _fetch.FetchError as exc:
        ctx['error'] = str(exc)
        return ctx
    if res['status'] >= 400:
        ctx['error'] = 'The page returned HTTP %d, so there is nothing to audit.' % res['status']
        return ctx
    ctype = res['headers'].get('content-type', '')
    if 'html' not in ctype.lower():
        ctx['error'] = 'That address did not return a web page (%s).' % (ctype or 'unknown type')
        return ctx
    checks, score, facts = _audit(res, robots, sitemap)
    order = {'fail': 0, 'warn': 1, 'pass': 2}
    ctx.update({
        'final_url': res['url'], 'score': score, 'facts': facts, 'chain': res['chain'],
        'checks': sorted(checks, key=lambda c: (order[c['status']], -c['weight'])),
        'counts': {s: sum(1 for c in checks if c['status'] == s) for s in order},
        'grade': 'Excellent' if score >= 90 else 'Good' if score >= 75 else 'Needs work' if score >= 55 else 'Poor',
    })
    ctx['ai'] = ai_slot('atlas', {'url': res['url'], 'score': score, 'checks': ctx['checks']})
    return ctx
