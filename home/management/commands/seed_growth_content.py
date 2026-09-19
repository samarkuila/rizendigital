from django.core.management.base import BaseCommand
from django.utils import timezone

from home.models import BlogPost, LocationPage, Service


class Command(BaseCommand):
    help = 'Seed the initial SEO editorial and local landing page content.'

    def handle(self, *args, **options):
        service, _ = Service.objects.get_or_create(
            name='Digital Marketing',
            defaults={
                'description': 'Digital marketing strategy built around search visibility, useful content, and measurable growth.',
            },
        )

        BlogPost.objects.update_or_create(
            slug='seo-content-strategy-for-growing-businesses',
            defaults={
                'title': 'A practical SEO content strategy for growing businesses',
                'excerpt': 'A simple framework for choosing topics, building useful pages, and turning organic visibility into qualified enquiries.',
                'content': '''<h2>Start with the questions your customers already ask</h2>
<p>Strong SEO content begins with customer intent, not a list of disconnected keywords. Group the questions your audience asks into discovery, comparison, and decision stages.</p>
<h2>Build one useful page before publishing ten average ones</h2>
<p>Create a focused service or location page that answers the complete question, shows your process, and gives the reader a clear next step. Supporting articles should strengthen that page through thoughtful internal links.</p>
<h2>Measure progress beyond rankings</h2>
<p>Track qualified organic visits, engaged sessions, enquiry rate, and assisted conversions alongside rankings. Those signals show whether visibility is helping the business, not just producing impressions.</p>''',
                'meta_title': 'SEO Content Strategy for Growing Businesses',
                'meta_description': 'Learn how to build an SEO content strategy around customer intent, useful pages, internal links, and qualified enquiries.',
                'author': 'Rizen Digital',
                'published_at': timezone.now(),
                'is_published': True,
            },
        )

        locations = [
            {
                'city': 'Kolkata',
                'slug': 'seo-agency-kolkata',
                'headline': 'SEO strategy for businesses growing in Kolkata',
                'introduction': 'Build stronger local visibility and a clearer path from search to enquiry with a strategy shaped around Kolkata customers.',
                'content': '''<h2>Make your local demand easier to find</h2>
<p>We help Kolkata businesses improve the technical foundations, service pages, local signals, and conversion paths that support sustainable search growth.</p>
<h2>What we focus on</h2>
<ul><li>Technical and on-page SEO priorities</li><li>Service pages aligned to commercial intent</li><li>Google Business Profile and local visibility</li><li>Reporting connected to qualified enquiries</li></ul>''',
                'meta_title': 'SEO Agency in Kolkata | Rizen Digital',
                'meta_description': 'Rizen Digital helps Kolkata businesses improve local visibility, qualified traffic, and enquiry generation through practical SEO.',
            },
            {
                'city': 'Haldia',
                'slug': 'seo-agency-haldia',
                'headline': 'A practical SEO partner for Haldia businesses',
                'introduction': 'Reach the customers searching for your expertise in Haldia with focused local SEO, useful content, and measurable reporting.',
                'content': '''<h2>Turn regional demand into measurable growth</h2>
<p>From industrial services to local professional firms, we build search journeys that explain your value clearly and make it easier for the right customer to take action.</p>
<h2>Our local growth work</h2>
<ul><li>Search intent and competitor research</li><li>Location and service page planning</li><li>Technical cleanup and content optimisation</li><li>Conversion tracking and monthly priorities</li></ul>''',
                'meta_title': 'SEO Agency in Haldia | Rizen Digital',
                'meta_description': 'Grow your Haldia business with practical local SEO, service content, and conversion-focused digital marketing from Rizen Digital.',
            },
            {
                'city': 'Kolaghat',
                'slug': 'seo-agency-kolaghat',
                'headline': 'Help more customers discover your Kolaghat business',
                'introduction': 'A focused SEO plan can help Kolaghat businesses earn better visibility, explain their offer, and generate more qualified enquiries.',
                'content': '''<h2>Build visibility around real customer needs</h2>
<p>We combine local search fundamentals with clear service messaging so your website becomes a useful destination for people ready to compare and contact providers.</p>
<h2>Where we create momentum</h2>
<ul><li>Local keyword and intent mapping</li><li>Clear, conversion-ready service pages</li><li>Content that answers buying questions</li><li>Simple reporting on leads and opportunities</li></ul>''',
                'meta_title': 'SEO Agency in Kolaghat | Rizen Digital',
                'meta_description': 'Rizen Digital helps Kolaghat businesses earn local search visibility and turn qualified website visits into enquiries.',
            },
        ]

        for location in locations:
            LocationPage.objects.update_or_create(
                slug=location['slug'],
                defaults={
                    **location,
                    'service': service,
                    'is_published': True,
                },
            )

        self.stdout.write(self.style.SUCCESS('Seeded 1 blog post and 3 published location pages.'))
