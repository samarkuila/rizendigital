"""Vega: turn a pasted daily CSV (or the built-in sample) into charts, change checks and anomaly alerts."""
import csv
import datetime as dt
import io
import random
import statistics

from django.utils.html import escape

from home import google_updates_data as gud

from . import ai_slot

ALIASES = {
    'date': 'date', 'day': 'date',
    'sessions': 'sessions', 'visits': 'sessions', 'users': 'sessions', 'traffic': 'sessions',
    'clicks': 'clicks', 'impressions': 'impressions', 'conversions': 'conversions', 'leads': 'conversions', 'goals': 'conversions',
}
MAX_DAYS = 400


def sample_csv():
    """90 days of plausible traffic that dips after a real core-update date, so the demo has a story to tell."""
    rng = random.Random(11)
    end = dt.date(2026, 6, 30)
    start = end - dt.timedelta(days=89)
    drop_day = dt.date(2026, 5, 21)  # start of the May 2026 core update in google_updates_data
    lines = ['date,sessions,clicks,impressions,conversions']
    for i in range(90):
        d = start + dt.timedelta(days=i)
        base = 420 + i * 2.2
        base *= 0.78 if d >= drop_day else 1
        base *= 0.72 if d.weekday() >= 5 else 1
        s = int(base * rng.uniform(0.88, 1.12))
        imp = int(s * rng.uniform(11, 13))
        clk = int(s * rng.uniform(0.34, 0.4))
        conv = int(s * rng.uniform(0.02, 0.035))
        lines.append('%s,%d,%d,%d,%d' % (d.isoformat(), s, clk, imp, conv))
    return '\n'.join(lines)


def parse(text):
    text = (text or '').strip('﻿\r\n ')
    if not text:
        return None, 'Paste a CSV with a date column and at least one metric, or use the sample data.'
    first = text.splitlines()[0]
    delim = '\t' if '\t' in first else ';' if first.count(';') > first.count(',') else ','
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    if len(rows) < 15:
        return None, 'Need a header row and at least 14 days of data.'
    headers = [ALIASES.get(h.strip().lower().replace(' ', '_')) for h in rows[0]]
    if 'date' not in headers:
        return None, 'Could not find a "date" column in the first row.'
    metrics = [m for m in dict.fromkeys(h for h in headers if h and h != 'date')]
    if not metrics:
        return None, 'No metric columns found. Use names like sessions, clicks, impressions or conversions.'
    data = {}
    for r in rows[1:MAX_DAYS + 1]:
        rec = dict(zip(headers, r))
        try:
            d = dt.date.fromisoformat(rec['date'].strip()[:10])
        except (ValueError, KeyError):
            continue
        vals = {}
        for m in metrics:
            try:
                vals[m] = float((rec.get(m) or '0').replace(',', ''))
            except ValueError:
                vals[m] = 0.0
        data[d] = vals
    if len(data) < 14:
        return None, 'Fewer than 14 valid dated rows were found. Dates should look like 2026-06-30.'
    days = sorted(data)
    return {'days': days, 'series': {m: [data[d][m] for d in days] for m in metrics}, 'metrics': metrics}, None


def _chart(days, values, flags, updates, w=760, h=190, pad=(38, 12, 10, 26)):
    left, right, top, bottom = pad
    lo, hi = 0, max(values) * 1.1 or 1
    n = len(values)

    def x(i):
        return left + (w - left - right) * i / max(1, n - 1)

    def y(v):
        return top + (h - top - bottom) * (1 - (v - lo) / (hi - lo))
    parts = ['<svg viewBox="0 0 %d %d" role="img" class="vg-chart" preserveAspectRatio="xMidYMid meet">' % (w, h)]
    for t in range(0, 5):
        v = hi * t / 4
        parts.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="vg-grid"/><text x="%d" y="%.1f" class="vg-tick" text-anchor="end">%s</text>' % (left, w - right, y(v), y(v), left - 6, y(v) + 4, _short(v)))
    for u in updates:
        i = next((k for k, d in enumerate(days) if d >= u['start']), None)
        if i is not None:
            parts.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="vg-update"/><text x="%.1f" y="%d" class="vg-utext">%s</text>' % (x(i), x(i), top, h - bottom, x(i) + 3, top + 9, escape(u['label'])))
    pts = ' '.join('%.1f,%.1f' % (x(i), y(v)) for i, v in enumerate(values))
    parts.append('<polyline points="%s" class="vg-line"/>' % pts)
    for i in flags:
        parts.append('<circle cx="%.1f" cy="%.1f" r="4" class="vg-flag"/>' % (x(i), y(values[i])))
    for k in (0, n // 2, n - 1):
        parts.append('<text x="%.1f" y="%d" class="vg-tick" text-anchor="%s">%s</text>' % (x(k), h - 8, 'start' if k == 0 else 'end' if k == n - 1 else 'middle', days[k].strftime('%d %b')))
    parts.append('</svg>')
    return ''.join(parts)


def _short(v):
    return '%.1fk' % (v / 1000) if v >= 10000 else '%d' % v


def _anomalies(values):
    flags = []
    for i in range(14, len(values)):
        window = values[i - 14:i]
        sd = statistics.pstdev(window)
        mean = statistics.fmean(window)
        if sd and abs(values[i] - mean) / sd > 2.6 and abs(values[i] - mean) / max(mean, 1) > 0.25:
            flags.append(i)
    return flags


def analyse(parsed):
    days, series = parsed['days'], parsed['series']
    n = len(days)
    half = n // 2
    updates = [{'start': u['start'], 'label': u['name'].replace(' core update', ' core').replace(' spam update', ' spam'), 'name': u['name'], 'type': u['type']}
               for u in gud.build_updates() if days[0] < u['start'] <= days[-1] and u['type'] in ('core', 'spam')]
    charts, cards, alerts, notes = [], [], [], []
    for m in parsed['metrics']:
        v = series[m]
        prev, cur = sum(v[:half]), sum(v[half:])
        change = (cur - prev) / prev * 100 if prev else 0
        flags = _anomalies(v)
        charts.append({'metric': m.title(), 'svg': _chart(days, v, flags, updates if m in ('sessions', 'clicks') else []), 'flags': len(flags)})
        cards.append({'metric': m.title(), 'total': int(sum(v)), 'avg': int(sum(v) / n), 'change': round(change, 1), 'up': change >= 0})
        for i in flags[:3]:
            base = statistics.fmean(v[i - 14:i])
            alerts.append({'date': days[i], 'metric': m.title(), 'value': int(v[i]), 'base': int(base), 'pct': round((v[i] - base) / base * 100) if base else 0})
        if m == 'sessions' and updates:
            for u in updates:
                i = next(k for k, d in enumerate(days) if d >= u['start'])
                before, after = v[max(0, i - 14):i], v[i:i + 14]
                if len(before) >= 7 and len(after) >= 7:
                    b, a = statistics.fmean(before), statistics.fmean(after)
                    pct = (a - b) / b * 100 if b else 0
                    notes.append({'update': u['name'], 'date': u['start'], 'pct': round(pct, 1), 'verdict': 'lost' if pct <= -10 else 'gained' if pct >= 10 else 'held steady'})
    ratios = []
    if 'clicks' in series and 'impressions' in series:
        ctr = sum(series['clicks']) / max(1, sum(series['impressions'])) * 100
        ratios.append(('Click-through rate', '%.1f%%' % ctr))
    if 'conversions' in series and 'sessions' in series:
        ratios.append(('Conversion rate', '%.2f%%' % (sum(series['conversions']) / max(1, sum(series['sessions'])) * 100)))
    weekday = [statistics.fmean([v for d, v in zip(days, series[parsed['metrics'][0]]) if d.weekday() == k] or [0]) for k in range(7)]
    best = max(range(7), key=lambda k: weekday[k])
    return {'range': (days[0], days[-1]), 'n': n, 'cards': cards, 'charts': charts, 'alerts': sorted(alerts, key=lambda a: a['date'], reverse=True)[:6],
            'notes': notes, 'ratios': ratios, 'best_day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][best]}


def run(request):
    ctx = {'csv': '', 'ran': False}
    if request.method != 'POST':
        return ctx
    text = sample_csv() if request.POST.get('use_sample') else (request.POST.get('csv') or '')[:200_000]
    ctx['csv'] = text
    ctx['ran'] = True
    parsed, err = parse(text)
    if err:
        ctx['error'] = err
        return ctx
    ctx['report'] = analyse(parsed)
    ctx['using_sample'] = bool(request.POST.get('use_sample'))
    ctx['ai'] = ai_slot('vega', {'cards': ctx['report']['cards'], 'notes': ctx['report']['notes']})
    return ctx
