"""Sample market data and scoring for the public Scout demo (/ai-agents/scout/).

The keyword rows come from our own research (KEYWORD.xlsx) and are static: the demo does not crawl the
visitor's site. Rows are (keyword, intent, monthly searches, difficulty 0-100, CPC in USD); None = not measured.
"""
import math
import re

from django.utils.text import slugify

SERVICES = {
    'digital-marketing': {'label': 'Digital Marketing', 'noun': 'digital marketing'},
    'seo': {'label': 'SEO', 'noun': 'SEO'},
}

GOALS = {
    'leads': 'Get more enquiries and leads',
    'awareness': 'Build awareness and authority',
}

KEYWORDS = {
    'digital-marketing': [
        ('Digital Marketing Agencies', None, 60500, None, 48.65),
        ('Digital Marketing Company', 'Commercial', 18100, 62, 31.88),
        ('Digital Marketing Services', 'Commercial', 18100, 63, 69.63),
        ('Digital Marketing Agency Near Me', 'Transactional', 14800, 30, 41.10),
        ('Digital Marketing Near Me', 'Transactional', 12100, 40, 45.30),
        ('Top Digital Marketing Companies', 'Commercial', 9900, 54, 38.59),
        ('Digital Marketing Company Near Me', 'Transactional', 5400, 44, 34.39),
        ('Digital Marketing Services Near Me', 'Transactional', 2400, 30, 41.94),
        ('Digital Marketing Consultant', 'Commercial', 1600, 54, 31.88),
        ('Best Digital Marketing Company', 'Commercial', 1300, 56, 39.43),
        ('Digital Marketing Expert', 'Commercial', 1300, 54, 26.84),
        ('Digital Marketing Solutions', 'Commercial', 880, 48, 26.00),
        ('Best Digital Marketing Services', 'Commercial', 720, 59, 39.43),
        ('Digital Agency Near Me', 'Transactional', 590, 48, 40.27),
        ('Digital Advertising Agencies', None, 390, None, 37.75),
        ('Top Digital Marketing Agencies', 'Commercial', 390, 50, 27.68),
        ('Digital Marketing Services Company', 'Informational', 320, 57, 26.00),
    ],
    'seo': [
        ('SEO Services', 'Commercial', 9900, 62, 38.59),
        ('Search Engine Optimization Digital Marketing', 'Informational', 6600, 73, 46.14),
        ('SEO Agency', 'Commercial', 4400, 67, 55.36),
        ('SEO Company', 'Commercial', 4400, 62, 47.81),
        ('SEO Website', 'Informational', 2900, 92, 44.46),
        ('SEO Agency Near Me', 'Transactional', 2400, 38, 55.36),
        ('Best SEO Agency', 'Commercial', 1600, 66, 59.56),
        ('Best SEO Company', 'Commercial', 1600, 70, 59.56),
        ('Local SEO Services', 'Commercial', 880, 47, 60.40),
    ],
}

# Real city-level rows we have measured. Any other city gets pattern suggestions with no volume figures.
CITY_KEYWORDS = {
    ('digital-marketing', 'kolkata'): [
        ('Digital Marketing Agency in Kolkata', 'Commercial', 4400, 57, 24.33),
        ('Digital Marketing Company in Kolkata', 'Commercial', 3600, 57, 16.78),
        ('Best Digital Marketing Company in Kolkata', 'Commercial', 1600, 50, 23.49),
        ('Best Digital Marketing Agency in Kolkata', 'Commercial', 1000, 56, 26.84),
        ('Top Digital Marketing Agency in Kolkata', 'Commercial', 320, 56, 26.00),
        ('Top Digital Marketing Company in Kolkata', 'Commercial', 140, 43, 22.65),
    ],
}

CITY_PATTERNS = ['{s} agency in {c}', '{s} company in {c}', 'best {s} company in {c}', 'top {s} agency in {c}', '{s} services in {c}']

INTENT_WEIGHT = {
    'leads': {'Transactional': 1.3, 'Commercial': 1.15, 'Informational': 0.7},
    'awareness': {'Transactional': 0.8, 'Commercial': 0.9, 'Informational': 1.3},
}


def _intent(keyword, intent):
    if intent:
        return intent, False
    return ('Transactional' if 'near me' in keyword.lower() else 'Commercial'), True


def _effort(kd):
    if kd is None:
        return 'Unknown'
    if kd < 40:
        return 'Quick win'
    if kd <= 60:
        return 'Medium'
    return 'Long game'


def _page_title(keyword, city):
    title = keyword.title().replace(' Seo', ' SEO')
    if city and city.lower() not in title.lower() and 'near me' not in title.lower():
        title += ' in ' + city
    return '%s | Rizen Digital' % title


def clean_city(raw):
    return re.sub(r'[^A-Za-z .\'-]', '', (raw or '')).strip()[:60]


def build_report(service, city, goal):
    """Return (rows, meta). Rows are dicts ready for the template/CSV, ranked by priority score."""
    if service not in SERVICES:
        service = 'digital-marketing'
    if goal not in GOALS:
        goal = 'leads'
    city = clean_city(city)
    base = list(KEYWORDS[service])
    measured_city = False
    if city:
        city_rows = CITY_KEYWORDS.get((service, city.lower()))
        if city_rows:
            base += city_rows
            measured_city = True
        else:
            noun = SERVICES[service]['noun']
            base += [(p.format(s=noun, c=city), 'Commercial', None, None, None) for p in CITY_PATTERNS]
    rows = []
    for kw, intent, sv, kd, cpc in base:
        kw = kw[0].upper() + kw[1:] if kw else kw
        intent_val, guessed = _intent(kw, intent)
        if sv is not None and sv < 50:
            continue
        kd_eff = 50 if kd is None else kd
        if sv is None:
            score = None
        else:
            raw = math.log10(sv + 1) * (100 - kd_eff) / 100 * INTENT_WEIGHT[goal][intent_val]
            score = raw
        rows.append({
            'keyword': kw, 'intent': intent_val, 'intent_guessed': guessed, 'volume': sv, 'difficulty': kd,
            'cpc': cpc, 'effort': _effort(kd), 'score': score,
            'slug': slugify(kw), 'title': _page_title(kw, city if not measured_city else ''),
            'estimated': sv is None,
        })
    top = max((r['score'] for r in rows if r['score'] is not None), default=1) or 1
    for r in rows:
        r['priority'] = round(r['score'] / top * 100) if r['score'] is not None else None
    rows.sort(key=lambda r: (r['priority'] is None, -(r['priority'] or 0), -(r['volume'] or 0)))
    for i, r in enumerate(rows, 1):
        r['rank'] = i
    meta = {'service': service, 'service_label': SERVICES[service]['label'], 'city': city, 'goal': goal,
            'measured_city': measured_city,
            'total_volume': sum(r['volume'] or 0 for r in rows),
            'quick_wins': sum(1 for r in rows if r['effort'] == 'Quick win')}
    return rows, meta


def group_by_intent(rows):
    groups = []
    for name in ('Transactional', 'Commercial', 'Informational'):
        sel = [r for r in rows if r['intent'] == name]
        if sel:
            groups.append({'name': name, 'count': len(sel), 'volume': sum(r['volume'] or 0 for r in sel)})
    return groups
