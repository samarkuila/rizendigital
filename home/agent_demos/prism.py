"""Prism: a starter brand kit (palette with real contrast checks, voice guide, taglines, monogram concepts)."""
import colorsys

from django.utils.html import escape

from . import ai_slot, clip

INDUSTRIES = {
    'agency': ('Marketing / tech', 225), 'health': ('Health / wellness', 165), 'food': ('Food / hospitality', 18),
    'realestate': ('Real estate', 200), 'education': ('Education', 265), 'retail': ('Retail / fashion', 335),
    'finance': ('Finance / legal', 210), 'creative': ('Creative / media', 285),
}

SCALE = {'1': 'Very', '2': 'Fairly', '3': 'Balanced', '4': 'Fairly', '5': 'Very'}


def _hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0, min(1, l)), max(0, min(1, s)))
    return '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))


def _lum(hexcolor):
    def chan(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def palette(hue, formal, playful, bold):
    sat = 0.45 + 0.09 * bold + 0.04 * playful
    light = 0.44 - 0.02 * bold + 0.01 * playful
    ink = _hex(hue, 0.35, 0.11)
    paper = _hex(hue, 0.45, 0.97)
    swatches = [
        ('Primary', _hex(hue, sat, light)),
        ('Secondary', _hex(hue + (24 if formal >= 3 else 40), sat * 0.85, light + 0.08)),
        ('Accent', _hex(hue + 180 + (playful - 3) * 8, min(0.95, sat + 0.2), 0.55)),
        ('Ink', ink),
        ('Paper', paper),
    ]
    out = []
    for name, hx in swatches:
        white, dark = contrast(hx, '#ffffff'), contrast(hx, ink)
        text, ratio = ('#ffffff', white) if white >= dark else (ink, dark)
        out.append({'name': name, 'hex': hx.upper(), 'text': text, 'ratio': round(ratio, 1), 'aa': ratio >= 4.5, 'aaa': ratio >= 7})
    return out


def monogram(name, colors):
    letters = ''.join(w[0] for w in name.split()[:2]).upper() or name[:1].upper() or 'R'
    p, a = colors[0]['hex'], colors[2]['hex']
    t = colors[0]['text']
    return [
        '<svg viewBox="0 0 120 120" role="img" aria-label="Rounded monogram"><rect width="120" height="120" rx="30" fill="%s"/><text x="60" y="76" font-family="Poppins,Arial,sans-serif" font-size="46" font-weight="700" text-anchor="middle" fill="%s">%s</text></svg>' % (p, t, escape(letters)),
        '<svg viewBox="0 0 120 120" role="img" aria-label="Circle monogram"><circle cx="60" cy="60" r="54" fill="none" stroke="%s" stroke-width="8"/><circle cx="60" cy="60" r="34" fill="%s"/><text x="60" y="72" font-family="Poppins,Arial,sans-serif" font-size="32" font-weight="700" text-anchor="middle" fill="%s">%s</text></svg>' % (a, p, t, escape(letters)),
        '<svg viewBox="0 0 120 120" role="img" aria-label="Angled monogram"><polygon points="60,6 114,60 60,114 6,60" fill="%s"/><polygon points="60,26 94,60 60,94 26,60" fill="%s"/><text x="60" y="70" font-family="Poppins,Arial,sans-serif" font-size="26" font-weight="700" text-anchor="middle" fill="%s">%s</text></svg>' % (p, a, colors[2]['text'], escape(letters)),
    ]


def voice(name, audience, values, formal, playful, bold):
    aud = audience or 'your customers'
    v = values or ['clarity', 'trust', 'results']
    principles = [
        ('Speak like %s' % ('a trusted advisor' if formal <= 2 else 'a helpful friend' if formal >= 4 else 'a knowledgeable colleague'),
         'Address %s directly. %s' % (aud, 'Keep sentences complete and precise.' if formal <= 2 else 'Use contractions and everyday words.' if formal >= 4 else 'Mix plain words with confident, professional phrasing.')),
        ('Keep energy %s' % ('high and lively' if playful >= 4 else 'steady and serious' if playful <= 2 else 'warm but focused'),
         'Humour is %s.' % ('welcome, used lightly' if playful >= 4 else 'rare; let the substance carry the message' if playful <= 2 else 'fine in small doses, never at the customer\'s expense')),
        ('Make claims %s' % ('boldly, with proof' if bold >= 4 else 'carefully, with context' if bold <= 2 else 'clearly, with evidence'),
         'Lead with %s. Back every promise with a number, example or source.' % v[0]),
    ]
    do = ['Use "you" and "we"', 'Name the benefit before the feature', 'Give one clear next step', 'Write for a smart reader in a hurry']
    dont = ['Use jargon without explaining it', 'Promise results you cannot guarantee', 'Use ALL CAPS or stacked exclamation marks', 'Hide the price or the catch']
    taglines = ['%s: %s, made simple.' % (name, v[0].capitalize()), 'Built on %s. Proven by %s.' % (v[0], v[1] if len(v) > 1 else 'results'),
                'For %s who want %s.' % (aud, v[-1]), '%s. %s. %s.' % tuple((v + v + v)[:3][i].capitalize() for i in range(3))]
    if bold >= 4:
        taglines.append('No guesswork. Just %s.' % v[-1])
    if playful >= 4:
        taglines.append('Serious about %s. Relaxed about everything else.' % v[0])
    tone_hi = 'Big news' if bold >= 4 else 'A quick update'
    excl = '!' if playful >= 4 else '.'
    sample = '%s from %s%s We help %s with %s. Here is how it works in three steps, and what it costs.' % (tone_hi, name, excl, aud, v[0])
    return principles, do, dont, taglines, sample


def _level(value):
    return value if value in ('1', '2', '3', '4', '5') else '3'


def run(request):
    g = request.GET
    ctx = {'industries': INDUSTRIES, 'ran': 'run' in g, 'brand': clip(g.get('brand'), 40), 'industry': g.get('industry', 'agency'), 'audience': clip(g.get('audience'), 60),
           'values': clip(g.get('values'), 90), 'formal': _level(g.get('formal')), 'playful': _level(g.get('playful')), 'bold': _level(g.get('bold')), 'scale': SCALE}
    if ctx['industry'] not in INDUSTRIES:
        ctx['industry'] = 'agency'
    if not ctx['ran']:
        return ctx
    name = ctx['brand'] or 'Your Brand'
    formal, playful, bold = int(ctx['formal']), int(ctx['playful']), int(ctx['bold'])
    values = [v.strip() for v in ctx['values'].split(',') if v.strip()][:3]
    pal = palette(INDUSTRIES[ctx['industry']][1], formal, playful, bold)
    principles, do, dont, taglines, sample = voice(name, ctx['audience'], values, formal, playful, bold)
    ctx.update({'name': name, 'palette': pal, 'monograms': monogram(name, pal), 'principles': principles, 'do': do, 'dont': dont, 'taglines': taglines, 'sample': sample,
                'pairs': [(label, fg, bg) for label, fg, bg in (('Ink on Paper', pal[3]['hex'], pal[4]['hex']), ('Paper on Primary', pal[4]['hex'], pal[0]['hex']), ('Ink on Accent', pal[3]['hex'], pal[2]['hex']))]})
    ctx['pairs'] = [{'label': l, 'fg': fg, 'bg': bg, 'ratio': round(contrast(fg, bg), 1), 'aa': contrast(fg, bg) >= 4.5} for l, fg, bg in ctx['pairs']]
    ctx['ai'] = ai_slot('prism', {'brand': name, 'palette': pal})
    return ctx
