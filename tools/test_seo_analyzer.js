// Unit tests for the Studio SEO analyzer.  Run: node tools/test_seo_analyzer.js
const assert = require('assert');
const { analyze } = require('../studio/static/studio/seo-panel.js');

const long = (kw) => `<p>${kw} is the way most small businesses start growing online. ` + 'We help teams plan practical work and measure what matters every month. '.repeat(40) + '</p>' +
    `<h2>Why ${kw} matters</h2><p>${'Clear plans beat guesswork. '.repeat(30)}</p><h2>Getting started</h2><p>${'Start small and keep improving. '.repeat(30)}</p>` +
    `<p><img src="a.jpg" alt="${kw} dashboard"> Read the <a href="/about/">about page</a> and this <a href="https://developers.google.com/search">Google guide</a>.</p>`;

const good = analyze({ keyword: 'seo services', title: 'SEO Services', seoTitle: '7 Proven SEO Services for Growing Businesses', description: 'Discover SEO services that help growing businesses earn more qualified traffic. Get a free plan today.',
    slug: 'seo-services', html: long('SEO services'), host: 'www.rizendigital.com', minWords: 600, duplicate: [] });
const bare = analyze({ keyword: '', title: 'Untitled', seoTitle: '', description: '', slug: '', html: '<p>Short.</p>', host: 'x.com', minWords: 600, duplicate: [] });
const get = (r, id) => r.groups.flatMap(g => g.tests).find(t => t.id === id);

assert(good.score >= 81, 'well-optimised page should score green, got ' + good.score);
assert(bare.score <= 30, 'empty page should score red, got ' + bare.score);
for (const id of ['kw-set', 'kw-title', 'kw-desc', 'kw-url', 'kw-first', 'kw-content', 'kw-heading', 'kw-alt', 'external', 'internal', 'unique', 'media']) {
    assert.strictEqual(get(good, id).status, 'pass', id + ' should pass');
}
assert.strictEqual(get(bare, 'kw-set').status, 'fail');

// individual behaviours
const stuffed = analyze({ keyword: 'seo', title: 't', seoTitle: 'SEO', description: 'seo', slug: 'seo', html: '<p>' + 'seo '.repeat(80) + '</p>', host: 'x.com', minWords: 10 });
assert.strictEqual(get(stuffed, 'density').status, 'warn', 'keyword stuffing must be flagged');
const noKwInTitle = analyze({ keyword: 'web design', title: 'x', seoTitle: 'Our great services', description: 'd', slug: 'x', html: '<p>hi</p>', host: 'x.com' });
assert.strictEqual(get(noKwInTitle, 'kw-title').status, 'fail');
const dup = analyze({ keyword: 'seo', title: 'x', seoTitle: 'SEO tips', description: 'seo', slug: 'seo', html: '<p>seo</p>', host: 'x.com', duplicate: [{ title: 'Other page' }] });
assert.strictEqual(get(dup, 'unique').status, 'fail', 'cannibalisation must fail');
assert(/Other page/.test(get(dup, 'unique').text));
const internal = analyze({ keyword: 'a', title: 'a', seoTitle: 'a', description: 'a', slug: 'a', html: '<p><a href="https://www.rizendigital.com/x/">i</a> <a href="https://other.com/y">e</a> <a href="mailto:a@b.c">m</a></p>', host: 'rizendigital.com' });
assert.strictEqual(get(internal, 'internal').status, 'pass');
assert.strictEqual(get(internal, 'external').status, 'pass');
const longSlug = analyze({ keyword: 'a', title: 'a', seoTitle: 'a', description: 'a', slug: 'x'.repeat(90), html: '<p>a</p>', host: 'x.com' });
assert.strictEqual(get(longSlug, 'url-len').status, 'fail');
const longPara = analyze({ keyword: 'a', title: 'a', seoTitle: 'a', description: 'a', slug: 'a', html: '<p>' + 'word '.repeat(200) + '</p>', host: 'x.com' });
assert.strictEqual(get(longPara, 'paras').status, 'warn');
assert.strictEqual(get(analyze({ keyword: 'a', title: 'a', seoTitle: 'Top 10 tips', description: '', slug: 'a', html: '', host: 'x.com' }), 't-number').status, 'pass');
// robust to hostile / odd input
analyze({ keyword: '<script>alert(1)</script>', title: null, seoTitle: undefined, description: null, slug: null, html: '<<<>>><p onclick=x>' });
console.log('analyzer tests passed: good=' + good.score + ' bare=' + bare.score);
