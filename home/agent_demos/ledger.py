"""Ledger: ad budget forecast, ad copy that fits Google's limits, and negative-keyword suggestions."""
from . import ai_slot, clip

# Rough India search-ad CPC starting points in rupees. Estimates for planning, not quotes.
INDUSTRIES = {
    'services': ('Local services', 35, 8),
    'agency': ('Agency / B2B services', 90, 6),
    'realestate': ('Real estate', 60, 3),
    'health': ('Health / clinic', 45, 10),
    'education': ('Education / coaching', 30, 9),
    'ecommerce': ('E-commerce', 20, 2.5),
}

NEGATIVES = {
    'Job seekers': ['jobs', 'job', 'career', 'careers', 'salary', 'hiring', 'internship', 'vacancy', 'resume'],
    'Free / DIY': ['free', 'diy', 'how to', 'tutorial', 'template', 'download', 'pdf', 'youtube', 'course', 'training'],
    'Low intent': ['cheap', 'cheapest', 'meaning', 'definition', 'example', 'wikipedia', 'reddit', 'quora'],
    'Wrong product': ['second hand', 'used', 'repair', 'wholesale', 'complaint', 'scam', 'review of', 'login'],
}


def _num(value, default, lo, hi):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return min(hi, max(lo, v))


def _fit(text, limit):
    text = ' '.join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(' ', 1)[0].rstrip(' ,;:-')
    return cut or text[:limit]


def forecast(budget, cpc, cr, close, value, margin):
    def scenario(mult_cpc, mult_cr):
        c, r = cpc * mult_cpc, cr * mult_cr
        clicks = budget / c
        leads = clicks * r / 100
        cust = leads * close / 100
        revenue = cust * value
        return {'clicks': round(clicks), 'leads': round(leads, 1), 'customers': round(cust, 1), 'revenue': round(revenue),
                'cpl': round(budget / leads) if leads else None, 'cpa': round(budget / cust) if cust else None,
                'roas': round(revenue / budget, 2) if budget else 0, 'profit': round(revenue * margin / 100 - budget)}
    return {'cautious': scenario(1.25, 0.75), 'expected': scenario(1, 1), 'strong': scenario(0.85, 1.25)}


def copy(business, service, city, usp, cta):
    place = ' in %s' % city if city else ''
    s = service or 'Services'
    heads = [
        '%s%s' % (s, place), 'Trusted %s Experts' % s, '%s | %s' % (s, business), 'Get a Free Quote Today', usp or 'Results You Can Measure',
        '%s That Get Results' % s, 'Talk to a Specialist', 'No Long Contracts', '%s? Call Now' % s, 'Rated by Local Clients',
    ]
    descs = [
        '%s%s from %s. %s. %s.' % (s, place, business, usp or 'Clear pricing and honest advice', cta or 'Get your free quote'),
        'Looking for %s%s? Speak to %s today. %s.' % (s.lower(), place, business, cta or 'Free consultation, no obligation'),
        'Real people, clear reporting and no hidden fees. %s with %s.' % (cta or 'Book a call', business),
    ]
    out_h = [{'text': _fit(h, 30), 'raw': len(h)} for h in heads]
    out_d = [{'text': _fit(d, 90), 'raw': len(d)} for d in descs]
    for x in out_h:
        x['len'], x['trimmed'] = len(x['text']), x['raw'] > 30
    for x in out_d:
        x['len'], x['trimmed'] = len(x['text']), x['raw'] > 90
    return out_h, out_d


def run(request):
    g = request.GET
    ctx = {'industries': INDUSTRIES, 'ran': 'run' in g, 'industry': g.get('industry', 'services')}
    if ctx['industry'] not in INDUSTRIES:
        ctx['industry'] = 'services'
    label, cpc0, cr0 = INDUSTRIES[ctx['industry']]
    ctx.update({'budget': g.get('budget', '30000'), 'cpc': g.get('cpc', str(cpc0)), 'cr': g.get('cr', str(cr0)), 'close': g.get('close', '20'),
                'value': g.get('value', '15000'), 'margin': g.get('margin', '40'), 'business': clip(g.get('business'), 40),
                'service': clip(g.get('service'), 40), 'city': clip(g.get('city'), 40), 'usp': clip(g.get('usp'), 60), 'cta': clip(g.get('cta'), 40)})
    if not ctx['ran']:
        return ctx
    budget = _num(ctx['budget'], 30000, 1000, 10_000_000)
    cpc = _num(ctx['cpc'], cpc0, 1, 5000)
    cr = _num(ctx['cr'], cr0, 0.1, 60)
    close = _num(ctx['close'], 20, 1, 100)
    value = _num(ctx['value'], 15000, 1, 100_000_000)
    margin = _num(ctx['margin'], 40, 1, 100)
    ctx.update({'budget': int(budget), 'cpc': cpc, 'cr': cr, 'close': close, 'value': int(value), 'margin': margin})
    f = forecast(budget, cpc, cr, close, value, margin)
    exp = f['expected']
    # Break-even CPC: the most you can pay per click and still cover the margin on the expected customers.
    profit_per_click = (cr / 100) * (close / 100) * value * (margin / 100)
    ctx.update({
        'f': f, 'label': INDUSTRIES[ctx['industry']][0], 'daily': round(budget / 30.4), 'break_even_cpc': round(profit_per_click, 1),
        'cpc_ok': cpc <= profit_per_click,
        'verdict': ('At these numbers the campaign is expected to pay for itself.' if exp['profit'] > 0 else
                    'At these numbers the campaign is expected to lose money. Raise the conversion rate, lower the CPC, or raise the value per customer before spending.'),
        'negatives': NEGATIVES,
    })
    business = ctx['business'] or 'Your Business'
    ctx['heads'], ctx['descs'] = copy(business, ctx['service'], ctx['city'], ctx['usp'], ctx['cta'])
    ctx['ai'] = ai_slot('ledger', {'forecast': f})
    return ctx
