import re

from django.test import TestCase, override_settings


class AuditFixTests(TestCase):
    PAGES = ('/', '/ai-agents/', '/contact/', '/privacy-policy/', '/terms-condition/', '/ai-agents/atlas/')

    def html(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, url)
        return r.content.decode()

    def test_first_heading_is_h1(self):
        for url in ('/', '/ai-agents/', '/contact/', '/about/'):
            m = re.search(r'<h([1-6])\b', self.html(url))
            self.assertEqual(m.group(1), '1', '%s starts with h%s' % (url, m.group(1)))

    def test_no_plain_text_email_in_source(self):
        for url in self.PAGES:
            self.assertNotRegex(self.html(url), r'[\w.+-]+@rizendigital\.com', url)

    def test_email_is_rebuilt_by_script(self):
        h = self.html('/contact/')
        self.assertIn('class="js-mail"', h)
        self.assertIn('admin [at] rizendigital.com', h)
        self.assertIn('a.js-mail', h)

    def test_no_inline_style_attributes_on_home_and_agents(self):
        for url in ('/', '/ai-agents/'):
            inline = re.findall(r'<[^>]+\sstyle="[^"]*"', self.html(url))
            self.assertEqual(inline, [], url)

    def test_agent_avatars_have_alt_text(self):
        for url in ('/', '/ai-agents/'):
            imgs = re.findall(r'<img[^>]+agents/[a-z]+[^>]*>', self.html(url))
            self.assertTrue(imgs)
            self.assertTrue(all(re.search(r'alt="[^"]+"', i) for i in imgs), url)

    def test_stylesheets_are_bundled(self):
        h = re.sub(r'<noscript>.*?</noscript>', '', self.html('/'), flags=re.S)
        blocking = re.findall(r'<link rel="stylesheet" href="([^"]+)"', h)
        self.assertLessEqual(len(blocking), 4, blocking)
        self.assertTrue(any('site.bundle.min.css' in b for b in blocking))

    def test_analytics_only_when_configured(self):
        self.assertNotIn('googletagmanager.com/gtag/js', self.html('/'))  # the GA4 snippet (GTM is separate)
        with override_settings(SITE_GA_ID='G-TEST12345'):
            h = self.html('/')
        self.assertIn('googletagmanager.com/gtag/js?id=G-TEST12345', h)

    def test_home_meta_migration_keeps_edited_text(self):
        import importlib
        from django.apps import apps
        from home.models import Page
        mig = importlib.import_module('home.migrations.0007_home_meta_description_keyword')
        Page.objects.filter(page_tag='home').delete()
        Page.objects.create(post_type='Page', page_name='Home', page_tag='home', page_meta_description='My own text')
        mig.forwards(apps, None)
        self.assertEqual(Page.objects.get(page_tag='home').page_meta_description, 'My own text')
        Page.objects.filter(page_tag='home').update(page_meta_description=mig.OLD)
        mig.forwards(apps, None)
        self.assertEqual(Page.objects.get(page_tag='home').page_meta_description, mig.NEW)
