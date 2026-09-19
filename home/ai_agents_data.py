"""AI agent roster shown on the home page and on /ai-agents/.

Edit this file to rename agents, change their tasks or add new ones. Artwork lives in
static/assets/img/agents/<slug>.svg (generated; see deploy/ notes) .
"""

AGENTS = [
    {
        'slug': 'scout',
        'name': 'Scout',
        'role': 'SEO Research Agent',
        'service': 'SEO',
        'color': '#7df9ff',
        'tagline': 'Finds the searches your customers make before you know to ask.',
        'description': (
            'Scout studies your market and turns it into a ranked opportunity list. It maps keywords, questions and '
            'competitors by search intent, so every page we plan targets real demand instead of guesswork.'
        ),
        'tasks': [
            'Keyword and search-intent research for every service and location',
            'Competitor gap analysis: what they rank for and you do not',
            'Topic clusters that build authority, not thin one-off pages',
            'Local keyword discovery for Kolkata and your other service areas',
            'SERP feature spotting: snippets, local packs, AI answers',
        ],
        'tools': ['Search Console', 'SERP analysis', 'Keyword data', 'Spreadsheets'],
        'console': [
            "scout run keyword-gap --site client.com",
            'crawling top results for 40 seed terms ...',
            'grouped keywords into topic clusters by intent',
            'flagged questions where competitors are weak',
            'ranked opportunities by demand vs. difficulty',
            'done: opportunity list ready for review',
        ],
    },
    {
        'slug': 'atlas',
        'name': 'Atlas',
        'role': 'Technical SEO Agent',
        'service': 'Technical SEO',
        'color': '#b6ff6a',
        'tagline': 'Keeps your site crawlable, fast and error-free, around the clock.',
        'description': (
            'Atlas watches the technical health of your website. It crawls, finds what blocks Google from seeing your '
            'pages and flags speed, indexing and structured-data problems before they cost you rankings.'
        ),
        'tasks': [
            'Scheduled site crawls that catch broken links and redirect chains',
            'Core Web Vitals and page-speed monitoring',
            'Structured data (schema) validation on every template',
            'Indexation and XML sitemap checks in Search Console',
            'Mobile-friendliness and HTTPS security checks',
        ],
        'tools': ['Site crawler', 'Core Web Vitals', 'Schema validator', 'Search Console'],
        'console': [
            'atlas run site-audit --depth 4',
            'crawled pages, checking status codes ...',
            'found broken links and redirect chains',
            'measured Core Web Vitals on key templates',
            'validated structured data on all page types',
            'done: prioritised fix list generated',
        ],
    },
    {
        'slug': 'quill',
        'name': 'Quill',
        'role': 'Content Strategy Agent',
        'service': 'Content',
        'color': '#ffd166',
        'tagline': 'Turns search intent into briefs and drafts that our editors make excellent.',
        'description': (
            'Quill prepares the groundwork for people-first content: intent-based briefs, outlines and first drafts, '
            'plus checklists for sources, authorship and originality. A human editor adds real experience and signs off '
            'before anything is published.'
        ),
        'tasks': [
            'Content briefs built from search intent and the pages that rank',
            'Outlines and first drafts prepared for expert editing',
            'E-E-A-T checklists: authors, sources, first-hand evidence',
            'Refresh audits that find ageing pages worth updating',
            'Internal-linking suggestions to strengthen topic clusters',
        ],
        'tools': ['Brief templates', 'Fact-check prompts', 'Editorial calendar', 'Plagiarism checks'],
        'console': [
            'quill run brief --topic "seo services kolkata"',
            'analysing intent behind the top-ranking pages ...',
            'drafted outline with questions readers ask',
            'added source and expert-review checklist',
            'queued for human editor before publishing',
            'done: brief and draft ready for review',
        ],
    },
    {
        'slug': 'pulse',
        'name': 'Pulse',
        'role': 'Social Media Agent',
        'service': 'Social Media',
        'color': '#ffe27a',
        'tagline': 'Keeps your brand active, consistent and part of the conversation.',
        'description': (
            'Pulse plans and prepares your social presence. It builds content calendars, drafts posts in your brand voice, '
            'repurposes long content into short formats and prepares engagement replies for your team to approve.'
        ),
        'tasks': [
            'Monthly content calendars aligned to campaigns and events',
            'Post, caption and hashtag drafts in your brand voice',
            'Repurposing blogs and case studies into short-form posts',
            'Best-time-to-post analysis per platform',
            'Comment and message reply drafts for approval',
        ],
        'tools': ['Content calendar', 'Scheduler', 'Platform insights', 'Brand voice guide'],
        'console': [
            'pulse run calendar --month next',
            'pulling top-performing posts and audience insights ...',
            'drafted posts for each platform in brand voice',
            'matched posts to best publishing times',
            'prepared reply drafts for the community team',
            'done: calendar ready for approval',
        ],
    },
    {
        'slug': 'ledger',
        'name': 'Ledger',
        'role': 'Paid Ads Agent',
        'service': 'PPC & Ads',
        'color': '#fff2b3',
        'tagline': 'Watches every rupee of ad spend so budgets go where they convert.',
        'description': (
            'Ledger monitors your Google and social ad accounts. It tests copy variations, mines search terms, finds wasted '
            'spend and alerts the team when budgets, bids or results drift off target.'
        ),
        'tasks': [
            'Ad copy and headline variations for A/B testing',
            'Search-term mining and negative keyword suggestions',
            'Wasted-spend detection and budget pacing alerts',
            'Audience and placement performance summaries',
            'Landing-page and conversion tracking checks',
        ],
        'tools': ['Google Ads', 'Meta Ads', 'Conversion tracking', 'Budget alerts'],
        'console': [
            'ledger run spend-review --range 30d',
            'reading campaign, keyword and search-term data ...',
            'found search terms that spend without converting',
            'suggested negative keywords and new ad variants',
            'checked budget pacing against monthly target',
            'done: optimisation plan queued for approval',
        ],
    },
    {
        'slug': 'vega',
        'name': 'Vega',
        'role': 'Analytics & Reporting Agent',
        'service': 'Analytics',
        'color': '#c8ffd9',
        'tagline': 'Turns raw numbers into clear answers, and warns you when something changes.',
        'description': (
            'Vega connects the dots between search, traffic and leads. It builds dashboards, watches for unusual movement, '
            'compares performance before and after Google updates, and writes the monthly report in plain language.'
        ),
        'tasks': [
            'Live dashboards from GA4 and Search Console',
            'Anomaly alerts for sudden traffic or ranking drops',
            'Before-and-after impact checks around Google core updates',
            'Monthly reports written in plain language, not jargon',
            'Lead and conversion attribution summaries',
        ],
        'tools': ['GA4', 'Search Console', 'Looker Studio', 'Alerts'],
        'console': [
            'vega run update-impact --baseline 28d',
            'comparing clicks and impressions before and after ...',
            'segmented changes by page and query group',
            'isolated the pages that moved most',
            'wrote a plain-language summary with next steps',
            'done: report ready for the strategist',
        ],
    },
    {
        'slug': 'prism',
        'name': 'Prism',
        'role': 'Creative & Brand Agent',
        'service': 'Creative Branding',
        'color': '#ffe066',
        'tagline': 'Explores creative directions fast, so designers spend time on the best ones.',
        'description': (
            'Prism supports the creative team with brand-voice guides, moodboards, concept ideas and ad or social creative '
            'variations. It checks tone and consistency across every asset, and designers refine the final work.'
        ),
        'tasks': [
            'Brand voice and messaging guides',
            'Moodboards and concept directions for logos and campaigns',
            'Ad and social creative variations to test',
            'Tone and consistency checks across copy and visuals',
            'Motion and media creative ideas for short-form video',
        ],
        'tools': ['Design tools', 'Moodboards', 'Brand guidelines', 'Asset library'],
        'console': [
            'prism run concepts --brand client',
            'reading brand guidelines and past campaigns ...',
            'generated three creative directions with rationale',
            'produced visual and copy variations to test',
            'checked every asset against the brand voice',
            'done: shortlist ready for the designer',
        ],
    },
    {
        'slug': 'echo',
        'name': 'Echo',
        'role': 'Lead & Customer Agent',
        'service': 'Lead Response',
        'color': '#9bf0ff',
        'tagline': 'Answers every enquiry quickly, so no lead waits for a reply.',
        'description': (
            'Echo responds to website and social enquiries straight away. It answers common questions, qualifies leads with '
            'a few smart questions, books calls and hands complex conversations to a person with the full context.'
        ),
        'tasks': [
            'Instant first response to website and social enquiries',
            'Lead qualification: budget, goals, timeline',
            'Call and consultation booking',
            'Follow-up reminders so no lead goes cold',
            'Smooth hand-off to the team with the conversation summary',
        ],
        'tools': ['Contact forms', 'Chat', 'Calendar booking', 'CRM notes'],
        'console': [
            'echo run inbox --new-enquiries',
            'reading new enquiry from the contact form ...',
            'answered pricing and service questions',
            'qualified the lead: goals, budget, timeline',
            'booked a consultation slot and notified the team',
            'done: lead handed over with full summary',
        ],
    },
    {
        'slug': 'forge',
        'name': 'Forge',
        'role': 'Web Development Agent',
        'service': 'Web Development',
        'color': '#ff9f43',
        'tagline': 'Builds, tests and ships fast, accessible pages that hold up in search.',
        'description': (
            'Forge helps our developers build and maintain your website. It scaffolds pages and components, runs accessibility '
            'and speed checks on every change, and tests before anything goes live.'
        ),
        'tasks': [
            'Page and component scaffolding from approved designs',
            'Accessibility checks for names, contrast and keyboard use',
            'Speed budgets: image, CSS and script optimisation',
            'Automated regression tests before each release',
            'Deployment checks and rollback readiness',
        ],
        'tools': ['Code review', 'Lighthouse', 'Test runner', 'Deploy pipeline'],
        'console': [
            'forge run release-check --build latest',
            'running accessibility and performance checks ...',
            'fixed missing labels and oversized images',
            'ran regression tests on key pages',
            'verified the deploy and rollback plan',
            'done: build approved for release',
        ],
    },
]

HOW_IT_WORKS = [
    ('Brief', 'You share your goals, audience and constraints. We turn them into clear instructions for the right agents.'),
    ('Agents execute', 'Agents research, audit, draft and monitor around the clock, doing the repetitive heavy lifting in minutes.'),
    ('Specialists review', 'A human specialist checks every output for accuracy, originality and brand fit before it goes anywhere.'),
    ('Report & improve', 'Results and learnings feed back into the plan, so each month starts smarter than the last.'),
]

PRINCIPLES = [
    ('People stay in charge', 'Agents prepare and monitor. A human specialist reviews and approves the work that matters.'),
    ('Quality over volume', 'We do not mass-produce pages. Speed is used to go deeper and check more, not to publish more thin content.'),
    ('Transparent by default', 'You see what each agent did, why, and what a human changed.'),
    ('Built for Google’s standards', 'Helpful, original, trustworthy work that follows the same principles core updates reward.'),
]

FAQ = [
    ('What are AI agents in digital marketing?',
     'AI agents are specialised software assistants that carry out defined marketing tasks, such as keyword research, site audits, '
     'reporting or lead response. Each agent has one focus, and our specialists direct and review what they produce.'),
    ('Do AI agents replace your marketing team?',
     'No. Agents handle research, monitoring and first drafts quickly, and our specialists apply judgement, creativity and '
     'accountability. The result is faster, more thorough work with a person responsible for it.'),
    ('Is AI-generated content safe for SEO?',
     'Search engines reward helpful, original, people-first content however it is produced, and penalise content made mainly to '
     'manipulate rankings. Our agents prepare drafts and checks; editors add first-hand experience and verify facts before publishing.'),
    ('Which agent do I need?',
     'It depends on your goal. Scout and Atlas suit SEO growth, Quill and Prism content and brand, Pulse social media, Ledger paid ads, '
     'Vega reporting, Forge websites and Echo lead response. Contact us and we will recommend the right combination.'),
    ('How do agents keep my data safe?',
     'We only give each agent the access it needs for its task, keep credentials out of shared documents, and review permissions '
     'regularly. Ask us about specific tools and requirements for your business.'),
]
