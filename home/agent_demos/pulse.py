"""Pulse: a 30-day social content calendar generated from business type, platforms and cadence."""
import csv
import datetime as dt

from django.http import HttpResponse

from . import ai_slot, clip

INDUSTRIES = {
    'agency': ('Marketing agency', ['SEO', 'digital marketing', 'growth', 'brand'], ['#DigitalMarketing', '#SEOTips', '#MarketingStrategy', '#GrowthMarketing', '#Kolkata']),
    'restaurant': ('Restaurant / cafe', ['food', 'fresh', 'menu', 'taste'], ['#Foodie', '#FoodLover', '#Kolkata', '#EatLocal', '#Cafe']),
    'realestate': ('Real estate', ['home', 'property', 'investment', 'neighbourhood'], ['#RealEstate', '#DreamHome', '#PropertyInvestment', '#HomeBuying', '#Kolkata']),
    'clinic': ('Clinic / healthcare', ['health', 'care', 'wellness', 'prevention'], ['#Health', '#Wellness', '#PreventiveCare', '#HealthTips', '#Doctor']),
    'retail': ('Shop / e-commerce', ['new arrivals', 'offers', 'style', 'quality'], ['#ShopLocal', '#NewArrivals', '#OnlineShopping', '#Sale', '#SmallBusiness']),
    'education': ('Coaching / education', ['learning', 'results', 'students', 'skills'], ['#Education', '#Learning', '#StudyTips', '#Skills', '#Students']),
}

PLATFORMS = {
    'instagram': ('Instagram', '19:00', ['Reel', 'Carousel', 'Image', 'Story']),
    'facebook': ('Facebook', '13:00', ['Image', 'Link post', 'Video', 'Poll']),
    'linkedin': ('LinkedIn', '09:00', ['Text post', 'Document carousel', 'Article link', 'Poll']),
    'x': ('X', '12:00', ['Text post', 'Thread', 'Image', 'Poll']),
}

PILLARS = [
    ('Educate', 'Share one useful tip about {topic}. Start with the mistake people make, then the fix.'),
    ('Proof', 'Show a real result, review or before-and-after from a customer. Name the number.'),
    ('Behind the scenes', 'Show how {topic} really gets done: the team, the tools, the messy middle.'),
    ('Offer', 'Make one clear offer for {topic} with a deadline and one way to respond.'),
    ('Engage', 'Ask a question your audience can answer in one line about {topic}.'),
]

HOOKS = {
    'Educate': ['3 mistakes we see with {topic}', 'Stop doing this with {topic}', 'The 60-second guide to {topic}'],
    'Proof': ['What changed for one of our clients', 'Real results, no filters', 'From stuck to steady: a short story'],
    'Behind the scenes': ['A day in the life of our team', 'How we actually do {topic}', 'What goes on behind the screen'],
    'Offer': ['This month only:', 'Book this week and get', 'A small offer for new customers:'],
    'Engage': ['Quick question:', 'Be honest:', 'Which would you pick?'],
}

FIXED_EVENTS = {(1, 1): 'New Year', (1, 26): 'Republic Day', (2, 14): "Valentine's Day", (3, 8): "Women's Day", (4, 22): 'Earth Day', (5, 1): 'Labour Day',
                (8, 15): 'Independence Day', (9, 5): "Teachers' Day", (10, 2): 'Gandhi Jayanti', (11, 14): "Children's Day", (12, 25): 'Christmas'}
WEEKDAYS = {2: (0, 2, 4), 3: (0, 2, 4), 4: (0, 1, 3, 4), 5: (0, 1, 2, 3, 4), 6: (0, 1, 2, 3, 4, 5), 7: tuple(range(7))}


def build(business, industry, platforms, per_week, start):
    label, topics, tags = INDUSTRIES[industry]
    days = WEEKDAYS[per_week]
    rows, n = [], 0
    for i in range(30):
        d = start + dt.timedelta(days=i)
        event = FIXED_EVENTS.get((d.month, d.day), '')
        if d.weekday() not in days and not event:
            continue
        pillar, brief = PILLARS[n % len(PILLARS)]
        topic = topics[n % len(topics)]
        plat_key = platforms[n % len(platforms)]
        pname, best, formats = PLATFORMS[plat_key]
        hook = HOOKS[pillar][(n // len(PILLARS)) % 3].format(topic=topic)
        if event:
            hook = '%s: a note from %s' % (event, business)
            pillar = 'Occasion'
            brief = 'A short, warm message for %s. Keep it human, avoid hard selling.' % event
        rows.append({
            'date': d, 'day': d.strftime('%a'), 'platform': pname, 'time': best + ' IST', 'format': formats[n % len(formats)],
            'pillar': pillar, 'hook': hook, 'brief': brief.format(topic=topic),
            'caption': '%s\n\n%s\n\n%s' % (hook, brief.format(topic=topic).split('. ')[0] + '.', ' '.join(tags[(n % 3):(n % 3) + 3])),
            'event': event,
        })
        n += 1
    return rows


def run(request):
    g = request.GET
    today = dt.date.today()
    ctx = {'industries': INDUSTRIES, 'platforms': PLATFORMS, 'business': clip(g.get('business'), 60), 'industry': g.get('industry', 'agency'),
           'picked': g.getlist('platform') or ['instagram', 'linkedin'], 'per_week': g.get('per_week', '3'), 'start': g.get('start') or today.isoformat(), 'ran': 'run' in g}
    if not ctx['ran']:
        return ctx
    if ctx['industry'] not in INDUSTRIES:
        ctx['industry'] = 'agency'
    picked = [p for p in ctx['picked'] if p in PLATFORMS] or ['instagram']
    ctx['picked'] = picked
    try:
        per_week = int(ctx['per_week'])
    except ValueError:
        per_week = 3
    per_week = per_week if per_week in WEEKDAYS else 3
    ctx['per_week'] = str(per_week)
    try:
        start = dt.date.fromisoformat(ctx['start'])
    except ValueError:
        start = today
    ctx['start'] = start.isoformat()
    business = ctx['business'] or 'your business'
    rows = build(business, ctx['industry'], picked, per_week, start)
    if g.get('format') == 'csv':
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="pulse-calendar.csv"'
        w = csv.writer(resp)
        w.writerow(['Date', 'Day', 'Platform', 'Best time', 'Format', 'Pillar', 'Hook', 'Caption draft'])
        for r in rows:
            w.writerow([r['date'].isoformat(), r['day'], r['platform'], r['time'], r['format'], r['pillar'], r['hook'], r['caption'].replace('\n', ' ')])
        return {'response': resp}
    pillars = {}
    for r in rows:
        pillars[r['pillar']] = pillars.get(r['pillar'], 0) + 1
    ctx.update({'rows': rows, 'pillar_mix': sorted(pillars.items(), key=lambda kv: -kv[1]), 'total': len(rows), 'business_name': business})
    ctx['ai'] = ai_slot('pulse', {'business': business, 'rows': len(rows)})
    return ctx
