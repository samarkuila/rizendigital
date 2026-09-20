from django.test import TestCase

# Create your tests here.


class ScoutDemoTests(TestCase):
    def test_form_page_loads(self):
        r = self.client.get('/ai-agents/scout/')
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Ranked opportunity list')

    def test_report_ranks_and_localises(self):
        r = self.client.get('/ai-agents/scout/', {'run': 1, 'service': 'digital-marketing', 'city': 'Kolkata', 'goal': 'leads'})
        self.assertContains(r, 'Digital Marketing Agency in Kolkata')
        self.assertEqual(r.context['rows'][0]['rank'], 1)

    def test_unmeasured_city_has_no_invented_volume(self):
        r = self.client.get('/ai-agents/scout/', {'service': 'seo', 'city': 'Pune', 'goal': 'leads'})
        pune = [x for x in r.context['rows'] if 'Pune' in x['keyword']]
        self.assertTrue(pune)
        self.assertTrue(all(x['volume'] is None for x in pune))

    def test_bad_input_and_html_are_safe(self):
        r = self.client.get('/ai-agents/scout/', {'service': 'x', 'goal': 'y', 'city': '<script>alert(1)</script>'})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, '<script>alert')

    def test_csv_export(self):
        r = self.client.get('/ai-agents/scout/', {'service': 'seo', 'city': '', 'goal': 'awareness', 'format': 'csv'})
        self.assertEqual(r['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('Rank,Keyword', r.content.decode())


class ScoutLlmTests(TestCase):
    ROWS = [{'keyword': 'SEO Agency', 'intent': 'Commercial', 'volume': 4400, 'difficulty': 67, 'effort': 'Long game', 'priority': 90}]

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_no_key_means_no_ai_and_no_error(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            r = self.client.get('/ai-agents/scout/', {'service': 'seo', 'city': '', 'goal': 'leads'})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Scout&rsquo;s read')

    def test_ai_brief_is_shown(self):
        from unittest import mock
        fake = {'summary': 'Focus on local intent first.', 'briefs': {'SEO Agency Near Me': {'title': 'T', 'meta_description': 'M', 'outline': ['One', 'Two']}}}
        with mock.patch('home.views.scout_llm.generate', return_value=fake):
            r = self.client.get('/ai-agents/scout/', {'service': 'seo', 'city': '', 'goal': 'leads'})
        self.assertContains(r, 'Focus on local intent first.')
        self.assertContains(r, 'Page brief')

    def test_api_failure_falls_back(self):
        import os
        from unittest import mock
        from home import scout_llm
        meta = {'service': 'seo', 'service_label': 'SEO', 'city': '', 'goal': 'leads'}
        with mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'x'}), mock.patch('anthropic.Anthropic', side_effect=RuntimeError('boom')):
            self.assertIsNone(scout_llm.generate(self.ROWS, meta, '1.2.3.4'))

    def test_rate_limit(self):
        import os
        from unittest import mock
        from home import scout_llm
        with mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'x', 'SCOUT_LLM_HOURLY_LIMIT': '1'}), mock.patch('anthropic.Anthropic', side_effect=RuntimeError('boom')) as m:
            for city in ('a', 'b', 'c'):
                scout_llm.generate(self.ROWS, {'service': 'seo', 'service_label': 'SEO', 'city': city, 'goal': 'leads'}, '9.9.9.9')
        self.assertEqual(m.call_count, 1)
