import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from admin_app.models import GetTouchWithUs
from home.models import BlogPost, LocationFAQ, LocationPage, Page, Service

from . import bulk
from .models import SiteSettings
from .registry import KINDS

User = get_user_model()
PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 40


PLAIN_STATIC = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=PLAIN_STATIC)
class StudioBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('editor', 'e@x.com', 'pw-Test-123', is_staff=True)
        cls.normal = User.objects.create_user('visitor', 'v@x.com', 'pw-Test-123')
        cls.svc = Service.objects.create(name='SEO Services', description='Search engine optimisation')
        cls.svc2 = Service.objects.create(name='Web Design', description='Websites')
        Page.objects.create(post_type='Page', page_name='Home', page_meta_title='Home', page_meta_keyword='k', page_meta_description='d', page_tag='home', page_content='<p>x</p>')

    def setUp(self):
        cache.clear()
        self.client.force_login(self.staff)


class AccessTests(StudioBase):
    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        for name, args in [('studio:dashboard', []), ('studio:list', ['pages']), ('studio:bulk_pages', []), ('studio:media', []), ('studio:settings', [])]:
            r = self.client.get(reverse(name, args=args))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn('/studio/login/', r['Location'])

    def test_non_staff_cannot_enter(self):
        self.client.force_login(self.normal)
        self.assertEqual(self.client.get(reverse('studio:dashboard')).status_code, 302)
        self.assertEqual(self.client.get(reverse('studio:api_search') + '?q=abc').status_code, 403)

    def test_post_endpoints_require_staff(self):
        self.client.logout()
        r = self.client.post(reverse('studio:bulk', args=['pages']), {'action': 'delete', 'ids': [1]})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Page.objects.filter(page_tag='home').exists())

    def test_login_flow_and_open_redirect_blocked(self):
        self.client.logout()
        r = self.client.post(reverse('studio:login') + '?next=https://evil.example/', {'username': 'editor', 'password': 'pw-Test-123', 'next': 'https://evil.example/'})
        self.assertRedirects(r, reverse('studio:dashboard'), fetch_redirect_response=False)

    def test_non_staff_login_refused(self):
        self.client.logout()
        r = self.client.post(reverse('studio:login'), {'username': 'visitor', 'password': 'pw-Test-123'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'does not have access')

    def test_login_throttle(self):
        self.client.logout()
        for _ in range(8):
            self.client.post(reverse('studio:login'), {'username': 'editor', 'password': 'wrong'})
        r = self.client.post(reverse('studio:login'), {'username': 'editor', 'password': 'pw-Test-123'})
        self.assertContains(r, 'Too many attempts')

    def test_responses_are_noindex(self):
        r = self.client.get(reverse('studio:dashboard'))
        self.assertIn('noindex', r['X-Robots-Tag'])

    def test_all_screens_render(self):
        GetTouchWithUs.objects.create(full_name='Ann', email='a@b.com', phone_number='1')
        for kind in KINDS:
            self.assertEqual(self.client.get(reverse('studio:list', args=[kind])).status_code, 200, kind)
            if not KINDS[kind].get('readonly'):
                self.assertEqual(self.client.get(reverse('studio:new', args=[kind])).status_code, 200, kind)
        for name in ('studio:dashboard', 'studio:bulk_pages', 'studio:bulk_locations', 'studio:media', 'studio:settings'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        lead = GetTouchWithUs.objects.first()
        self.assertEqual(self.client.get(reverse('studio:edit', args=['leads', lead.pk])).status_code, 200)

    def test_edit_screens_render_for_existing_items_without_images(self):
        # regression: editing an existing item that has no uploaded image must not crash
        from home.models import CaseStudy, SubService, Testimonial
        objs = {
            'blog': BlogPost.objects.create(title='T', slug='t', excerpt='e', content='c'),
            'cases': CaseStudy.objects.create(client_name='Acme', slug='acme', summary='s', challenge='c', solution='s', results='r'),
            'locations': LocationPage.objects.create(service=self.svc, city='Pune', slug='pune', headline='h', introduction='i', content='c', meta_title='m', meta_description='d'),
            'testimonials': Testimonial.objects.create(client_name='Bob', quote='q'),
            'pages': Page.objects.get(page_tag='home'),
            'services': self.svc,
            'subservices': SubService.objects.create(service=self.svc, name='Sub'),
        }
        for kind, obj in objs.items():
            r = self.client.get(reverse('studio:edit', args=[kind, obj.pk]))
            self.assertEqual(r.status_code, 200, kind)

    def test_public_site_still_works_and_studio_not_caught_by_catchall(self):
        self.client.logout()
        self.assertEqual(self.client.get('/').status_code, 200)
        r = self.client.get('/studio/')
        self.assertEqual(r.status_code, 302)  # login redirect, not a 404 from the page catch-all


class ContentCrudTests(StudioBase):
    def test_blog_create_edit_publish_delete(self):
        r = self.client.post(reverse('studio:new', args=['blog']), {
            'title': 'My First Post', 'slug': '', 'excerpt': 'Short', 'content': '<p>Hello</p>', 'author': 'Me', 'meta_title': '', 'meta_description': '',
        })
        self.assertEqual(r.status_code, 302)
        post = BlogPost.objects.get(title='My First Post')
        self.assertEqual(post.slug, 'my-first-post')
        self.assertFalse(post.is_published)
        self.client.post(reverse('studio:bulk', args=['blog']), {'action': 'publish', 'ids': [post.pk]})
        post.refresh_from_db()
        self.assertTrue(post.is_published)
        self.assertIsNotNone(post.published_at)
        self.client.post(reverse('studio:delete', args=['blog', post.pk]))
        self.assertFalse(BlogPost.objects.filter(pk=post.pk).exists())

    def test_blog_slug_uniqueness_generated(self):
        BlogPost.objects.create(title='Dup', slug='dup', excerpt='e', content='c')
        self.client.post(reverse('studio:new', args=['blog']), {'title': 'Dup', 'slug': '', 'excerpt': 'e', 'content': 'c', 'author': 'a'})
        self.assertTrue(BlogPost.objects.filter(slug='dup-2').exists())

    def test_page_rules(self):
        base = {'post_type': 'Custom_Page', 'page_name': 'Test', 'page_meta_title': 'Test title', 'page_meta_description': 'desc', 'page_content': '<p>ok</p>'}
        r = self.client.post(reverse('studio:new', args=['pages']), dict(base, page_tag='admin'))
        self.assertContains(r, 'reserved')
        r = self.client.post(reverse('studio:new', args=['pages']), dict(base, page_tag='Bad Slug!'))
        self.assertContains(r, 'lowercase')
        r = self.client.post(reverse('studio:new', args=['pages']), dict(base, page_tag='ok-page', page_content='{% load static %}<p>x</p>'))
        self.assertContains(r, 'Template tags')
        r = self.client.post(reverse('studio:new', args=['pages']), dict(base, page_tag='ok-page'))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Page.objects.filter(page_tag='ok-page').exists())

    def test_home_page_cannot_be_deleted(self):
        home = Page.objects.get(page_tag='home')
        self.client.post(reverse('studio:delete', args=['pages', home.pk]))
        self.assertTrue(Page.objects.filter(pk=home.pk).exists())
        self.client.post(reverse('studio:bulk', args=['pages']), {'action': 'delete', 'ids': [home.pk]})
        self.assertTrue(Page.objects.filter(pk=home.pk).exists())

    def test_service_page_protected_from_direct_delete(self):
        self.assertTrue(self.svc.page)
        self.client.post(reverse('studio:delete', args=['pages', self.svc.page.pk]))
        self.assertTrue(Service.objects.filter(pk=self.svc.pk).exists())

    def test_location_with_faqs(self):
        r = self.client.post(reverse('studio:new', args=['locations']), {
            'service': self.svc.pk, 'city': 'Pune', 'country': 'India', 'slug': '', 'headline': 'H', 'introduction': 'Intro', 'content': '<p>c</p>',
            'meta_title': 'T', 'meta_description': 'D', 'faqs-TOTAL_FORMS': '2', 'faqs-INITIAL_FORMS': '0', 'faqs-MIN_NUM_FORMS': '0', 'faqs-MAX_NUM_FORMS': '1000',
            'faqs-0-question': 'Q1?', 'faqs-0-answer': 'A1', 'faqs-1-question': 'Q2?', 'faqs-1-answer': 'A2',
        })
        self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
        loc = LocationPage.objects.get(city='Pune')
        self.assertEqual(loc.slug, 'seo-services-pune')
        self.assertEqual(loc.faqs.count(), 2)

    def test_settings_flow_to_public_site(self):
        self.client.post(reverse('studio:settings'), {'phone': '+911234567890', 'email': 'hello@example.com', 'address': '1 Main St', 'facebook': 'https://facebook.com/x'})
        self.assertEqual(SiteSettings.load().phone, '+911234567890')
        cache.clear()
        html = self.client.get('/').content.decode()
        self.assertIn('tel:+911234567890', html)
        self.assertIn('hello@example.com', html)
        self.assertIn('https://facebook.com/x', html)

    def test_search_api(self):
        BlogPost.objects.create(title='Zebra guide', slug='zebra', excerpt='e', content='c')
        d = self.client.get(reverse('studio:api_search') + '?q=zebra').json()
        self.assertEqual(d['results'][0]['title'], 'Zebra guide')

    def test_csv_export_neutralises_formulas(self):
        BlogPost.objects.create(title='=HYPERLINK("x")', slug='evil', excerpt='e', content='c')
        r = self.client.get(reverse('studio:export', args=['blog']))
        self.assertIn("'=HYPERLINK", r.content.decode())


class BulkPagesTests(StudioBase):
    CSV = ('page_name,page_tag,meta_title,meta_description,content\n'
           'Alpha Service,alpha-service,Alpha | Rizen,Alpha description,"<p>%s</p>"\n'
           'Beta Service,,,,"Plain text para one.\n\nPara two."\n') % ('word ' * 200)

    def test_parse_and_preview(self):
        rows, err = bulk.parse_table(self.CSV)
        self.assertIsNone(err)
        self.assertEqual(len(rows), 2)
        items, _ = bulk.build_page_items(rows)
        self.assertEqual([i['status'] for i in items], ['new', 'new'])
        self.assertEqual(items[1]['values']['page_tag'], 'beta-service')
        self.assertIn('<p>Plain text para one.</p>', items[1]['values']['page_content'])
        self.assertTrue(any('thin' in w.lower() for w in items[1]['warnings']))

    def test_preview_does_not_write_create_does(self):
        self.client.post(reverse('studio:bulk_pages'), {'mode': 'paste', 'table': self.CSV, 'action': 'preview', 'on_conflict': 'skip'})
        self.assertFalse(Page.objects.filter(page_tag='alpha-service').exists())
        r = self.client.post(reverse('studio:bulk_pages'), {'mode': 'paste', 'table': self.CSV, 'action': 'create', 'on_conflict': 'skip'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Page.objects.filter(page_tag='alpha-service').exists())
        self.assertTrue(Page.objects.filter(page_tag='beta-service').exists())

    def test_conflicts_skip_or_update(self):
        Page.objects.create(post_type='Page', page_name='Old', page_meta_title='o', page_meta_keyword='o', page_meta_description='o', page_tag='alpha-service', page_content='old')
        self.client.post(reverse('studio:bulk_pages'), {'mode': 'paste', 'table': self.CSV, 'action': 'create', 'on_conflict': 'skip'})
        self.assertEqual(Page.objects.get(page_tag='alpha-service').page_name, 'Old')
        self.client.post(reverse('studio:bulk_pages'), {'mode': 'paste', 'table': self.CSV, 'action': 'create', 'on_conflict': 'update'})
        self.assertEqual(Page.objects.get(page_tag='alpha-service').page_name, 'Alpha Service')

    def test_dangerous_rows_rejected(self):
        csv = 'page_name,page_tag,content\nBad,admin,<p>x</p>\nTags,tags-page,"{% load os %}"\nDup,dup,x\nDup2,dup,y\n,,z\nSpaced,Spaced Slug!,x\n'
        rows, _ = bulk.parse_table(csv)
        items, _ = bulk.build_page_items(rows)
        status = {i['values']['page_name']: i['status'] for i in items}
        self.assertEqual(status['Bad'], 'error')
        self.assertEqual(status['Tags'], 'error')
        self.assertEqual(status['Dup2'], 'error')
        self.assertEqual(status[''], 'error')
        self.assertEqual(status['Spaced'], 'error')
        res = bulk.apply_page_items(items)
        self.assertEqual(len(res['created']), 1)
        self.assertFalse(Page.objects.filter(page_tag='admin').exists())

    def test_template_mode_and_tsv(self):
        rows = bulk.generate_page_rows('Web Design\nApp Dev | app-development', '<h2>{name}</h2>', '{name} | Rizen', 'About {keyword}')
        items, _ = bulk.build_page_items(rows)
        self.assertEqual(items[1]['values']['page_tag'], 'app-development')
        self.assertEqual(items[0]['values']['page_meta_title'], 'Web Design | Rizen')
        rows, err = bulk.parse_table('page_name\tpage_tag\nOne\tone-page\n')
        self.assertIsNone(err)
        self.assertEqual(rows[0]['page_tag'], 'one-page')

    def test_html_in_template_names_is_escaped(self):
        rows = bulk.generate_page_rows('<script>alert(1)</script>', '<h2>{name}</h2>', '{name}', '{name}')
        items, _ = bulk.build_page_items(rows)
        self.assertNotIn('<script>', items[0]['values']['page_content'])

    def test_bad_input_messages(self):
        self.assertIsNotNone(bulk.parse_table('')[1])
        self.assertIsNotNone(bulk.parse_table('only,header')[1])


class BulkLocationTests(StudioBase):
    def cfg(self):
        return {k: bulk.DEFAULTS[k] for k in ('slug_pattern', 'headline', 'intro_variants', 'meta_title', 'meta_description', 'content', 'faqs')}

    def test_matrix_generation_and_notes(self):
        items, errors, ok = bulk.build_location_items([self.svc.pk, self.svc2.pk], 'Pune | India | A note here\nKolkata, India', self.cfg())
        self.assertTrue(ok)
        self.assertEqual(len(items), 4)
        slugs = {i['values']['slug'] for i in items}
        self.assertIn('seo-services-pune', slugs)
        self.assertIn('web-design-kolkata', slugs)
        note_page = next(i for i in items if i['city'] == 'Pune')
        self.assertIn('A note here', note_page['values']['content'])
        self.assertTrue(note_page['has_note'])
        self.assertFalse(next(i for i in items if i['city'] == 'Kolkata')['has_note'])
        self.assertTrue(all(len(i['values']['meta_title']) <= 60 for i in items))
        self.assertTrue(all(len(i['faqs']) == 2 for i in items))

    def test_intro_variants_rotate(self):
        items, _, _ = bulk.build_location_items([self.svc.pk], 'A\nB\nC', self.cfg())
        intros = [i['values']['introduction'] for i in items]
        self.assertEqual(len(set(intros)), 3)

    def test_create_as_drafts_then_skip_existing(self):
        url = reverse('studio:bulk_locations')
        post = {'services': [self.svc.pk], 'cities': 'Pune | India | note\nSurat | India | note', 'action': 'create', 'on_conflict': 'skip', **self.cfg()}
        self.client.post(url, post)
        self.assertEqual(LocationPage.objects.count(), 2)
        self.assertFalse(LocationPage.objects.filter(is_published=True).exists())
        self.assertEqual(LocationFAQ.objects.count(), 4)
        r = self.client.post(url, post)
        self.assertEqual(LocationPage.objects.count(), 2)
        self.assertContains(r, 'skipped')

    def test_publish_flag_and_update(self):
        url = reverse('studio:bulk_locations')
        post = {'services': [self.svc.pk], 'cities': 'Pune | India | note', 'action': 'create', 'on_conflict': 'update', 'publish': 'on', **self.cfg()}
        self.client.post(url, post)
        self.assertTrue(LocationPage.objects.get(city='Pune').is_published)
        post['headline'] = 'New headline for {city}'
        self.client.post(url, post)
        self.assertEqual(LocationPage.objects.count(), 1)
        self.assertEqual(LocationPage.objects.get(city='Pune').headline, 'New headline for Pune')
        self.assertEqual(LocationPage.objects.get(city='Pune').faqs.count(), 2)

    def test_validation_messages(self):
        _, errors, ok = bulk.build_location_items([], 'Pune', self.cfg())
        self.assertFalse(ok)
        _, errors, ok = bulk.build_location_items([self.svc.pk], '', self.cfg())
        self.assertFalse(ok)
        items, _, _ = bulk.build_location_items([self.svc.pk], 'Pune | India | n | abc | 1', self.cfg())
        self.assertEqual(items[0]['status'], 'error')
        cfg = self.cfg()
        cfg['content'] = '{% load x %}<p>y</p>'
        items, _, _ = bulk.build_location_items([self.svc.pk], 'Pune | India | n', cfg)
        self.assertEqual(items[0]['status'], 'error')

    def test_city_html_is_escaped_in_content(self):
        items, _, _ = bulk.build_location_items([self.svc.pk], '<b>Evil</b> | India | <script>x</script>', self.cfg())
        self.assertNotIn('<script>', items[0]['values']['content'])
        self.assertNotIn('<b>Evil</b>', items[0]['values']['content'])


class MediaTests(StudioBase):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.tmp)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_upload_accepts_real_png_only(self):
        good = SimpleUploadedFile('Logo Pic.png', PNG, content_type='image/png')
        svg = SimpleUploadedFile('x.svg', b'<svg onload=alert(1)>', content_type='image/svg+xml')
        fake = SimpleUploadedFile('fake.png', b'not an image at all', content_type='image/png')
        self.client.post(reverse('studio:media_upload'), {'files': [good, svg, fake]})
        r = self.client.get(reverse('studio:api_media')).json()
        self.assertEqual(len(r['items']), 1)
        self.assertTrue(r['items'][0]['name'].startswith('logo-pic-'))

    def test_delete_is_confined_to_media_root(self):
        self.client.post(reverse('studio:media_upload'), {'files': SimpleUploadedFile('a.png', PNG)})
        self.client.post(reverse('studio:media_delete'), {'path': '../../manage.py'})
        item = self.client.get(reverse('studio:api_media')).json()['items'][0]
        self.client.post(reverse('studio:media_delete'), {'path': item['path']})
        self.assertEqual(self.client.get(reverse('studio:api_media')).json()['items'], [])


class RankMathStyleSeoTests(StudioBase):
    def make_post(self, **kw):
        data = dict(title='SEO Guide', slug='seo-guide', excerpt='e', content='<p>Body about seo services.</p>', is_published=True)
        data.update(kw)
        return BlogPost.objects.create(**data)

    def test_seo_fields_saved_from_editor_and_score_clamped(self):
        r = self.client.post(reverse('studio:new', args=['blog']), {
            'title': 'Rank Post', 'slug': 'rank-post', 'excerpt': 'e', 'content': '<p>x</p>', 'author': 'a', 'focus_keyword': 'rank post',
            'seo_score': '250', 'seo_noindex': 'on', 'seo_canonical': 'https://example.com/original/', 'og_title': 'Social title', 'og_description': 'Social desc',
        })
        self.assertEqual(r.status_code, 302)
        post = BlogPost.objects.get(slug='rank-post')
        self.assertEqual(post.focus_keyword, 'rank post')
        self.assertEqual(post.seo_score, 100)
        self.assertTrue(post.seo_noindex)
        self.assertEqual(post.og_title, 'Social title')

    def test_editor_shows_seo_panel_for_every_seo_kind(self):
        from home.models import CaseStudy
        objs = {
            'blog': self.make_post(), 'pages': Page.objects.get(page_tag='home'),
            'locations': LocationPage.objects.create(service=self.svc, city='Pune', slug='pune', headline='h', introduction='i', content='c', meta_title='m', meta_description='d'),
            'cases': CaseStudy.objects.create(client_name='Acme', slug='acme', summary='s', challenge='c', solution='s', results='r'),
        }
        for kind, obj in objs.items():
            html = self.client.get(reverse('studio:edit', args=[kind, obj.pk])).content.decode()
            self.assertIn('id="st-rm"', html, kind)
            self.assertIn('name="focus_keyword"', html, kind)
            self.assertIn('data-rm-tab="social"', html, kind)
            self.assertIn('name="seo_canonical"', html, kind)
        html = self.client.get(reverse('studio:new', args=['testimonials'])).content.decode()
        self.assertNotIn('id="st-rm"', html)

    def test_keyword_cannibalisation_api(self):
        a = self.make_post(focus_keyword='seo services')
        b = self.make_post(slug='other', title='Other', focus_keyword='SEO Services')
        d = self.client.get(reverse('studio:api_keyword'), {'kw': 'seo services', 'kind': 'blog', 'pk': a.pk}).json()
        self.assertEqual([u['title'] for u in d['used_by']], ['Other'])
        d = self.client.get(reverse('studio:api_keyword'), {'kw': 'nothing here', 'kind': 'blog', 'pk': a.pk}).json()
        self.assertEqual(d['used_by'], [])

    def test_internal_link_suggestions_exclude_self_and_drafts(self):
        me = self.make_post(title='Local SEO checklist', slug='local-seo')
        self.make_post(title='Technical SEO audit', slug='tech-seo')
        self.make_post(title='Draft SEO plan', slug='draft-seo', is_published=False)
        d = self.client.get(reverse('studio:api_links'), {'q': 'seo audit', 'kind': 'blog', 'pk': me.pk}).json()
        titles = [r['title'] for r in d['results']]
        self.assertIn('Technical SEO audit', titles)
        self.assertNotIn('Local SEO checklist', titles)
        self.assertNotIn('Draft SEO plan', titles)

    def test_seo_apis_require_staff(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('studio:api_keyword'), {'kw': 'x'}).status_code, 403)
        self.assertEqual(self.client.get(reverse('studio:api_links'), {'q': 'x'}).status_code, 403)

    def test_public_page_uses_noindex_canonical_and_social_tags(self):
        post = self.make_post(seo_noindex=True, seo_canonical='https://example.com/orig/', og_title='Share me', og_description='Share desc')
        self.client.logout()
        html = self.client.get(post.get_absolute_url()).content.decode()
        self.assertIn('<meta name="robots" content="noindex,follow">', html)
        self.assertIn('<link rel="canonical" href="https://example.com/orig/">', html)
        self.assertIn('property="og:title" content="Share me"', html)
        self.assertIn('property="og:description" content="Share desc"', html)
        self.assertIn('property="og:type" content="article"', html)
        self.assertIn('name="twitter:title" content="Share me"', html)

    def test_public_defaults_unchanged_when_no_seo_settings(self):
        post = self.make_post()
        self.client.logout()
        html = self.client.get(post.get_absolute_url()).content.decode()
        self.assertIn('<meta name="robots" content="index,follow">', html)
        self.assertIn('property="og:image" content="http', html)  # absolute URL, not a relative /static path

    def test_social_image_is_absolute_url(self):
        from django.core.files.base import ContentFile
        post = self.make_post()
        post.og_image.save('share.png', ContentFile(PNG), save=True)
        self.client.logout()
        html = self.client.get(post.get_absolute_url()).content.decode()
        self.assertRegex(html, r'property="og:image" content="http://testserver/media/social/share[^"]*\.png"')
        post.og_image.delete(save=False)

    def test_noindex_items_are_removed_from_the_sitemap(self):
        self.make_post(slug='visible', title='Visible')
        self.make_post(slug='hidden-post', title='Hidden', seo_noindex=True)
        xml = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('/blog/visible/', xml)
        self.assertNotIn('/blog/hidden-post/', xml)

    def test_lists_show_saved_analyzer_score(self):
        self.make_post(seo_score=42)
        html = self.client.get(reverse('studio:list', args=['blog'])).content.decode()
        self.assertIn('st-score-bad', html)
        self.assertIn('>42<', html)

