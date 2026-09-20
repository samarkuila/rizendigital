from unittest import mock

from django.core.cache import cache
from django.test import TestCase


class AgentDemoTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_every_agent_page_loads_and_is_linked(self):
        from home import agent_demos
        for slug in agent_demos.SLUGS:
            self.assertEqual(self.client.get('/ai-agents/%s/' % slug).status_code, 200, slug)
        self.assertEqual(self.client.get('/ai-agents/nobody/').status_code, 404)
        self.assertContains(self.client.get('/ai-agents/'), '/ai-agents/atlas/')

    def test_sitemap_lists_demos(self):
        self.assertContains(self.client.get('/sitemap.xml'), '/ai-agents/forge/')

    # ---- Atlas
    def test_atlas_blocks_private_and_odd_targets(self):
        from home.agent_demos import _fetch
        for bad in ('http://127.0.0.1', 'localhost', 'http://169.254.169.254/latest', 'http://10.0.0.5', 'http://[::1]/',
                    'file:///etc/passwd', 'https://example.com:8443', 'http://user:pw@example.com'):
            with self.assertRaises(_fetch.FetchError, msg=bad):
                _fetch.fetch(bad)

    def test_atlas_audits_a_page(self):
        html = (b'<!doctype html><html lang="en"><head><title>Rizen Digital SEO and Marketing Agency Kolkata</title>'
                b'<meta name="viewport" content="width=device-width"><link rel="canonical" href="https://x.test/"></head>'
                b'<body><h1>Hi</h1><img src="a.png"></body></html>')
        res = {'url': 'https://x.test/', 'status': 200, 'headers': {'content-type': 'text/html'}, 'body': html, 'truncated': False,
               'ms': 120, 'chain': [{'url': 'https://x.test/', 'status': 200}], 'https': True}
        with mock.patch('home.agent_demos._fetch.fetch', return_value=res):
            r = self.client.get('/ai-agents/atlas/', {'url': 'x.test'})
        self.assertEqual(r.status_code, 200)
        names = {c['name']: c['status'] for c in r.context['checks']}
        self.assertEqual(names['Main heading (H1)'], 'pass')
        self.assertEqual(names['Meta description'], 'fail')
        self.assertEqual(names['Image alt text'], 'warn')

    def test_atlas_errors_are_friendly_and_rate_limited(self):
        self.assertContains(self.client.get('/ai-agents/atlas/', {'url': 'http://127.0.0.1'}), 'private network')
        for _ in range(10):
            r = self.client.get('/ai-agents/atlas/', {'url': 'http://127.0.0.1'})
        self.assertContains(r, 'several audits')

    # ---- Quill
    def test_quill_brief_and_report(self):
        r = self.client.post('/ai-agents/quill/', {'keyword': 'seo agency', 'city': 'Kolkata', 'use_sample': '1'})
        self.assertEqual(r.context['brief']['intent'], 'commercial')
        self.assertGreater(r.context['report']['words'], 80)
        self.assertGreater(r.context['report']['score'], 0)

    def test_quill_requires_keyword(self):
        self.assertContains(self.client.post('/ai-agents/quill/', {'draft': 'hello there'}), 'Enter a target keyword')

    # ---- Pulse
    def test_pulse_calendar_and_csv(self):
        q = {'run': 1, 'business': 'Sharma Dental', 'industry': 'clinic', 'per_week': '3', 'start': '2026-08-10', 'platform': ['instagram', 'linkedin']}
        rows = self.client.get('/ai-agents/pulse/', q).context['rows']
        self.assertTrue(12 <= len(rows) <= 15)
        self.assertTrue(any(x['event'] == 'Independence Day' for x in rows))
        c = self.client.get('/ai-agents/pulse/', {**q, 'format': 'csv'})
        self.assertEqual(c['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('Caption draft', c.content.decode())

    def test_pulse_bad_input_is_safe(self):
        r = self.client.get('/ai-agents/pulse/', {'run': 1, 'industry': 'zzz', 'per_week': 'x', 'start': 'nope', 'platform': ['bogus']})
        self.assertEqual(r.status_code, 200)

    # ---- Ledger
    def test_ledger_math(self):
        r = self.client.get('/ai-agents/ledger/', {'run': 1, 'budget': '30000', 'cpc': '30', 'cr': '10', 'close': '20', 'value': '10000', 'margin': '50'})
        e = r.context['f']['expected']
        self.assertEqual((e['clicks'], e['leads'], e['customers'], e['revenue'], e['profit']), (1000, 100.0, 20.0, 200000, 70000))
        self.assertEqual(r.context['break_even_cpc'], 100.0)

    def test_ledger_ad_copy_respects_limits(self):
        r = self.client.get('/ai-agents/ledger/', {'run': 1, 'business': 'A Very Long Business Name Pvt Ltd', 'service': 'Comprehensive Teeth Whitening Treatment', 'city': 'Kolkata'})
        self.assertTrue(all(h['len'] <= 30 for h in r.context['heads']))
        self.assertTrue(all(d['len'] <= 90 for d in r.context['descs']))

    # ---- Vega
    def test_vega_sample_finds_the_drop(self):
        rep = self.client.post('/ai-agents/vega/', {'use_sample': '1'}).context['report']
        self.assertEqual(rep['n'], 90)
        self.assertIn('<svg', rep['charts'][0]['svg'])
        self.assertTrue(any(n['verdict'] == 'lost' for n in rep['notes']))

    def test_vega_csv_validation(self):
        self.assertContains(self.client.post('/ai-agents/vega/', {'csv': 'foo,bar\n1,2'}), 'at least 14 days')
        rows = 'date,sessions\n' + '\n'.join('2026-01-%02d,%d' % (d, 100 + d) for d in range(1, 21))
        self.assertEqual(self.client.post('/ai-agents/vega/', {'csv': rows}).context['report']['n'], 20)

    # ---- Prism
    def test_prism_contrast_and_palette(self):
        from home.agent_demos.prism import contrast
        self.assertAlmostEqual(contrast('#000000', '#ffffff'), 21.0, places=1)
        self.assertAlmostEqual(contrast('#777777', '#ffffff'), 4.48, places=1)
        r = self.client.get('/ai-agents/prism/', {'run': 1, 'brand': 'Green Leaf Cafe', 'industry': 'food', 'values': 'freshness, care, community'})
        self.assertEqual(len(r.context['palette']), 5)
        self.assertContains(r, '>GL<')

    def test_prism_escapes_brand_name(self):
        self.assertNotContains(self.client.get('/ai-agents/prism/', {'run': 1, 'brand': '<b>x</b> <i>y</i>'}), '<b>x</b>')

    # ---- Echo
    def test_echo_scores_samples(self):
        tags = {s: self.client.post('/ai-agents/echo/', {'sample': s}).context['tag'] for s in ('hot', 'warm', 'cold')}
        self.assertEqual(tags, {'hot': 'Hot', 'warm': 'Warm', 'cold': 'Cold'})
        f = self.client.post('/ai-agents/echo/', {'sample': 'hot'}).context['f']
        self.assertEqual((f['budget'], f['name']), (25000, 'Priya Sharma'))
        self.assertIn('SEO', f['services'])

    def test_echo_needs_real_text(self):
        self.assertContains(self.client.post('/ai-agents/echo/', {'text': 'hi'}), 'Paste a real enquiry')

    # ---- Forge
    def test_forge_finds_known_problems(self):
        r = self.client.post('/ai-agents/forge/', {'use_sample': '1'})
        found = {c['name'] for c in r.context['a11y']}
        for n in ('Image missing alt text', 'Form field without a label', 'Button with no name', 'Link with no text', 'Vague link text',
                  'Skipped heading level', 'Positive tabindex', 'Text contrast', 'Page language'):
            self.assertIn(n, found, n)
        self.assertLess(r.context['a11y_score'], 60)

    def test_forge_clean_html_scores_high(self):
        html = ('<!doctype html><html lang="en"><head><title>Ok</title><meta name="viewport" content="width=device-width"></head><body>'
                '<h1>Hi</h1><img src="a.png" alt="A" width="1" height="1"><label for="n">Name</label><input id="n">'
                '<a href="/x">Read our pricing</a></body></html>')
        self.assertEqual(self.client.post('/ai-agents/forge/', {'html': html}).context['a11y_score'], 100)
