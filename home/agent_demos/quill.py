"""Quill: analyse a pasted draft against a target keyword, and build a content brief from a topic."""
import re
from html import unescape

from django.utils.text import slugify

from . import ai_slot, clip

SAMPLE = (
    "Choosing an SEO agency in Kolkata can feel like guesswork. Most agencies promise page-one rankings, but few explain how.\n\n"
    "## What an SEO agency actually does\n"
    "A good agency starts with research. We look at what your customers search for, which pages of yours already rank, and where competitors are ahead. "
    "In our experience, most small businesses have three or four pages that could rank with a few weeks of focused work.\n\n"
    "## How much does SEO cost?\n"
    "Pricing depends on competition and scope. Local businesses often start at a modest monthly retainer, while national campaigns cost more. "
    "Ask every agency to show a sample report before you sign.\n\n"
    "## How to choose\n"
    "Look for clear reporting, honest timelines and case studies you can verify. Avoid anyone who guarantees a ranking."
)

STOP = set('a an the and or but of to in on for with at by from as is are was were be been it this that these those we you your our i they he she'.split())


def _syllables(word):
    word = re.sub(r'[^a-z]', '', word.lower())
    if not word:
        return 0
    groups = re.findall(r'[aeiouy]+', word)
    n = len(groups)
    if word.endswith('e') and not word.endswith(('le', 'ee')) and n > 1:
        n -= 1
    return max(1, n)


def _plain(text):
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', text, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return unescape(text)


def analyse(draft, keyword):
    headings = [h.strip('# ').strip() for h in re.findall(r'^\s*#{1,4}\s+.+$', draft, flags=re.M)]
    headings += [unescape(re.sub(r'<[^>]+>', '', h)).strip() for h in re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', draft, flags=re.S | re.I)]
    body = re.sub(r'^\s*#{1,4}\s+.+$', ' ', _plain(draft), flags=re.M)
    words = re.findall(r"[A-Za-z0-9']+", body)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', re.sub(r'\s+', ' ', body)) if len(s.split()) >= 3]
    n_words, n_sent = len(words), max(1, len(sentences))
    syl = sum(_syllables(w) for w in words)
    flesch = 206.835 - 1.015 * (n_words / n_sent) - 84.6 * (syl / max(1, n_words))
    long_sent = [s for s in sentences if len(s.split()) > 28]
    passive = sum(1 for s in sentences if re.search(r'\b(is|are|was|were|be|been|being)\s+\w+ed\b', s, re.I))
    kw = keyword.lower().strip()
    lower = ' '.join(words).lower()
    kw_count = len(re.findall(r'\b%s\b' % re.escape(kw), lower)) if kw else 0
    density = kw_count / n_words * 100 if n_words else 0
    first100 = ' '.join(words[:100]).lower()
    checks = []

    def add(status, name, detail, tip=''):
        checks.append({'status': status, 'name': name, 'detail': detail, 'fix': tip})
    add('pass' if n_words >= 600 else 'warn' if n_words >= 300 else 'fail', 'Length', '%d words.' % n_words,
        '' if n_words >= 600 else 'Pages that rank for competitive terms usually cover the topic in 800+ useful words.')
    if kw:
        add('pass' if kw in first100 else 'warn', 'Keyword in the opening', 'Found in the first 100 words.' if kw in first100 else 'Not in the first 100 words.', '' if kw in first100 else 'Mention the topic early so readers and search engines see it straight away.')
        add('pass' if 0.5 <= density <= 2.5 else 'warn', 'Keyword use', '%d mentions (%.1f%% of words).' % (kw_count, density),
            '' if 0.5 <= density <= 2.5 else ('Use the phrase and close variations a little more naturally.' if density < 0.5 else 'Reads as stuffed; use synonyms and related terms.'))
        in_h = any(kw in h.lower() for h in headings)
        add('pass' if in_h else 'warn', 'Keyword in a heading', 'Yes.' if in_h else 'No heading contains it.', '' if in_h else 'Work the phrase into at least one H2.')
    add('pass' if len(headings) >= 3 else 'warn', 'Structure', '%d headings.' % len(headings), '' if len(headings) >= 3 else 'Break the text into sections with descriptive headings.')
    add('pass' if flesch >= 60 else 'warn' if flesch >= 45 else 'fail', 'Readability', 'Flesch reading ease %d (%s).' % (flesch, 'easy' if flesch >= 70 else 'plain English' if flesch >= 60 else 'fairly hard' if flesch >= 45 else 'difficult'),
        '' if flesch >= 60 else 'Shorten sentences and swap long words for simple ones.')
    add('pass' if not long_sent else 'warn', 'Sentence length', 'Average %.0f words per sentence.' % (n_words / n_sent) + (' %d sentence(s) over 28 words.' % len(long_sent) if long_sent else ''), '' if not long_sent else 'Split the very long sentences.')
    add('pass' if passive / n_sent < 0.2 else 'warn', 'Active voice', '%d possible passive sentence(s).' % passive, '' if passive / n_sent < 0.2 else 'Prefer active phrasing: "we audited the site" over "the site was audited".')
    low = body.lower()
    experience = bool(re.search(r"\b(we|our|i|my)\b", low)) and bool(re.search(r"\b(in our experience|we found|we saw|we tested|our clients|i have|we have|case study)\b", low))
    data_pts = len(re.findall(r'\b\d[\d,.]*\s?(%|percent|x|k|lakh|crore|days|weeks|months)\b', low))
    sources = len(re.findall(r'https?://|according to|source:|study|report by', draft, flags=re.I))
    add('pass' if experience else 'warn', 'First-hand experience', 'Signals of real experience found.' if experience else 'No first-hand experience signals.', '' if experience else 'Add what you did, tested or saw yourself. This is the "E" in E-E-A-T.')
    add('pass' if data_pts else 'warn', 'Specific numbers', '%d specific figure(s).' % data_pts, '' if data_pts else 'Concrete numbers and results build trust.')
    add('pass' if sources else 'warn', 'Sources', '%d source reference(s).' % sources, '' if sources else 'Link to or name the sources behind key claims.')
    weights = {'pass': 1, 'warn': 0.5, 'fail': 0}
    score = round(sum(weights[c['status']] for c in checks) / len(checks) * 100)
    return {'words': n_words, 'flesch': round(flesch), 'headings': headings, 'checks': checks, 'score': score,
            'keyword_count': kw_count, 'density': round(density, 1)}


def build_brief(topic, keyword, city, audience):
    k = keyword or topic
    kc = k.title()
    intent = ('commercial' if re.search(r'\b(best|top|agency|company|services?|cost|price|hire|near me|vs|compare)\b', k, re.I)
              else 'how-to' if re.search(r'\b(how|guide|steps?|tips|learn)\b', k, re.I) else 'informational')
    loc = ' in %s' % city if city else ''
    titles = {
        'commercial': ['%s%s: What to Look For Before You Hire' % (kc, loc), 'How to Choose %s%s (A Practical Checklist)' % (kc, loc), '%s%s: Costs, Questions and Red Flags' % (kc, loc)],
        'how-to': ['How to %s: A Step-by-Step Guide' % k.replace('how to ', '').title(), '%s: The Complete Guide' % kc, '%s: Mistakes to Avoid and What Works' % kc],
        'informational': ['What Is %s? A Plain-English Guide' % kc, '%s Explained: What It Means for %s' % (kc, audience or 'Your Business'), '%s: What Matters and What Doesn\'t' % kc],
    }[intent]
    outline = {
        'commercial': ['What %s actually includes' % k, 'How much %s costs%s' % (k, loc), 'How to compare providers: the questions to ask', 'Red flags and unrealistic promises', 'What results to expect, and when', 'Proof: a real example with numbers', 'Frequently asked questions', 'Next step: how to get a quote'],
        'how-to': ['What you need before you start', 'Step 1 to Step 5, one heading per step', 'Common mistakes and how to fix them', 'Tools that help (with honest pros and cons)', 'A worked example', 'Frequently asked questions', 'Summary and next action'],
        'informational': ['The short answer', 'Why it matters%s' % loc, 'How it works, in plain English', 'Real examples', 'Myths and misunderstandings', 'Frequently asked questions', 'Where to go next'],
    }[intent]
    faq = ['What is %s?' % k, 'How much does %s cost%s?' % (k, loc), 'How long does %s take to show results?' % k, 'Is %s worth it for a small business?' % k, 'How do I choose the right %s%s?' % (k, loc)]
    target = {'commercial': 1400, 'how-to': 1800, 'informational': 1200}[intent]
    eeat = ['Named author with a short bio and relevant credentials', 'At least one first-hand example, screenshot or result from your own work', 'Two or more sources for statistics or claims', 'Date published and last updated', 'A clear, honest call to action (no guaranteed rankings)']
    links = ['Your service page for %s' % k, 'A relevant case study', 'One related blog post that supports this topic']
    return {'intent': intent, 'titles': titles, 'outline': outline, 'faq': faq, 'target_words': target, 'eeat': eeat, 'links': links,
            'slug': slugify(k)[:60], 'meta': ('%s%s: what it involves, what it costs and how to choose. A clear, honest guide.' % (kc, loc))[:155]}


def run(request):
    ctx = {'topic': '', 'keyword': '', 'city': '', 'audience': '', 'draft': '', 'ran': False, 'sample': SAMPLE}
    if request.method != 'POST':
        return ctx
    p = request.POST
    ctx.update({'topic': clip(p.get('topic'), 120), 'keyword': clip(p.get('keyword'), 100), 'city': clip(p.get('city'), 60),
                'audience': clip(p.get('audience'), 80), 'draft': (p.get('draft') or '')[:20000]})
    if p.get('use_sample'):
        ctx['draft'], ctx['keyword'] = SAMPLE, ctx['keyword'] or 'seo agency'
    ctx['ran'] = True
    if not (ctx['keyword'] or ctx['topic']):
        ctx['error'] = 'Enter a target keyword or topic.'
        return ctx
    ctx['brief'] = build_brief(ctx['topic'], ctx['keyword'], ctx['city'], ctx['audience'])
    if ctx['draft'].strip():
        ctx['report'] = analyse(ctx['draft'], ctx['keyword'] or ctx['topic'])
    ctx['ai'] = ai_slot('quill', {'brief': ctx['brief'], 'draft_words': ctx.get('report', {}).get('words')})
    return ctx
