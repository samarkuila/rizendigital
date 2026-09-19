from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import BlogPost, CaseStudy, LocationPage, Page


class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        return ('home', 'about', 'contact', 'blog', 'case_studies', 'google_updates', 'ai_agents')

    def location(self, item):
        return reverse(item)


class PageSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return (
            Page.objects.exclude(post_type='Blog')
            .exclude(page_tag='')
            .exclude(page_tag='home')
            .exclude(seo_noindex=True)
            .order_by('pk')
        )

    def location(self, page):
        if '/' in page.page_tag:
            service_slug, subservice_slug = page.page_tag.split('/', 1)
            return reverse('subservice_detail', kwargs={
                'service_slug': service_slug,
                'subservice_slug': subservice_slug,
            })
        return reverse('page_detail', kwargs={'page_tag': page.page_tag})

    def lastmod(self, page):
        return page.post_date_time


class BlogSitemap(Sitemap):
    priority = 0.6
    changefreq = 'weekly'

    def items(self):
        return BlogPost.objects.filter(is_published=True, seo_noindex=False)

    def lastmod(self, post):
        return post.updated_at


class CaseStudySitemap(Sitemap):
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        return CaseStudy.objects.filter(is_published=True, seo_noindex=False)

    def lastmod(self, study):
        return study.updated_at


class LocationSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return LocationPage.objects.filter(is_published=True, seo_noindex=False)

    def lastmod(self, page):
        return page.updated_at