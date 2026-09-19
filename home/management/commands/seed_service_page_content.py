from django.core.management.base import BaseCommand

from home.models import Page

CONTENT = {
    'digital-marketing': {
        'page_meta_title': 'Digital Marketing Services in Kolkata | Rizen Digital',
        'page_meta_description': 'Rizen Digital plans and runs SEO, social media marketing, and performance marketing campaigns that turn search visibility into qualified leads.',
        'page_content': '''<h1>Digital Marketing Services in Kolkata</h1>
<p>Rizen Digital's digital marketing services combine SEO, social media marketing (SMO), and conversion-focused website work to help businesses in Kolkata and across India attract qualified traffic and turn it into enquiries.</p>
<h2>What our digital marketing service includes</h2>
<ul>
<li><a href="/digital-marketing/seo-company-kolkata/">Search Engine Optimization (SEO)</a> &mdash; technical SEO, on-page optimisation, and content built around real customer search intent.</li>
<li><a href="/digital-marketing/smo/">Social Media Optimization (SMO)</a> &mdash; building and managing a consistent brand presence across social platforms.</li>
<li>Performance marketing &mdash; paid campaigns aligned to measurable business outcomes rather than vanity metrics.</li>
</ul>
<h2>How we work</h2>
<p>Every engagement starts with a diagnosis of your current search and social presence, followed by a practical roadmap and monthly reporting tied to enquiries and leads, not just rankings or impressions.</p>''',
    },
    'digital-marketing/smo': {
        'page_meta_title': 'Social Media Optimization (SMO) Services | Rizen Digital',
        'page_meta_description': 'Grow a consistent, engaged brand presence on social media with SMO services from Rizen Digital, covering strategy, content, and profile optimisation.',
        'page_content': '''<h1>Social Media Optimization (SMO) Services</h1>
<p>Social Media Optimization (SMO) is the practice of optimising a brand's social media profiles and content so that it reaches the right audience, builds engagement, and supports overall search visibility. Rizen Digital manages SMO as part of a wider digital marketing strategy for clients in Kolkata and beyond.</p>
<h2>What's included</h2>
<ul>
<li>Profile setup and optimisation across relevant platforms</li>
<li>Content planning aligned to your brand voice and audience</li>
<li>Community engagement and response management</li>
<li>Performance tracking connected to website traffic and leads</li>
</ul>
<h2>Why SMO matters alongside SEO</h2>
<p>A well-optimised, consistently active social presence reinforces brand trust signals that support your broader <a href="/digital-marketing/seo-company-kolkata/">SEO</a> and digital marketing efforts.</p>''',
    },
    'internet-solution': {
        'page_meta_title': 'Web Development & Internet Solutions | Rizen Digital',
        'page_meta_description': 'Rizen Digital offers full-stack web development and technical internet solutions built for performance, SEO-readiness, and business growth.',
        'page_content': '''<h1>Internet Solutions &amp; Web Development</h1>
<p>Rizen Digital's internet solution service covers full-stack web development for businesses that need a fast, technically sound website as the foundation for their digital marketing.</p>
<h2>What we build</h2>
<ul>
<li><a href="/internet-solution/full-stack-web-development/">Full-stack web development</a> &mdash; custom websites and web applications built with performance and SEO in mind.</li>
<li>Website maintenance and technical support</li>
<li>Site speed and Core Web Vitals improvements</li>
</ul>
<h2>Built to support your marketing</h2>
<p>A technically sound website is the foundation every <a href="/digital-marketing/">digital marketing</a> campaign depends on. We build with crawlability, mobile performance, and conversion paths in mind from the start.</p>''',
    },
    'internet-solution/full-stack-web-development': {
        'page_meta_title': 'Full-Stack Web Development Services | Rizen Digital',
        'page_meta_description': 'Custom full-stack web development from Rizen Digital, covering front-end, back-end, and technical SEO foundations for growing businesses.',
        'page_content': '''<h1>Full-Stack Web Development</h1>
<p>Rizen Digital's full-stack web development service covers both the front-end experience and the back-end systems that power your website, so it performs well for users and search engines alike.</p>
<h2>What's included</h2>
<ul>
<li>Custom website and web application development</li>
<li>Technical SEO foundations: clean markup, fast load times, mobile responsiveness</li>
<li>Integration with content management and lead-capture tools</li>
<li>Ongoing support and maintenance</li>
</ul>
<h2>Why it matters for growth</h2>
<p>A well-built website supports every other part of your <a href="/digital-marketing/">digital marketing</a> strategy, from SEO to conversion rate.</p>''',
    },
    'creative-branding': {
        'page_meta_title': 'Creative Branding Services | Rizen Digital',
        'page_meta_description': 'Rizen Digital offers creative branding services including logo design, motion graphics, and digital media creatives for growing businesses.',
        'page_content': '''<h1>Creative Branding Services</h1>
<p>Rizen Digital's creative branding service helps businesses build a clear, consistent visual identity across their website, social media, and marketing materials.</p>
<h2>What our creative branding service includes</h2>
<ul>
<li><a href="/creative-branding/logo-design/">Logo design</a> &mdash; distinctive, versatile logos that work across every platform.</li>
<li><a href="/creative-branding/motion-graphics/">Motion graphics</a> &mdash; animated content for social media, ads, and video.</li>
<li><a href="/creative-branding/digital-media-creatives/">Digital media creatives</a> &mdash; graphics and creative assets for campaigns and social channels.</li>
</ul>
<h2>Brand consistency drives trust</h2>
<p>Consistent branding across every touchpoint reinforces the trust signals that support your <a href="/digital-marketing/">digital marketing</a> and SEO efforts.</p>''',
    },
    'creative-branding/logo-design': {
        'page_meta_title': 'Logo Design Services | Rizen Digital',
        'page_meta_description': 'Custom logo design from Rizen Digital, built to give your brand a distinctive, professional identity across every platform.',
        'page_content': '''<h1>Logo Design Services</h1>
<p>A well-designed logo is often the first impression a customer has of your business. Rizen Digital's logo design service creates distinctive, versatile marks that work across web, print, and social media.</p>
<h2>Our process</h2>
<ul>
<li>Understanding your brand, audience, and industry</li>
<li>Concept development and initial design options</li>
<li>Refinement based on your feedback</li>
<li>Final delivery in formats ready for web and print use</li>
</ul>
<p>Logo design is part of our broader <a href="/creative-branding/">creative branding</a> service, helping ensure visual consistency across your marketing.</p>''',
    },
    'creative-branding/motion-graphics': {
        'page_meta_title': 'Motion Graphics Services | Rizen Digital',
        'page_meta_description': 'Rizen Digital creates motion graphics and animated content for social media, advertising, and video, built to fit your brand identity.',
        'page_content': '''<h1>Motion Graphics Services</h1>
<p>Animated, motion-driven content consistently earns higher engagement on social media and video platforms. Rizen Digital's motion graphics service produces animated assets tailored to your brand and campaign goals.</p>
<h2>What we produce</h2>
<ul>
<li>Short-form animated content for social media</li>
<li>Animated ad creatives</li>
<li>Explainer and promotional video graphics</li>
</ul>
<p>Motion graphics work alongside our <a href="/creative-branding/">creative branding</a> and <a href="/digital-marketing/smo/">social media optimization</a> services to build a consistent, engaging brand presence.</p>''',
    },
    'creative-branding/digital-media-creatives': {
        'page_meta_title': 'Digital Media Creatives | Rizen Digital',
        'page_meta_description': 'Rizen Digital designs digital media creatives, including social media graphics and campaign assets, aligned to your brand identity.',
        'page_content': '''<h1>Digital Media Creatives</h1>
<p>Rizen Digital's digital media creatives service covers the graphic design work behind your social media posts, ad campaigns, and digital marketing materials.</p>
<h2>What's included</h2>
<ul>
<li>Social media post and story graphics</li>
<li>Campaign and advertising creative assets</li>
<li>Brand-consistent templates for ongoing content</li>
</ul>
<p>Digital media creatives are typically produced alongside our <a href="/digital-marketing/smo/">social media optimization</a> and <a href="/creative-branding/">creative branding</a> services.</p>''',
    },
}


class Command(BaseCommand):
    help = 'Seed real SEO content into the placeholder-only service/subservice pages.'

    def handle(self, *args, **options):
        updated = 0
        missing = []
        for page_tag, fields in CONTENT.items():
            page = Page.objects.filter(page_tag=page_tag).first()
            if not page:
                missing.append(page_tag)
                continue
            page.page_meta_title = fields['page_meta_title']
            page.page_meta_description = fields['page_meta_description']
            page.page_meta_keyword = page.page_meta_keyword or fields['page_meta_title']
            page.page_content = fields['page_content']
            page.save(update_fields=[
                'page_meta_title', 'page_meta_description', 'page_meta_keyword', 'page_content',
            ])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Updated content for {updated} pages.'))
        if missing:
            self.stdout.write(self.style.WARNING(f'Page tags not found: {missing}'))
