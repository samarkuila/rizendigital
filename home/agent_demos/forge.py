"""Forge: accessibility and speed-budget checks on a pasted HTML page or component."""
import re
from html.parser import HTMLParser

from . import ai_slot
from .prism import contrast

SAMPLE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://cdn.example.com/analytics.js"></script>
  <link rel="stylesheet" href="/css/site.css">
</head>
<body>
  <h1>Kolkata Dental Care</h1>
  <h3>Our services</h3>
  <img src="/img/hero.jpg">
  <img src="/img/team.jpg" alt="Our dentists">
  <p style="color:#999999;background:#ffffff">Book your appointment today.</p>
  <a href="/book">Click here</a>
  <a href="/contact"></a>
  <form>
    <input type="text" name="name" placeholder="Your name">
    <label for="phone">Phone</label><input id="phone" type="tel" name="phone">
    <button></button>
  </form>
  <div tabindex="3">Offer ends soon</div>
</body>
</html>"""

HEX = re.compile(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', re.I)
VOID = {'meta', 'link', 'img', 'input', 'br', 'hr', 'source', 'area', 'base', 'col', 'embed', 'track', 'wbr'}


def _hex(value):
    m = HEX.match(value.strip())
    if not m:
        return None
    h = m.group(1)
    return '#' + (''.join(c * 2 for c in h) if len(h) == 3 else h).lower()


class _Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = self.title = ''
        self.viewport = False
        self.stack = []
        self.headings = []
        self.imgs = []
        self.inputs = []
        self.labels_for = set()
        self.buttons = []
        self.links = []
        self.tabindex = []
        self.contrast = []
        self.scripts = []
        self.styles = 0
        self.iframes = 0
        self._text_target = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        pos = self.getpos()[0]
        if tag == 'html':
            self.lang = a.get('lang', '')
        elif tag == 'title':
            self._in_title = True
        elif tag == 'meta' and a.get('name', '').lower() == 'viewport':
            self.viewport = True
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings.append((int(tag[1]), pos))
        elif tag == 'img':
            self.imgs.append({'alt': 'alt' in a, 'dims': bool(a.get('width') and a.get('height')), 'lazy': a.get('loading') == 'lazy', 'line': pos})
        elif tag in ('input', 'select', 'textarea') and a.get('type', '').lower() not in ('hidden', 'submit', 'button', 'image', 'reset'):
            self.inputs.append({'id': a.get('id', ''), 'named': bool(a.get('aria-label') or a.get('aria-labelledby') or a.get('title')), 'line': pos})
        elif tag == 'label' and a.get('for'):
            self.labels_for.add(a['for'])
        elif tag in ('a', 'button'):
            self._text_target = {'tag': tag, 'text': '', 'named': bool(a.get('aria-label') or a.get('title')), 'href': a.get('href', ''), 'line': pos}
        elif tag == 'script':
            if a.get('src'):
                self.scripts.append({'blocking': 'async' not in a and 'defer' not in a and a.get('type') != 'module' and 'head' in self.stack, 'src': a['src'], 'line': pos})
        elif tag == 'style':
            self.styles += 1
        elif tag == 'iframe':
            self.iframes += 1
        if 'tabindex' in a:
            try:
                if int(a['tabindex']) > 0:
                    self.tabindex.append(pos)
            except ValueError:
                pass
        if a.get('style'):
            props = dict((k.strip().lower(), v.strip()) for k, _, v in (p.partition(':') for p in a['style'].split(';')) if k.strip())
            fg, bg = _hex(props.get('color', '')), _hex(props.get('background-color', props.get('background', '')))
            if fg and bg:
                self.contrast.append({'fg': fg, 'bg': bg, 'ratio': contrast(fg, bg), 'line': pos})
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        if tag in ('a', 'button') and self._text_target:
            (self.links if self._text_target['tag'] == 'a' else self.buttons).append(self._text_target)
            self._text_target = None
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._text_target is not None:
            self._text_target['text'] += data


def _c(status, area, name, detail, fix='', line=None):
    return {'status': status, 'area': area, 'name': name, 'detail': detail, 'fix': fix, 'line': line}


def check(html):
    s = _Scan()
    s.feed(html)
    out = []
    a11y = 'Accessibility'
    out.append(_c('pass' if s.lang else 'fail', a11y, 'Page language', s.lang or 'No lang attribute on <html>.', '' if s.lang else 'Add <html lang="en"> so screen readers pronounce the page correctly.'))
    if s.title.strip():
        out.append(_c('pass', a11y, 'Page title', s.title.strip()[:70]))
    elif '<html' in html.lower():
        out.append(_c('fail', a11y, 'Page title', 'No <title>.', 'Give every page a unique, descriptive title.'))
    out.append(_c('pass' if s.viewport else 'warn', 'Speed & mobile', 'Mobile viewport', 'Present.' if s.viewport else 'Missing.', '' if s.viewport else 'Add <meta name="viewport" content="width=device-width, initial-scale=1">.'))
    bad = [i for i in s.imgs if not i['alt']]
    for i in bad:
        out.append(_c('fail', a11y, 'Image missing alt text', 'An <img> has no alt attribute.', 'Describe the image, or use alt="" if it is purely decorative.', i['line']))
    if s.imgs and not bad:
        out.append(_c('pass', a11y, 'Image alt text', 'All %d images have alt attributes.' % len(s.imgs)))
    unlabeled = [i for i in s.inputs if not (i['named'] or (i['id'] and i['id'] in s.labels_for))]
    for i in unlabeled:
        out.append(_c('fail', a11y, 'Form field without a label', 'A form field has no <label for> or aria-label. Placeholder text is not a label.', 'Add <label for="id"> connected to the field.', i['line']))
    if s.inputs and not unlabeled:
        out.append(_c('pass', a11y, 'Form labels', 'All %d fields are labelled.' % len(s.inputs)))
    for b in s.buttons:
        if not b['text'].strip() and not b['named']:
            out.append(_c('fail', a11y, 'Button with no name', 'A <button> has no text or aria-label.', 'Give it visible text or aria-label so it can be announced.', b['line']))
    generic = {'click here', 'here', 'read more', 'more', 'link'}
    for l in s.links:
        t = ' '.join(l['text'].split()).lower()
        if not t and not l['named']:
            out.append(_c('fail', a11y, 'Link with no text', 'An <a> has no text or aria-label.', 'Describe where the link goes.', l['line']))
        elif t in generic:
            out.append(_c('warn', a11y, 'Vague link text', '"%s" does not say where it leads.' % t, 'Use descriptive text like "Book an appointment".', l['line']))
    levels = [h for h, _ in s.headings]
    h1s = levels.count(1)
    if s.headings:
        out.append(_c('pass' if h1s == 1 else 'warn', a11y, 'Main heading', '%d H1 heading(s).' % h1s, '' if h1s == 1 else 'Use exactly one H1.'))
        for (prev, _), (cur, line) in zip(s.headings, s.headings[1:]):
            if cur > prev + 1:
                out.append(_c('warn', a11y, 'Skipped heading level', 'H%d follows H%d.' % (cur, prev), 'Do not skip levels; screen-reader users navigate by heading.', line))
    for line in s.tabindex:
        out.append(_c('warn', a11y, 'Positive tabindex', 'tabindex above 0 breaks natural keyboard order.', 'Use tabindex="0" or remove it.', line))
    for c in s.contrast:
        ok = c['ratio'] >= 4.5
        out.append(_c('pass' if ok else 'fail', a11y, 'Text contrast', '%s on %s is %.1f:1 (needs 4.5:1).' % (c['fg'], c['bg'], c['ratio']), '' if ok else 'Darken the text or lighten the background.', c['line']))
    perf = 'Speed & mobile'
    blocking = [x for x in s.scripts if x['blocking']]
    for x in blocking:
        out.append(_c('warn', perf, 'Render-blocking script', '%s loads in <head> without defer/async.' % x['src'][:60], 'Add defer (or async) so it does not delay first paint.', x['line']))
    nodims = [i for i in s.imgs if not i['dims']]
    if nodims:
        out.append(_c('warn', perf, 'Images without width/height', '%d image(s) will shift the layout as they load.' % len(nodims), 'Set width and height on every image (protects your CLS score).'))
    below = [i for i in s.imgs[1:] if not i['lazy']]
    if below:
        out.append(_c('warn', perf, 'Images not lazy-loaded', '%d image(s) after the first could use loading="lazy".' % len(below), 'Add loading="lazy" to below-the-fold images.'))
    size = len(html.encode('utf-8')) / 1024
    out.append(_c('pass' if size < 100 else 'warn', perf, 'HTML weight', '%.1f KB (budget: 100 KB).' % size, '' if size < 100 else 'Trim inline data and unused markup.'))
    total_req = len(s.scripts) + len(re.findall(r'<link[^>]+stylesheet', html, re.I)) + len(s.imgs)
    out.append(_c('pass' if total_req <= 30 else 'warn', perf, 'Request count', '%d linked scripts, styles and images (budget: 30).' % total_req, '' if total_req <= 30 else 'Combine or remove resources you do not need.'))
    return out


def run(request):
    ctx = {'html': '', 'ran': False, 'sample': SAMPLE}
    if request.method != 'POST':
        return ctx
    text = SAMPLE if request.POST.get('use_sample') else (request.POST.get('html') or '')[:120_000]
    ctx['html'], ctx['ran'] = text, True
    if len(text.strip()) < 20 or '<' not in text:
        ctx['error'] = 'Paste some HTML (a full page or a single component), or use the sample.'
        return ctx
    checks = check(text)
    order = {'fail': 0, 'warn': 1, 'pass': 2}
    counts = {k: sum(1 for c in checks if c['status'] == k) for k in order}
    a11y = [c for c in checks if c['area'] == 'Accessibility']
    speed = [c for c in checks if c['area'] != 'Accessibility']

    def grade(items):
        return round(sum({'pass': 1, 'warn': 0.5, 'fail': 0}[c['status']] for c in items) / len(items) * 100) if items else 100
    ctx.update({'a11y': sorted(a11y, key=lambda c: order[c['status']]), 'speed': sorted(speed, key=lambda c: order[c['status']]), 'counts': counts,
                'a11y_score': grade(a11y), 'speed_score': grade(speed), 'using_sample': bool(request.POST.get('use_sample'))})
    ctx['ai'] = ai_slot('forge', {'counts': counts})
    return ctx
