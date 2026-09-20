"""Echo: read a lead enquiry, qualify it, and draft the instant first reply and follow-up plan."""
import datetime as dt
import re
import time

from . import ai_slot

SERVICES = {
    'SEO': ['seo', 'search engine', 'rank', 'google ranking', 'organic', 'keywords', 'show up on google', 'showing up on google'],
    'Google Ads / PPC': ['google ads', 'adwords', 'ppc', 'paid ads', 'ad campaign', 'facebook ads', 'meta ads'],
    'Website design & development': ['website', 'web design', 'web development', 'landing page', 'wordpress', 'redesign', 'ecommerce', 'e-commerce', 'online store'],
    'Social media marketing': ['social media', 'instagram', 'facebook', 'linkedin', 'content calendar'],
    'Google Business Profile / local SEO': ['google business', 'google my business', 'gmb', 'local seo', 'near me', 'maps'],
    'Content & branding': ['content', 'blog', 'brand', 'logo', 'copywriting'],
}

SAMPLES = {
    'hot': "Hi, I'm Priya Sharma from Sharma Dental Clinic in Salt Lake, Kolkata. Our website is not showing up on Google and we need SEO help urgently. "
           "We have a budget of about Rs 25,000 per month and want to start this week. Can someone call me today? 98300 12345, priya@sharmadental.example",
    'warm': "Hello, we run a small boutique and are thinking about getting an online store built sometime next quarter. Could you tell me roughly what it costs? Thanks, Rahul",
    'cold': "Do you do free logo design? Also can you guarantee first page ranking in 3 days? Send price list.",
}
RUPEE = '₹'


def _extract(text):
    low = text.lower()
    out = {}
    m = re.search(r"(?i:i'?m|i am|my name is|this is)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", text)
    out['name'] = m.group(1) if m else ''
    m = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    out['email'] = m.group(0) if m else ''
    m = re.search(r'(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)', text)
    out['phone'] = m.group(0).strip() if m else ''
    budget = None
    m = re.search(r'(?:rs\.?|inr|%s|\$|usd)\s?([\d,]+(?:\.\d+)?)\s?(k|lakh|lakhs|lac|l)?' % RUPEE, low)
    if m:
        val = float(m.group(1).replace(',', ''))
        unit = m.group(2) or ''
        val *= 1000 if unit == 'k' else 100000 if unit in ('lakh', 'lakhs', 'lac', 'l') else 1
        budget = int(val)
    else:
        m = re.search(r'([\d.]+)\s?(lakh|lakhs|lac|k)\b', low)
        if m:
            budget = int(float(m.group(1)) * (1000 if m.group(2) == 'k' else 100000))
    out['budget'] = budget
    out['services'] = [s for s, kws in SERVICES.items() if any(k in low for k in kws)]
    if re.search(r'\b(urgent|urgently|asap|immediately|today|this week|right away|right now)\b', low):
        out['timeline'] = 'Immediate (this week)'
    elif re.search(r'\b(this month|next week|soon|within a month)\b', low):
        out['timeline'] = 'Soon (this month)'
    elif re.search(r'\b(next quarter|few months|later|sometime|thinking about|exploring)\b', low):
        out['timeline'] = 'Later (exploring)'
    else:
        out['timeline'] = 'Not stated'
    m = re.search(r"\b((?:[A-Z][\w&']+\s+){1,3}(?:Clinic|Studio|Store|Boutique|Restaurant|Cafe|Traders|Enterprises|Academy|Institute|Hospital|Agency))", text)
    out['company'] = m.group(1).strip() if m else ''
    m = re.search(r'\bin\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)(?:,\s*([A-Z][a-z]+))?', text)
    out['location'] = (m.group(2) or m.group(1)) if m else ''
    out['red_flags'] = [f for f, pat in [('Asks for a guaranteed ranking', r'guarantee'), ('Expects free work', r'\bfree\b'), ('Unrealistic timeline', r'in \d days?\b')] if re.search(pat, low)]
    return out


def _score(f, text):
    pts, why = 0, []

    def add(n, reason):
        nonlocal pts
        pts += n
        why.append(('+' if n >= 0 else '') + '%d %s' % (n, reason))
    if f['services']:
        add(20, 'names a specific service (%s)' % f['services'][0])
    if f['budget']:
        add(25 if f['budget'] >= 15000 else 12, 'shares a budget (Rs %s)' % format(f['budget'], ','))
    if f['timeline'].startswith('Immediate'):
        add(25, 'wants to start immediately')
    elif f['timeline'].startswith('Soon'):
        add(15, 'plans to start soon')
    elif f['timeline'].startswith('Later'):
        add(4, 'still exploring')
    if re.search(r'\b(costs?|price|pricing|quote|how much|rates?|charges?)\b', text.lower()):
        add(15, 'asks about pricing')
    if f['phone'] or f['email']:
        add(15, 'left contact details')
    if f['company']:
        add(10, 'gave a business name')
    if len(text.split()) >= 25:
        add(5, 'wrote a detailed message')
    if f['red_flags']:
        add(-15 * len(f['red_flags']), 'red flag: ' + '; '.join(f['red_flags']).lower())
    pts = max(0, min(100, pts))
    return pts, ('Hot' if pts >= 70 else 'Warm' if pts >= 40 else 'Cold'), why


def _slots():
    d, slots = dt.date.today(), []
    while len(slots) < 3:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            slots.append('%s, %s IST' % (d.strftime('%a %d %b'), '3:00 pm' if len(slots) == 1 else '11:00 am'))
    return slots


def _reply(f, tag):
    name = f['name'].split()[0] if f['name'] else 'there'
    first = f['services'][0] if f['services'] else ''
    svc = (first if any(ch.isupper() for ch in first[1:]) else first.lower()) if first else 'what you are looking for'
    biz = ' for %s' % f['company'] if f['company'] else ''
    if tag == 'Cold' and f['red_flags']:
        return ("Hi %s, thanks for getting in touch with Rizen Digital. To be upfront: no honest agency can guarantee a ranking, and we do not offer free design work. "
                "What we can do is a free 20-minute call to understand your goals and tell you what is realistic. Would you like a time this week? Best, Team Rizen Digital" % name)
    ask = []
    if not f['services']:
        ask.append('which service you are interested in')
    if not f['budget']:
        ask.append('a rough monthly budget')
    if f['timeline'] == 'Not stated':
        ask.append('when you would like to start')
    if not (f['phone'] or f['email']):
        ask.append('the best number or email to reach you')
    body = "Hi %s, thanks for reaching out to Rizen Digital. We would be glad to help with %s%s." % (name, svc, biz)
    if tag == 'Hot':
        body += " Since you would like to move quickly, I can hold a call slot for you: %s. Reply with the one that suits you and we will send a calendar invite." % ' or '.join(_slots()[:2])
    else:
        body += " A good next step is a free 20-minute call to understand your goals and share honest options."
    if ask:
        body += " To prepare, could you tell us %s?" % (ask[0] if len(ask) == 1 else ', '.join(ask[:-1]) + ' and ' + ask[-1])
    return body + " Best, Team Rizen Digital"


def run(request):
    ctx = {'text': '', 'ran': False, 'samples': SAMPLES}
    if request.method != 'POST':
        return ctx
    text = (request.POST.get('text') or '').strip()
    if request.POST.get('sample') in SAMPLES:
        text = SAMPLES[request.POST['sample']]
    ctx['text'] = text[:3000]
    ctx['ran'] = True
    if len(text.split()) < 4:
        ctx['error'] = 'Paste a real enquiry (at least a sentence) or pick one of the samples.'
        return ctx
    t0 = time.perf_counter()
    f = _extract(ctx['text'])
    pts, tag, why = _score(f, ctx['text'])
    missing = [label for label, ok in [('Service', bool(f['services'])), ('Budget', bool(f['budget'])), ('Timeline', f['timeline'] != 'Not stated'), ('Contact details', bool(f['phone'] or f['email']))] if not ok]
    plan = {'Hot': [('Now', 'Send instant reply with call slots'), ('+15 min', 'Alert a human specialist to call'), ('+1 day', 'Follow up if no reply')],
            'Warm': [('Now', 'Send instant reply with qualifying questions'), ('+1 day', 'Follow up with a relevant case study'), ('+4 days', 'Offer a free audit')],
            'Cold': [('Now', 'Send a polite reply that sets expectations'), ('+7 days', 'One light follow-up, then stop')]}[tag]
    ctx.update({'f': f, 'score': pts, 'tag': tag, 'why': why, 'missing': missing, 'reply': _reply(f, tag), 'plan': plan, 'slots': _slots(),
                'ms': max(1, int((time.perf_counter() - t0) * 1000)),
                'route': {'Hot': 'Human call within 15 minutes', 'Warm': 'Nurture sequence, review in 24 hours', 'Cold': 'Auto-reply only, low priority'}[tag]})
    ctx['ai'] = ai_slot('echo', {'enquiry': ctx['text'], 'fields': f, 'tag': tag})
    return ctx
