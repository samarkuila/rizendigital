# Content Guide: Blog Posts and Bulk Location Pages

Everything here is done in **Rizen Studio** at `/studio/` (staff login required; 8 failed logins per 10 minutes locks the IP out temporarily). Django admin at `/admin/` also works but Studio is the intended tool.

---

## 1. Posting a blog post

**Studio → Blog posts → New** (`/studio/blog/new/`)

| Field | What to enter | Limit / rule |
|---|---|---|
| Title | Post headline (H1 on the page) | max 180 chars |
| Slug | URL part. Auto-built from the title if left blank and made unique | Live URL: `/blog/<slug>/` |
| Excerpt | Summary shown on the blog listing | max 500 chars |
| Content | Article body, HTML | Aim for **600+ words** (the SEO panel warns below that) |
| Meta title | Search result title | max 60 chars |
| Meta description | Search result snippet | max 160 chars |
| Featured image | Upload or pick from Media library | Add descriptive file name |
| Author | Defaults to "Rizen Digital" | |
| Published | Tick to make it live | Unticked = draft, not public |
| Published at | Date/time shown on the post | Auto-set to now if you tick Published and leave it blank. Set a date to backdate |
| Focus keyword | The one phrase the post targets | Drives the SEO score |
| Hide from search engines | Adds `noindex` and removes it from the sitemap | Leave off normally |
| Canonical URL | Only if the content duplicates another URL | Leave blank normally |
| Social title / description / image | Open Graph overrides | Optional; falls back to meta fields |

### Steps
1. Open **Blog posts → New**.
2. Fill Title, Excerpt, Content. Paste HTML using `<h2>`, `<h3>`, `<p>`, `<ul>`, `<a>`, `<img alt="...">`. Do **not** use `<h1>` (the title is the H1). Template tags like `{% ... %}` are not supported.
3. Set the Focus keyword and write the Meta title and Meta description. Watch the SERP preview and SEO score panel (target 80+).
4. Add a featured image.
5. Use the internal-link suggestions (Studio `api/links`) to link to 2-3 service or other blog pages.
6. Save as draft first and preview, then tick **Published** and save.
7. Confirm at `https://<your-domain>/blog/<slug>/` and that it appears in `/sitemap.xml`.

### Editing / unpublishing
- Edit: Blog posts list → click the post.
- Unpublish: untick Published (it disappears from `/blog/` and the sitemap).
- Bulk publish/unpublish/delete: tick rows in the list and use the bulk action menu.
- Export all posts: `/studio/blog/export.csv`.

### Quality checklist
- One clear topic per post, matching a real search intent.
- Original, useful content (no spun or auto-generated filler).
- Title contains the focus keyword; meta description is a genuine summary.
- Every image has alt text.
- At least 2 internal links and 1 relevant external source.

---

## 2. Bulk location pages

Creates one page per **service × city** combination at `/locations/<slug>/`.

**Studio → Bulk locations** (`/studio/bulk/locations/`)

### Prerequisite
The services must already exist (Studio → Services). Only services you tick are used.

### Form fields

| Field | Purpose | Default |
|---|---|---|
| Services | Tick one or more | none |
| Cities | One city per line (format below) | empty |
| Slug pattern | URL builder | `{service_slug}-{city_slug}` |
| Headline | H1 | `{service} for businesses in {city}` |
| Intro variants | One intro per line; rotated across pages to reduce duplication | 3 built-in variants |
| Meta title | Trimmed to 60 chars | `{service} in {city} \| Rizen Digital` |
| Meta description | Trimmed to 160 chars | see form |
| Content | HTML body template | built-in template |
| FAQs | One per line as `Question \| Answer` | 2 built-in FAQs |
| If page exists | **Skip** (default) or **Update** | Skip |
| Publish immediately | Off = created as drafts | Off |

### City line format
Pipe-separated (preferred):

```
City | Country | Local note | Latitude | Longitude
```

Comma format also works: `City, Country, Local note`. Lines starting with `#` are ignored. Country defaults to India. Only City is required.

Example:

```
Howrah | India | Howrah has a dense mix of manufacturing and trading firms around the Bally and Shibpur belts. | 22.5958 | 88.2636
Durgapur | India | Steel, engineering and B2B suppliers make up much of Durgapur's search demand.
Siliguri | India | Siliguri is the trade gateway to North Bengal, Sikkim and Bhutan.
```

### Placeholders
Use in slug, headline, intros, meta, content and FAQs:

`{city}` `{country}` `{service}` `{service_lower}` `{service_slug}` `{city_slug}`

In **Content** you can also use `{local_note_block}`, which becomes `<p>your local note</p>` (empty if no note was given).

### Steps
1. Open Bulk locations, tick services, paste cities.
2. Adjust templates if needed (defaults are safe).
3. Click **Preview**. Nothing is saved. Each row shows a status:
   - **new**: will be created
   - **update**: existing slug, will be overwritten (only if "Update" chosen)
   - **skip**: existing slug, left untouched
   - **error**: will not be created (missing city, duplicate slug, bad lat/lng, template tags in content)
4. Read the warnings, especially **"No local note"**.
5. Click **Create**. All rows are saved in one transaction.
6. Review drafts in **Locations**, then publish (edit individually or use the bulk action). Or tick "Publish immediately" if you have already reviewed the preview.

### Limits
- **300 pages per run** (services × cities). Extra cities are dropped with a notice.
- Slugs must be unique across all location pages.
- On update, the page's existing FAQs are replaced by the ones in the form.

### Avoiding thin / duplicate content (important for SEO)
Google can treat pages that only swap the city name as doorway pages. To stay safe:
- **Always fill the Local note** with something true and specific to that city.
- Add 3+ different intro variants.
- Only create pages for cities you can genuinely serve. Rizen Digital is Kolkata-based, so pages for other cities must say the work is delivered remotely (the built-in content should be edited to say so).
- Publish in small batches (10-30), check indexing in Search Console, then continue.
- Add unique details afterward for priority cities (map embed URL, case study, local FAQs).

### Single or hand-written location pages
Studio → Location pages → New. Extra fields there: Google Maps embed URL, latitude/longitude.

### Seeding from code
`python manage.py generate_location_pages` loads the 12 predefined city pages (Howrah, Durgapur, Siliguri, Mumbai, Delhi, Bengaluru, New York, Los Angeles, London, Toronto, Sydney, Dubai) under the "Digital Marketing" service and publishes them. Re-running updates them rather than duplicating.

---

## 3. Bulk pages (generic service or landing pages)

**Studio → Bulk pages** (`/studio/bulk/pages/`), download a starter file at `/studio/bulk/pages/template.csv`.

Two modes:

**Paste/CSV mode.** First row is headers. Accepted column names (aliases in brackets):

| Column | Aliases |
|---|---|
| `page_name` | name, title, page |
| `page_tag` (URL slug) | slug, url, tag |
| `meta_title` | seo_title |
| `meta_description` | description, seo_description |
| `keywords` | meta_keywords, keyword |
| `content` | body, html |
| `short_content` | summary, excerpt |
| `post_type` | type (`Page`, `Blog` or `Custom_Page`; default `Custom_Page`) |
| `image_alt` | |

Comma, tab, semicolon and pipe delimiters are auto-detected. Plain-text content is wrapped into paragraphs.

**Template mode.** One page per line, `Name` or `Name | slug`, with `{name}`, `{slug}`, `{keyword}` in the content, title and description templates.

Rules: slugs are lowercase letters, numbers, hyphens; reserved slugs (`blog`, `about`, `contact`, `locations`, `studio`, `admin`, etc.) are rejected; max 300 rows; pages under 150 words get a thin-content warning; Preview first, then Create.

> Bulk blog posts are not supported. Blog posts go through the single-post form above (or `post_type = Blog` in Bulk pages, which creates a generic page, not a `BlogPost`).

---

## 4. After publishing

1. Check the page loads and the canonical/title look right (view source).
2. Confirm it appears in `/sitemap.xml` (drafts and noindex pages are excluded).
3. In Google Search Console: **URL Inspection → Request indexing** for key pages, and submit `/sitemap.xml` once.
4. Production: content saved in Studio is stored in the database, so no redeploy is needed. Code changes are deployed with `deploy/update.sh` (see `deploy/DEPLOY.md`). Back up the DB with `deploy/backup.sh`.

## 5. Troubleshooting

| Problem | Cause / fix |
|---|---|
| Post not visible on `/blog/` | Published is unticked, or Published at is in the future |
| "Duplicate slug" in bulk preview | Two rows produce the same slug; change the slug pattern or city name |
| Row shows "skip" | Slug already exists; switch "If page exists" to Update |
| "Template tags are not allowed" | Remove `{% ... %}` or `{# ... #}` from content |
| Latitude/longitude error | Use plain decimals like `22.5958` |
| Meta title/description shortened | Auto-trimmed to 60/160 chars; edit the template to control the wording |
| Locked out of Studio | Wait 10 minutes (login rate limit) |
