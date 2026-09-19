from django.core.management.base import BaseCommand

from home.models import LocationFAQ, LocationPage, Service

LOCATIONS = [
    {
        'city': 'Howrah', 'country': 'India',
        'slug': 'seo-agency-howrah',
        'headline': 'SEO strategy for businesses growing in Howrah',
        'introduction': 'Rizen Digital helps Howrah businesses improve local search visibility with practical, measurable SEO work.',
        'content': '''<h2>Local search growth for Howrah businesses</h2>
<p>We help Howrah businesses strengthen technical SEO, on-page content, and local search signals so the right customers can find them online.</p>
<h2>What we focus on</h2>
<ul><li>Technical and on-page SEO priorities</li><li>Google Business Profile and local visibility</li><li>Service pages aligned to commercial intent</li><li>Monthly reporting tied to qualified enquiries</li></ul>''',
        'meta_title': 'SEO Agency in Howrah | Rizen Digital',
        'meta_description': 'Rizen Digital helps Howrah businesses improve local search visibility, qualified traffic, and enquiry generation through practical SEO.',
        'faqs': [
            ('How much does SEO cost in Howrah?', 'SEO pricing in Howrah depends on your industry, target keywords, and scope of work. Rizen Digital offers budget-friendly packages tailored to small and mid-sized businesses; contact us for a free quote.'),
            ('Does Rizen Digital work with businesses outside Kolkata?', 'Yes. While based in Kolkata, Rizen Digital works with clients across West Bengal, including Howrah, and pan-India.'),
        ],
    },
    {
        'city': 'Durgapur', 'country': 'India',
        'slug': 'seo-agency-durgapur',
        'headline': 'A practical SEO partner for Durgapur businesses',
        'introduction': 'Reach customers actively searching for your services in Durgapur with focused local SEO and measurable reporting.',
        'content': '''<h2>Turn regional demand into measurable growth</h2>
<p>From industrial and manufacturing businesses to local professional firms, we build search strategies that explain your value clearly and make it easier for the right customer to take action.</p>
<h2>Our local growth work</h2>
<ul><li>Search intent and competitor research</li><li>Location and service page planning</li><li>Technical cleanup and content optimisation</li><li>Conversion tracking and monthly priorities</li></ul>''',
        'meta_title': 'SEO Agency in Durgapur | Rizen Digital',
        'meta_description': 'Grow your Durgapur business with practical local SEO, service content, and conversion-focused digital marketing from Rizen Digital.',
        'faqs': [
            ('What industries does Rizen Digital support in Durgapur?', 'We work with a range of local businesses in Durgapur, from industrial and B2B service providers to retail and professional firms, tailoring SEO strategy to each industry.'),
        ],
    },
    {
        'city': 'Siliguri', 'country': 'India',
        'slug': 'seo-agency-siliguri',
        'headline': 'Help more customers discover your Siliguri business',
        'introduction': 'A focused SEO plan can help Siliguri businesses earn better visibility and generate more qualified enquiries.',
        'content': '''<h2>Build visibility around real customer needs</h2>
<p>We combine local search fundamentals with clear service messaging so your website becomes a useful destination for people ready to compare and contact providers in Siliguri.</p>
<h2>Where we create momentum</h2>
<ul><li>Local keyword and intent mapping</li><li>Clear, conversion-ready service pages</li><li>Content that answers buying questions</li><li>Simple reporting on leads and opportunities</li></ul>''',
        'meta_title': 'SEO Agency in Siliguri | Rizen Digital',
        'meta_description': 'Rizen Digital helps Siliguri businesses earn local search visibility and turn qualified website visits into enquiries.',
        'faqs': [
            ('Can Rizen Digital manage SEO remotely for a Siliguri business?', 'Yes. Our SEO and reporting process is fully remote-friendly, with regular calls and transparent monthly reports regardless of your location in North Bengal.'),
        ],
    },
    {
        'city': 'Mumbai', 'country': 'India',
        'slug': 'digital-marketing-agency-mumbai',
        'headline': 'Digital marketing strategy for Mumbai businesses',
        'introduction': 'Rizen Digital supports Mumbai businesses with SEO, social media, and web development built around measurable growth.',
        'content': '''<h2>Compete for visibility in a crowded market</h2>
<p>Mumbai's business landscape is highly competitive online. We help businesses cut through with focused technical SEO, useful content, and conversion-ready websites.</p>
<h2>What we focus on</h2>
<ul><li>Competitive keyword and market research</li><li>Technical SEO and Core Web Vitals improvements</li><li>Content built around genuine customer questions</li><li>Reporting tied to enquiries, not just rankings</li></ul>''',
        'meta_title': 'Digital Marketing Agency in Mumbai | Rizen Digital',
        'meta_description': 'Rizen Digital helps Mumbai businesses grow through SEO, digital marketing, and conversion-focused web development.',
        'faqs': [
            ('Does Rizen Digital have an office in Mumbai?', 'Rizen Digital is headquartered in Kolkata and serves Mumbai businesses remotely, with the same reporting and communication standards as our local clients.'),
        ],
    },
    {
        'city': 'Delhi', 'country': 'India',
        'slug': 'digital-marketing-agency-delhi',
        'headline': 'Digital marketing strategy for Delhi businesses',
        'introduction': 'Rizen Digital helps Delhi businesses build search visibility and turn organic traffic into qualified leads.',
        'content': '''<h2>A focused approach to a competitive market</h2>
<p>We help Delhi businesses prioritise the SEO and digital marketing work that actually moves the needle, rather than spreading effort across a long generic checklist.</p>
<h2>What we focus on</h2>
<ul><li>Technical SEO audits and fixes</li><li>Service and location page strategy</li><li>Social media optimisation aligned to your brand</li><li>Transparent monthly reporting</li></ul>''',
        'meta_title': 'Digital Marketing Agency in Delhi | Rizen Digital',
        'meta_description': 'Rizen Digital helps Delhi businesses grow through SEO, digital marketing, and conversion-focused web development.',
        'faqs': [
            ('How does Rizen Digital support clients in Delhi remotely?', 'We manage SEO, content, and reporting entirely online, with scheduled calls and a shared reporting dashboard, so distance from our Kolkata office does not affect service quality.'),
        ],
    },
    {
        'city': 'Bengaluru', 'country': 'India',
        'slug': 'digital-marketing-agency-bengaluru',
        'headline': 'Digital marketing strategy for Bengaluru businesses',
        'introduction': 'Rizen Digital helps Bengaluru businesses grow through technical SEO, content, and conversion-focused websites.',
        'content': '''<h2>Search strategy built for a tech-savvy market</h2>
<p>Bengaluru's audience is often research-driven and comparison-heavy. We build content and technical SEO foundations that hold up to scrutiny and convert considered buyers.</p>
<h2>What we focus on</h2>
<ul><li>Technical SEO and site performance</li><li>Content built around buyer research questions</li><li>Service pages aligned to commercial intent</li><li>Reporting connected to real business outcomes</li></ul>''',
        'meta_title': 'Digital Marketing Agency in Bengaluru | Rizen Digital',
        'meta_description': 'Rizen Digital helps Bengaluru businesses grow through SEO, digital marketing, and conversion-focused web development.',
        'faqs': [
            ('Does Rizen Digital work with startups in Bengaluru?', 'Yes, we work with startups and growing businesses in Bengaluru, tailoring scope and budget to early-stage growth needs.'),
        ],
    },
    {
        'city': 'New York', 'country': 'United States',
        'slug': 'digital-marketing-agency-new-york',
        'headline': 'Digital marketing strategy for New York businesses',
        'introduction': 'Rizen Digital supports New York businesses with SEO, social media, and web development focused on measurable growth.',
        'content': '''<h2>Global expertise, remote-first delivery</h2>
<p>Rizen Digital works with businesses in New York on the same technical SEO, content, and conversion-focused approach we use with clients across India, adapted to the US market and competitive landscape.</p>
<h2>What we focus on</h2>
<ul><li>Technical SEO audits and fixes</li><li>Content built around US buyer search intent</li><li>Conversion-focused website work</li><li>Transparent monthly reporting across time zones</li></ul>
<p><em>Note: Rizen Digital is headquartered in Kolkata, India, and serves New York clients remotely.</em></p>''',
        'meta_title': 'Digital Marketing Agency in New York | Rizen Digital',
        'meta_description': 'Rizen Digital helps New York businesses grow through SEO, digital marketing, and conversion-focused web development, delivered remotely.',
        'faqs': [
            ('Does Rizen Digital have a physical office in New York?', 'No. Rizen Digital is based in Kolkata, India, and serves New York clients remotely through video calls, shared reporting, and asynchronous communication.'),
            ('How are time zone differences handled for US clients?', 'We schedule regular calls at times that work for US business hours and maintain written reporting so progress is clear regardless of time zone overlap.'),
        ],
    },
    {
        'city': 'Los Angeles', 'country': 'United States',
        'slug': 'digital-marketing-agency-los-angeles',
        'headline': 'Digital marketing strategy for Los Angeles businesses',
        'introduction': 'Rizen Digital supports Los Angeles businesses with SEO, social media, and web development focused on measurable growth.',
        'content': '''<h2>Global expertise, remote-first delivery</h2>
<p>We bring the same technical SEO and conversion-focused approach we use with clients across India to businesses in Los Angeles, adapted to the local market and competitive landscape.</p>
<h2>What we focus on</h2>
<ul><li>Technical SEO audits and fixes</li><li>Content built around US buyer search intent</li><li>Social media optimisation</li><li>Transparent monthly reporting</li></ul>
<p><em>Note: Rizen Digital is headquartered in Kolkata, India, and serves Los Angeles clients remotely.</em></p>''',
        'meta_title': 'Digital Marketing Agency in Los Angeles | Rizen Digital',
        'meta_description': 'Rizen Digital helps Los Angeles businesses grow through SEO, digital marketing, and conversion-focused web development, delivered remotely.',
        'faqs': [
            ('Does Rizen Digital have a physical office in Los Angeles?', 'No. Rizen Digital is based in Kolkata, India, and serves Los Angeles clients remotely through video calls, shared reporting, and asynchronous communication.'),
        ],
    },
    {
        'city': 'London', 'country': 'United Kingdom',
        'slug': 'digital-marketing-agency-london',
        'headline': 'Digital marketing strategy for London businesses',
        'introduction': 'Rizen Digital supports London businesses with SEO, social media, and web development focused on measurable growth.',
        'content': '''<h2>Global expertise, remote-first delivery</h2>
<p>We apply the same technical SEO, content, and conversion-focused approach we use with clients across India to businesses in London, adapted to the UK market.</p>
<h2>What we focus on</h2>
<ul><li>Technical SEO audits and fixes</li><li>Content built around UK buyer search intent</li><li>Conversion-focused website work</li><li>Transparent monthly reporting</li></ul>
<p><em>Note: Rizen Digital is headquartered in Kolkata, India, and serves London clients remotely.</em></p>''',
        'meta_title': 'Digital Marketing Agency in London | Rizen Digital',
        'meta_description': 'Rizen Digital helps London businesses grow through SEO, digital marketing, and conversion-focused web development, delivered remotely.',
        'faqs': [
            ('Does Rizen Digital have a physical office in London?', 'No. Rizen Digital is based in Kolkata, India, and serves London clients remotely through video calls, shared reporting, and asynchronous communication.'),
        ],
    },
    {
        'city': 'Toronto', 'country': 'Canada',
        'slug': 'digital-marketing-agency-toronto',
        'headline': 'Digital marketing strategy for Toronto businesses',
        'introduction': 'Rizen Digital supports Toronto businesses with SEO, social media, and web development focused on measurable growth.',
        'content': '''<h2>Global expertise, remote-first delivery</h2>
<p>We bring the same technical SEO and conversion-focused approach we use with clients across India to businesses in Toronto, adapted to the Canadian market.</p>
<h2>What we focus on</h2>
<ul><li>Technical SEO audits and fixes</li><li>Content built around Canadian buyer search intent</li><li>Social media optimisation</li><li>Transparent monthly reporting</li></ul>
<p><em>Note: Rizen Digital is headquartered in Kolkata, India, and serves Toronto clients remotely.</em></p>''',
        'meta_title': 'Digital Marketing Agency in Toronto | Rizen Digital',
        'meta_description': 'Rizen Digital helps Toronto businesses grow through SEO, digital marketing, and conversion-focused web development, delivered remotely.',
        'faqs': [
            ('Does Rizen Digital have a physical office in Toronto?', 'No. Rizen Digital is based in Kolkata, India, and serves Toronto clients remotely through video calls, shared reporting, and asynchronous communication.'),
        ],
    },
    {
        'city': 'Sydney', 'country': 'Australia',
        'slug': 'digital-marketing-agency-sydney',
        'headline': 'Digital marketing strategy for Sydney businesses',
        'introduction': 'Rizen Digital supports Sydney businesses with SEO, social media, and web development focused on measurable growth.',
        'content': '''<h2>Global expertise, remote-first delivery</h2>
<p>We apply the same technical SEO, content, and conversion-focused approach we use with clients across India to businesses in Sydney, adapted to the Australian market.</p>
<h2>What we focus on</h2>
<ul><li>Technical SEO audits and fixes</li><li>Content built around Australian buyer search intent</li><li>Conversion-focused website work</li><li>Transparent monthly reporting across time zones</li></ul>
<p><em>Note: Rizen Digital is headquartered in Kolkata, India, and serves Sydney clients remotely.</em></p>''',
        'meta_title': 'Digital Marketing Agency in Sydney | Rizen Digital',
        'meta_description': 'Rizen Digital helps Sydney businesses grow through SEO, digital marketing, and conversion-focused web development, delivered remotely.',
        'faqs': [
            ('Does Rizen Digital have a physical office in Sydney?', 'No. Rizen Digital is based in Kolkata, India, and serves Sydney clients remotely through video calls, shared reporting, and asynchronous communication.'),
            ('How are time zone differences handled for Australian clients?', 'Kolkata and Sydney have a manageable time zone overlap for scheduled calls, and we maintain written reporting so progress stays clear between sessions.'),
        ],
    },
    {
        'city': 'Dubai', 'country': 'United Arab Emirates',
        'slug': 'digital-marketing-agency-dubai',
        'headline': 'Digital marketing strategy for Dubai businesses',
        'introduction': 'Rizen Digital supports Dubai businesses with SEO, social media, and web development focused on measurable growth.',
        'content': '''<h2>Global expertise, remote-first delivery</h2>
<p>We bring the same technical SEO and conversion-focused approach we use with clients across India to businesses in Dubai, adapted to the UAE market.</p>
<h2>What we focus on</h2>
<ul><li>Technical SEO audits and fixes</li><li>Content built around UAE buyer search intent</li><li>Social media optimisation</li><li>Transparent monthly reporting</li></ul>
<p><em>Note: Rizen Digital is headquartered in Kolkata, India, and serves Dubai clients remotely.</em></p>''',
        'meta_title': 'Digital Marketing Agency in Dubai | Rizen Digital',
        'meta_description': 'Rizen Digital helps Dubai businesses grow through SEO, digital marketing, and conversion-focused web development, delivered remotely.',
        'faqs': [
            ('Does Rizen Digital have a physical office in Dubai?', 'No. Rizen Digital is based in Kolkata, India, and serves Dubai clients remotely through video calls, shared reporting, and asynchronous communication.'),
            ('How are time zone differences handled for UAE clients?', 'Kolkata and Dubai have a close time zone overlap, making scheduled calls straightforward alongside regular written reporting.'),
        ],
    },
]


class Command(BaseCommand):
    help = 'Generate location pages for India expansion cities and global target cities.'

    def handle(self, *args, **options):
        service, _ = Service.objects.get_or_create(
            name='Digital Marketing',
            defaults={
                'description': 'Digital marketing strategy built around search visibility, useful content, and measurable growth.',
            },
        )

        created_count = 0
        for location in LOCATIONS:
            faqs = location.pop('faqs')
            page, created = LocationPage.objects.update_or_create(
                slug=location['slug'],
                defaults={
                    **location,
                    'service': service,
                    'is_published': True,
                },
            )
            created_count += 1

            for order, (question, answer) in enumerate(faqs):
                LocationFAQ.objects.update_or_create(
                    location_page=page,
                    question=question,
                    defaults={'answer': answer, 'order': order},
                )

        self.stdout.write(self.style.SUCCESS(f'Created/updated {created_count} location pages.'))
