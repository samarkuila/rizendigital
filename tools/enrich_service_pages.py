"""Append longer, genuinely useful sections to the thin service pages (idempotent).

Run:  python manage.py shell < tools/enrich_service_pages.py     (locally and on the server)
"""
from home.models import Page

MARK = '<!-- rd-extended -->'

EXTRA = {
    'creative-branding/logo-design': """
<h2>What makes a logo work</h2>
<p>A logo has to do more than look good on a presentation slide. It needs to stay legible at a favicon size, hold up in one colour, sit comfortably on a dark or light background, and still feel like your business on a shop sign, an invoice, or a social profile picture. We design with those real-world uses in mind from the first sketch, so you do not discover a problem after the printing has been paid for.</p>
<h2>What you receive</h2>
<ul>
<li>A primary logo plus horizontal, stacked, and icon-only variations</li>
<li>Colour, black, and white versions for light and dark backgrounds</li>
<li>Files for web (SVG, PNG) and print-ready formats</li>
<li>Simple usage notes covering colours, fonts, and spacing so anyone on your team can apply the brand consistently</li>
</ul>
<h2>Who this service is for</h2>
<p>New businesses that need an identity to launch with, established companies whose logo no longer reflects what they do, and teams that have grown across several platforms and now need consistency. If you already have a logo that works, we can also tidy it up, rebuild it as clean vector artwork, and prepare the formats you are missing.</p>
<h2>Questions to think about before we start</h2>
<p>Who are your customers, and what should they feel when they see your name? Which competitors do you want to look different from? Where will the logo appear most often? A short conversation about these points usually saves several rounds of revisions and leads to a mark that fits the business rather than following a passing trend.</p>
<p>Ready to talk about your brand? <a href="/contact/">Contact our Kolkata team</a> for a free consultation.</p>
""",
    'creative-branding/digital-media-creatives': """
<h2>Design that keeps your feed consistent</h2>
<p>Most businesses do not struggle with ideas; they struggle with producing good-looking posts week after week without every image looking different. We build a small set of templates around your colours, fonts, and tone, then use it to produce your daily and weekly creatives so your profiles feel like one brand instead of a scrapbook.</p>
<h2>Formats we produce</h2>
<ul>
<li>Feed posts, carousels, stories, and cover images for the major social platforms</li>
<li>Display and social advertising creatives in the sizes each platform requires</li>
<li>Email headers, web banners, and simple brochures or flyers</li>
<li>Festival, offer, and announcement designs prepared in advance of the dates that matter to your customers</li>
</ul>
<h2>How the work runs</h2>
<p>We agree on a monthly plan with you first: the topics, the offers, and the dates that matter. Designs are delivered for approval before anything is published, and we keep the source files organised so your brand assets stay reusable. When a campaign performs well, we reuse what worked and adjust what did not, rather than starting again from a blank canvas every month.</p>
<h2>Why it supports your results</h2>
<p>Creative quality affects how long people stay on a post, whether they trust an advert, and whether they remember your name when they are ready to buy. Well-made creatives therefore support both your paid campaigns and your organic reach. To see how we pair design with distribution, read about our <a href="/digital-marketing/smo/">social media optimization</a> service or <a href="/contact/">contact us</a> to discuss your next campaign.</p>
""",
    'creative-branding/motion-graphics': """
<h2>Why motion earns attention</h2>
<p>Movement is one of the fastest ways to stop someone scrolling. A ten-second animated clip can explain a product, announce an offer, or introduce your brand more clearly than a static image, and it is easy to repurpose across social platforms, your website, and paid campaigns.</p>
<h2>Typical projects</h2>
<ul>
<li>Animated logo reveals and brand intros</li>
<li>Short explainer clips that show how a product or service works</li>
<li>Animated social posts, stories, and reel-style promotional videos</li>
<li>Animated banners and video adverts for paid campaigns</li>
<li>Infographic-style animations that make data or processes easier to follow</li>
</ul>
<h2>Our production process</h2>
<p>Every project starts with a short brief covering the goal, audience, platform, and length. We then write a simple script or storyboard for your approval, design the visual style, animate, and add sound where needed. You review the work at clear checkpoints, so changes are cheap and the final piece matches what you expected. Files are supplied in the sizes and formats each platform needs.</p>
<h2>Keeping it useful</h2>
<p>We keep animation purposeful: clear message, readable text, and a call to action, rather than movement for its own sake. Captions are added so videos work with the sound off, which is how many people watch on mobile. If you already have brand guidelines, we follow them; if not, our <a href="/creative-branding/logo-design/">logo design</a> and branding work can supply them.</p>
<p>Have a video idea or a campaign coming up? <a href="/contact/">Get in touch</a> and we will suggest the format that fits your budget.</p>
""",
    'internet-solution/full-stack-web-development': """
<h2>What full-stack means in practice</h2>
<p>The front end is everything a visitor sees and touches: layout, navigation, forms, and how quickly the page appears. The back end is what makes it work: the database, admin panel, business logic, integrations, and security. When one team handles both, decisions about design, speed, and search visibility are made together instead of being negotiated between separate vendors.</p>
<h2>What we build</h2>
<ul>
<li>Business and service websites with an easy-to-use admin panel</li>
<li>Landing pages built for campaigns, with tracking set up from day one</li>
<li>Blogs, resource libraries, and location or service page systems that scale</li>
<li>Booking, enquiry, and lead-capture workflows connected to email or your CRM</li>
<li>Custom web applications and dashboards for internal use</li>
</ul>
<h2>Built for speed, search, and security</h2>
<p>We treat performance as a feature. That means compressed and correctly sized images, minimal and minified code, sensible caching, and clean markup that both people and search engines can understand. We also add the basics that protect a site: HTTPS, secure forms, regular updates, and backups.</p>
<h2>How a project runs</h2>
<p>We begin with your goals and content, agree on the structure, and design the key pages. Development follows in stages, with a working preview you can test. Before launch we check speed, mobile layout, forms, and tracking. After launch, we offer support and maintenance so fixes and improvements do not wait in a queue.</p>
<p>Explore how a good site supports <a href="/digital-marketing/">digital marketing</a> or <a href="/contact/">contact us</a> to discuss your project.</p>
""",
}

for tag, html in EXTRA.items():
    page = Page.objects.filter(page_tag=tag).first()
    if not page:
        print('missing', tag)
        continue
    if MARK in page.page_content:
        print('already extended', tag)
        continue
    page.page_content = page.page_content.rstrip() + '\n' + MARK + html
    page.save()
    print('extended', tag, len(page.page_content))
