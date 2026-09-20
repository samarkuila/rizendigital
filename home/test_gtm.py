import re

from django.test import TestCase, override_settings

ID = 'GTM-WL9WHQXF'


class TagManagerTests(TestCase):
    def html(self, url='/'):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, url)
        return r.content.decode()

    def test_head_snippet_is_first_thing_in_head(self):
        h = self.html()
        head = h[h.index('<head>'):h.index('</head>')]
        self.assertIn("'dataLayer','%s'" % ID, head)
        self.assertLess(head.index('Google Tag Manager'), head.index('<meta charset'))
        self.assertEqual(h.count("'dataLayer','%s'" % ID), 1)

    def test_noscript_iframe_is_right_after_body_tag(self):
        h = self.html()
        body_open = re.search(r'<body[^>]*>', h)
        after = h[body_open.end():].lstrip()
        self.assertTrue(after.startswith('<!-- Google Tag Manager (noscript) -->'), after[:80])
        self.assertIn('https://www.googletagmanager.com/ns.html?id=%s' % ID, after[:400])

    def test_no_inline_style_added_by_the_snippet(self):
        self.assertNotIn('style="display:none;visibility:hidden"', self.html())

    def test_on_every_public_page_type(self):
        for url in ('/ai-agents/', '/ai-agents/atlas/', '/contact/', '/blog/', '/about/'):
            self.assertIn(ID, self.html(url), url)

    def test_not_on_private_studio_or_admin_pages(self):
        for url in ('/studio/login/', '/admin/login/'):
            self.assertNotIn('googletagmanager', self.html(url), url)

    @override_settings(SITE_GTM_ID='')
    def test_can_be_switched_off(self):
        self.assertNotIn('googletagmanager.com/gtm.js', self.html())
        self.assertNotIn('ns.html?id=', self.html())

    def test_invalid_container_id_is_rejected_by_settings(self):
        import importlib
        import os
        from unittest import mock
        import rizendigital.settings as s
        with mock.patch.dict(os.environ, {'GTM_CONTAINER_ID': "x');alert(1);//"}):
            importlib.reload(s)
            self.assertEqual(s.SITE_GTM_ID, '')
        importlib.reload(s)
        self.assertEqual(s.SITE_GTM_ID, ID)
