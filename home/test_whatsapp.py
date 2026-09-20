import re

from django.test import TestCase, override_settings


class WhatsAppOnlyTests(TestCase):
    PAGES = ('/', '/contact/', '/about/', '/ai-agents/', '/blog/')

    def html(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, url)
        return r.content.decode()

    @override_settings(SITE_PHONE='+919733585522', SITE_WHATSAPP='')
    def test_no_call_links_or_visible_number(self):
        for url in self.PAGES:
            h = self.html(url)
            self.assertNotIn('tel:', h, url)
            visible = re.sub(r'<script[^>]*>.*?</script>', '', h, flags=re.S)
            visible = re.sub(r'https://wa\.me/\d+', '', visible)  # the chat link itself carries the number
            self.assertNotIn('9733585522', visible, url)
            self.assertNotIn('flaticon-call', h, url)

    @override_settings(SITE_PHONE='+919733585522', SITE_WHATSAPP='')
    def test_single_whatsapp_button_using_site_phone(self):
        h = self.html('/')
        self.assertEqual(h.count('class="wa-float"'), 1)
        m = re.search(r'class="wa-float"', h)
        self.assertTrue(m)
        self.assertRegex(h, r'href="https://wa\.me/919733585522\?text=Hi%20Rizen%20Digital')

    @override_settings(SITE_PHONE='+919733585522', SITE_WHATSAPP='+91 98765-43210')
    def test_dedicated_whatsapp_number_wins_and_is_cleaned(self):
        self.assertIn('https://wa.me/919876543210?text=', self.html('/contact/'))

    @override_settings(SITE_PHONE='', SITE_WHATSAPP='')
    def test_no_number_means_no_button(self):
        h = self.html('/')
        self.assertNotIn('wa-float', h)
        self.assertNotIn('wa.me', h)

    @override_settings(SITE_PHONE='+919733585522')
    def test_whatsapp_link_opens_safely_in_new_tab(self):
        for a in re.findall(r'<a [^>]*wa\.me[^>]*>', self.html('/')):
            self.assertIn('rel="noopener"', a)
            self.assertIn('target="_blank"', a)
