from django.test import TestCase


class NoIndexPrivateAreasTests(TestCase):
    HEADER = 'noindex, nofollow, noarchive'

    def test_private_areas_send_noindex_header(self):
        for url in ('/studio/', '/studio/login/', '/studio/pages/', '/studio/blog/export.csv', '/studio/api/search/',
                    '/admin/', '/admin/login/'):
            r = self.client.get(url)
            self.assertEqual(r.headers.get('X-Robots-Tag'), self.HEADER, '%s (%s)' % (url, r.status_code))

    def test_public_pages_are_not_noindexed(self):
        for url in ('/', '/ai-agents/', '/contact/', '/blog/', '/robots.txt'):
            self.assertNotIn('noindex', self.client.get(url).headers.get('X-Robots-Tag', ''), url)

    def test_robots_txt_lets_crawlers_see_the_noindex(self):
        body = self.client.get('/robots.txt').content.decode()
        disallowed = [l.split(':', 1)[1].strip() for l in body.splitlines() if l.lower().startswith('disallow')]
        self.assertNotIn('/studio/', disallowed)
        self.assertNotIn('/admin/', disallowed)

    def test_studio_login_page_also_has_meta_noindex(self):
        r = self.client.get('/studio/login/')
        self.assertContains(r, '<meta name="robots" content="noindex, nofollow, noarchive">')
