/* Rizen Studio: Rank-Math-style SEO analysis (focus keyword, live score, previews).
   The analyzer is a pure function (RizenSEO.analyze) so it can be unit-tested in Node. */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) { module.exports = factory(); }
    else { root.RizenSEO = factory(); if (typeof document !== 'undefined') { root.RizenSEO.mount(); } }
})(typeof self !== 'undefined' ? self : this, function () {
    'use strict';

    var POWER = ['free', 'proven', 'ultimate', 'essential', 'complete', 'powerful', 'easy', 'simple', 'best', 'guaranteed', 'secret', 'amazing', 'instant', 'effective', 'exclusive', 'expert', 'definitive', 'practical', 'step-by-step', 'actionable', 'boost', 'unlock', 'master', 'top', 'smart', 'fast', 'quick', 'improve', 'grow', 'discover'];
    var POSITIVE = ['best', 'great', 'good', 'easy', 'simple', 'proven', 'effective', 'powerful', 'improve', 'boost', 'grow', 'success', 'win', 'better', 'trusted', 'smart', 'love', 'amazing', 'helpful', 'reliable', 'affordable', 'perfect'];
    var NEGATIVE = ['worst', 'bad', 'mistake', 'mistakes', 'fail', 'failure', 'avoid', 'never', 'stop', 'wrong', 'problem', 'problems', 'hard', 'difficult', 'risk', 'warning', 'waste', 'lose', 'kill', 'dangerous'];

    function decode(s) { return s.replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;|&rsquo;|&lsquo;/g, "'").replace(/&ldquo;|&rdquo;/g, '"'); }
    function strip(html) { return decode(String(html || '').replace(/<(script|style)[\s\S]*?<\/\1>/gi, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim(); }
    function words(text) { return (text.match(/[\p{L}\p{N}][\p{L}\p{N}'’-]*/gu) || []); }
    function norm(s) { return decode(String(s || '')).toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, ' ').replace(/\s+/g, ' ').trim(); }
    function slugify(s) { return norm(s).replace(/\s+/g, '-'); }
    function countOf(hay, needle) { if (!needle) { return 0; } var n = 0, i = 0; hay = ' ' + hay + ' '; needle = ' ' + needle + ' '; while ((i = hay.indexOf(needle, i)) > -1) { n++; i += needle.length - 1; } return n; }

    function syllables(word) {
        word = word.toLowerCase().replace(/[^a-z]/g, '');
        if (!word) { return 0; }
        if (word.length <= 3) { return 1; }
        word = word.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '').replace(/^y/, '');
        var m = word.match(/[aeiouy]{1,2}/g);
        return Math.max(1, m ? m.length : 1);
    }

    function parse(html) {
        html = String(html || '');
        var headings = [], images = [], links = [], paras = [], m;
        var reH = /<h([1-6])\b[^>]*>([\s\S]*?)<\/h\1>/gi;
        while ((m = reH.exec(html))) { headings.push({ level: +m[1], text: strip(m[2]) }); }
        var reI = /<img\b[^>]*>/gi;
        while ((m = reI.exec(html))) { var a = /alt\s*=\s*["']([^"']*)["']/i.exec(m[0]); images.push({ alt: a ? decode(a[1]).trim() : '' }); }
        var reA = /<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
        while ((m = reA.exec(html))) { links.push({ href: m[1].trim(), text: strip(m[2]) }); }
        var reP = /<p\b[^>]*>([\s\S]*?)<\/p>/gi;
        while ((m = reP.exec(html))) { var t = strip(m[1]); if (t) { paras.push(t); } }
        var text = strip(html);
        if (!paras.length && text) { paras = html.replace(/<[^>]+>/g, '\n').split(/\n\s*\n|\n/).map(function (x) { return decode(x).trim(); }).filter(Boolean); }
        var sentences = text.split(/[.!?]+(?:\s|$)/).map(function (x) { return x.trim(); }).filter(function (x) { return words(x).length > 0; });
        return { text: text, words: words(text), headings: headings, images: images, links: links, paras: paras, sentences: sentences, hasMedia: /<(img|video|iframe)\b/i.test(html) };
    }

    function isInternal(href, host) {
        if (/^(mailto:|tel:|#)/i.test(href)) { return null; }
        if (href.charAt(0) === '/' && href.charAt(1) !== '/') { return true; }
        try { var u = new URL(href, 'https://' + host); return u.hostname.replace(/^www\./, '') === String(host).split(':')[0].replace(/^www\./, ''); } catch (e) { return null; }
    }

    /**
     * input: {keyword, title, seoTitle, description, slug, html, host, minWords, kind, duplicate: [{title,url}] | null}
     * returns {score, band, groups:[{id,title,tests:[{id,status,text,weight}]}], fails, warns, passes}
     */
    function analyze(input) {
        var kw = norm(input.keyword);
        var seoTitle = (input.seoTitle || input.title || '').trim();
        var desc = (input.description || '').trim();
        var slug = (input.slug || '').trim();
        var doc = parse(input.html);
        var total = doc.words.length;
        var minWords = input.minWords || 600;
        var host = input.host || 'localhost';
        var has = !!kw;
        var tests = { basic: [], extra: [], title: [], read: [] };
        var add = function (g, id, weight, status, text) { tests[g].push({ id: id, weight: weight, status: status, text: text }); };
        var pf = function (cond, w) { return cond ? 'pass' : (w || 'fail'); };
        var needKw = 'Set a focus keyword so this can be checked.';

        // ----- Basic SEO
        if (!has) { add('basic', 'kw-set', 3, 'fail', 'Add a focus keyword: the main phrase you want this page to rank for.'); }
        else { add('basic', 'kw-set', 3, 'pass', 'Focus keyword set: “' + input.keyword.trim() + '”.'); }
        var nTitle = norm(seoTitle), inTitle = has && nTitle.indexOf(kw) > -1, startTitle = has && nTitle.indexOf(kw) === 0;
        add('basic', 'kw-title', 3, !has ? 'fail' : inTitle ? (startTitle || nTitle.indexOf(kw) < 20 ? 'pass' : 'warn') : 'fail',
            !has ? needKw : inTitle ? (nTitle.indexOf(kw) < 20 ? 'Focus keyword is at the beginning of the SEO title.' : 'Focus keyword appears in the SEO title. Moving it nearer the start helps.') : 'Add the focus keyword to the SEO title.');
        var inDesc = has && norm(desc).indexOf(kw) > -1;
        add('basic', 'kw-desc', 2, !has ? 'fail' : inDesc ? 'pass' : 'fail', !has ? needKw : inDesc ? 'Focus keyword appears in the meta description.' : 'Add the focus keyword to the meta description.');
        var kwSlug = slugify(input.keyword || ''), inSlug = has && (slug.indexOf(kwSlug) > -1 || kwSlug.split('-').every(function (p) { return slug.indexOf(p) > -1; }));
        add('basic', 'kw-url', 2, !has ? 'fail' : inSlug ? 'pass' : 'fail', !has ? needKw : inSlug ? 'Focus keyword appears in the URL.' : 'Use the focus keyword in the URL slug.');
        var firstN = Math.max(30, Math.ceil(total * 0.1)), first = norm(doc.words.slice(0, firstN).join(' '));
        var inFirst = has && first.indexOf(kw) > -1;
        add('basic', 'kw-first', 2, !has ? 'fail' : inFirst ? 'pass' : 'fail', !has ? needKw : inFirst ? 'Focus keyword appears in the first 10% of the content.' : 'Use the focus keyword near the beginning of your content.');
        var nText = norm(doc.text), occ = countOf(nText, kw);
        add('basic', 'kw-content', 2, !has ? 'fail' : occ > 0 ? 'pass' : 'fail', !has ? needKw : occ > 0 ? 'Focus keyword appears in the content (' + occ + ' time' + (occ === 1 ? '' : 's') + ').' : 'Use the focus keyword in the content.');
        var lenStatus = total >= minWords ? 'pass' : total >= minWords * 0.5 ? 'warn' : 'fail';
        add('basic', 'length', 2, lenStatus, total >= minWords ? 'Content is ' + total + ' words. Great length.' : 'Content is ' + total + ' words. Aim for at least ' + minWords + ' words.');

        // ----- Additional
        var kwHeading = has && doc.headings.some(function (h) { return h.level >= 2 && norm(h.text).indexOf(kw) > -1; });
        add('extra', 'kw-heading', 1, !has ? 'fail' : kwHeading ? 'pass' : 'fail', !has ? needKw : kwHeading ? 'Focus keyword appears in a subheading (H2–H6).' : 'Use the focus keyword in at least one subheading.');
        var kwAlt = has && doc.images.some(function (i) { return norm(i.alt).indexOf(kw) > -1; });
        add('extra', 'kw-alt', 1, !doc.images.length ? 'fail' : !has ? 'fail' : kwAlt ? 'pass' : 'fail',
            !doc.images.length ? 'Add at least one image, with the focus keyword in its alt text.' : !has ? needKw : kwAlt ? 'Focus keyword appears in an image alt attribute.' : 'Add the focus keyword to an image alt attribute.');
        var dens = total ? occ / total * 100 : 0;
        add('extra', 'density', 1, !has ? 'fail' : dens === 0 ? 'fail' : dens > 2.5 ? 'warn' : dens < 0.5 ? 'warn' : 'pass',
            !has ? needKw : dens === 0 ? 'Keyword density is 0%. Use the keyword naturally in the text.' : dens > 2.5 ? 'Keyword density is ' + dens.toFixed(1) + '%: this looks like stuffing. Aim for 0.5–2.5%.' : dens < 0.5 ? 'Keyword density is ' + dens.toFixed(1) + '%. Aim for 0.5–2.5%.' : 'Keyword density is ' + dens.toFixed(1) + '%. Well balanced.');
        add('extra', 'url-len', 1, slug.length && slug.length <= 75 ? 'pass' : 'fail', slug.length && slug.length <= 75 ? 'URL is ' + slug.length + ' characters. Nice and short.' : slug.length ? 'URL is ' + slug.length + ' characters. Keep it under 75.' : 'Add a URL slug.');
        var ext = 0, intl = 0;
        doc.links.forEach(function (l) { var i = isInternal(l.href, host); if (i === true) { intl++; } else if (i === false) { ext++; } });
        add('extra', 'external', 1, ext ? 'pass' : 'fail', ext ? 'Links to ' + ext + ' external source' + (ext === 1 ? '' : 's') + '.' : 'Link out to at least one trustworthy external source.');
        add('extra', 'internal', 1, intl ? 'pass' : 'fail', intl ? 'Contains ' + intl + ' internal link' + (intl === 1 ? '' : 's') + '.' : 'Add internal links to related pages on your site.');
        if (input.duplicate === null || input.duplicate === undefined) { add('extra', 'unique', 1, has ? 'warn' : 'fail', has ? 'Checking whether another page already targets this keyword…' : needKw); }
        else if (!input.duplicate.length) { add('extra', 'unique', 1, has ? 'pass' : 'fail', has ? 'No other page targets this focus keyword.' : needKw); }
        else { add('extra', 'unique', 1, 'fail', 'Also used as the focus keyword on: ' + input.duplicate.map(function (d) { return d.title; }).join(', ') + '. Targeting one keyword on several pages splits your ranking power.'); }

        // ----- Title readability
        var tl = seoTitle.length;
        add('title', 't-len', 1, tl >= 30 && tl <= 60 ? 'pass' : tl === 0 ? 'fail' : 'warn', tl === 0 ? 'Add an SEO title.' : tl >= 30 && tl <= 60 ? 'SEO title is ' + tl + ' characters.' : 'SEO title is ' + tl + ' characters. 30–60 works best.');
        var tw = norm(seoTitle).split(' ');
        add('title', 't-number', 1, /\d/.test(seoTitle) ? 'pass' : 'warn', /\d/.test(seoTitle) ? 'SEO title contains a number.' : 'Adding a number to the title can lift click-through.');
        add('title', 't-power', 1, tw.some(function (w) { return POWER.indexOf(w) > -1; }) ? 'pass' : 'warn', tw.some(function (w) { return POWER.indexOf(w) > -1; }) ? 'SEO title contains a power word.' : 'Add a power word (e.g. proven, complete, essential) to the title.');
        var sent = tw.some(function (w) { return POSITIVE.indexOf(w) > -1 || NEGATIVE.indexOf(w) > -1; });
        add('title', 't-sentiment', 1, sent ? 'pass' : 'warn', sent ? 'SEO title expresses a clear sentiment.' : 'A positive or negative sentiment word makes the title more compelling.');

        // ----- Content readability
        var longParas = doc.paras.filter(function (p) { return words(p).length > 120; }).length;
        add('read', 'paras', 1, !doc.paras.length ? 'fail' : longParas === 0 ? 'pass' : 'warn', !doc.paras.length ? 'Write some content first.' : longParas === 0 ? 'Paragraphs are a comfortable length.' : longParas + ' paragraph' + (longParas === 1 ? ' is' : 's are') + ' over 120 words. Break them up.');
        var wc = Math.max(1, total), sc = Math.max(1, doc.sentences.length), sy = 0;
        doc.words.forEach(function (w) { sy += syllables(w); });
        var flesch = 206.835 - 1.015 * (wc / sc) - 84.6 * (sy / wc);
        add('read', 'flesch', 1, total < 30 ? 'fail' : flesch >= 60 ? 'pass' : flesch >= 40 ? 'warn' : 'fail', total < 30 ? 'Write more content to measure readability.' : 'Reading ease score is ' + Math.round(flesch) + (flesch >= 60 ? ': easy to read.' : flesch >= 40 ? ': fairly difficult. Use shorter words and sentences.' : ': hard to read. Simplify.'));
        var avgSent = total / sc;
        add('read', 'sent', 1, total < 30 ? 'fail' : avgSent <= 20 ? 'pass' : avgSent <= 25 ? 'warn' : 'fail', total < 30 ? 'Write more content to measure sentence length.' : 'Average sentence length is ' + Math.round(avgSent) + ' words' + (avgSent <= 20 ? '.' : '. Aim for 20 or fewer.'));
        var subOk = total <= 300 || (doc.headings.filter(function (h) { return h.level >= 2; }).length >= Math.floor(total / 300));
        add('read', 'subheads', 1, total <= 300 ? 'pass' : subOk ? 'pass' : 'fail', total <= 300 ? 'Short content does not need many subheadings.' : subOk ? 'Subheadings break the content up well.' : 'Add a subheading about every 300 words.');
        add('read', 'media', 1, doc.hasMedia ? 'pass' : 'fail', doc.hasMedia ? 'Content includes images or media.' : 'Add an image or video to support the text.');

        var groups = [
            { id: 'basic', title: 'Basic SEO', tests: tests.basic }, { id: 'extra', title: 'Additional', tests: tests.extra },
            { id: 'title', title: 'Title readability', tests: tests.title }, { id: 'read', title: 'Content readability', tests: tests.read }
        ];
        var got = 0, max = 0, fails = 0, warns = 0, passes = 0;
        groups.forEach(function (g) {
            g.fails = g.tests.filter(function (t) { return t.status === 'fail'; }).length;
            g.warns = g.tests.filter(function (t) { return t.status === 'warn'; }).length;
            g.tests.forEach(function (t) { max += t.weight; if (t.status === 'pass') { got += t.weight; passes++; } else if (t.status === 'warn') { got += t.weight * 0.5; warns++; } else { fails++; } });
        });
        var score = max ? Math.round(got / max * 100) : 0;
        return { score: score, band: score >= 81 ? 'good' : score >= 51 ? 'ok' : 'bad', groups: groups, fails: fails, warns: warns, passes: passes, words: total };
    }

    // ------------------------------------------------------------------ browser panel
    function mount() {
        var panel = document.getElementById('st-rm');
        var mainCard = document.querySelector('[data-rm-main]');
        if (!panel) { return; }
        var cfg = JSON.parse(panel.getAttribute('data-config'));
        var $ = function (s, r) { return (r || document).querySelector(s); };
        var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
        var esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
        var el = function (name) { return document.getElementById('id_' + name); };
        var val = function (name) { var f = name && el(name); return f ? f.value : ''; };
        var state = { duplicate: null };
        var timer, kwTimer;

        var contentHtml = function () {
            return cfg.content.map(function (n) {
                var v = val(n);
                return /<[a-z][^>]*>/i.test(v) ? v : (v ? '<p>' + esc(v) + '</p>' : '');
            }).join('\n');
        };
        var gather = function () {
            return { keyword: val(cfg.keyword), title: val(cfg.title), seoTitle: val(cfg.seoTitle) || val(cfg.title), description: val(cfg.desc), slug: val(cfg.slug),
                     html: contentHtml(), host: cfg.host, minWords: cfg.minWords, kind: cfg.kind, duplicate: state.duplicate };
        };

        var icon = { pass: 'check', warn: 'alert', fail: 'x' };
        var openGroups = {};
        var render = function () {
            var r = analyze(gather());
            var ring = $('[data-rm-ring]', panel);
            ring.style.setProperty('--p', r.score);
            ring.className = 'st-rm-ring st-rm-' + r.band;
            $('[data-rm-score]', panel).textContent = r.score;
            var badge = $('[data-rm-badge]', panel);
            badge.textContent = r.band === 'good' ? 'Good' : r.band === 'ok' ? 'Needs work' : 'Poor';
            badge.className = 'st-rm-badge st-rm-badge-' + r.band;
            var sc = el(cfg.score); if (sc) { sc.value = r.score; }
            $('[data-rm-summary]', panel).textContent = !val(cfg.keyword).trim()
                ? 'Enter a focus keyword to see how well this page is optimised for it.'
                : r.fails ? r.fails + ' test' + (r.fails === 1 ? '' : 's') + ' to fix' + (r.warns ? ' and ' + r.warns + ' to improve' : '') + '. ' + r.passes + ' passed.'
                    : r.warns ? 'Almost there: ' + r.warns + ' improvement' + (r.warns === 1 ? '' : 's') + ' suggested.' : 'Everything passes. This page is fully optimised.';
            var box = $('[data-rm-groups]', panel);
            box.innerHTML = r.groups.map(function (g) {
                var open = openGroups[g.id] !== undefined ? openGroups[g.id] : (g.id === 'basic');
                var meta = g.fails ? '<em class="bad">' + g.fails + ' to fix</em>' : g.warns ? '<em class="warn">' + g.warns + ' to improve</em>' : '<em class="good">All good</em>';
                return '<details data-g="' + g.id + '"' + (open ? ' open' : '') + '><summary><span>' + g.title + '</span>' + meta + '<svg class="ico st-chev"><use href="#i-chevron"/></svg></summary><ul>' +
                    g.tests.map(function (t) { return '<li class="' + t.status + '"><svg class="ico"><use href="#i-' + icon[t.status] + '"/></svg><span>' + esc(t.text) + '</span></li>'; }).join('') + '</ul></details>';
            }).join('');
            $$('details', box).forEach(function (d) { d.addEventListener('toggle', function () { openGroups[d.getAttribute('data-g')] = d.open; }); });
            var dup = $('[data-rm-dup]', panel);
            if (state.duplicate && state.duplicate.length) {
                dup.hidden = false;
                dup.innerHTML = '<b>Keyword already used</b><ul>' + state.duplicate.map(function (d) { return '<li><a href="' + esc(d.url) + '">' + esc(d.title) + '</a> <small>' + esc(d.kind) + '</small></li>'; }).join('') + '</ul>';
            } else { dup.hidden = true; }
        };

        // ---------- previews
        var hi = function (text, kw) {
            var out = esc(text); if (!kw) { return out; }
            try { var re = new RegExp('(' + kw.trim().split(/\s+/).map(function (w) { return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).filter(Boolean).join('|') + ')', 'gi'); return out.replace(re, '<b>$1</b>'); } catch (e) { return out; }
        };
        var cut = function (t, n) { return t.length > n ? t.slice(0, n - 1).trim() + '…' : t; };
        var mobile = false;
        var renderSerp = function () {
            var serp = $('[data-rm-serp]', document); if (!serp) { return; }
            var kw = val(cfg.keyword);
            var title = val(cfg.seoTitle) || val(cfg.title) || 'Your page title';
            var d = val(cfg.desc) || 'Add a meta description so searchers know what this page offers.';
            $('[data-serp-title]', serp).innerHTML = hi(cut(title, 60), kw);
            $('[data-serp-desc]', serp).innerHTML = hi(cut(d, mobile ? 120 : 160), kw);
            var slug = val(cfg.slug);
            $('[data-serp-url]', serp).textContent = (cfg.prefix === '/' ? '' : cfg.prefix.replace(/^\//, '')) + slug + (slug ? '/' : '');
            var meter = function (sel, n, min, max) { var m = $(sel, serp); if (!m) { return; } m.style.setProperty('--w', Math.min(100, Math.round(n / max * 100)) + '%'); m.className = n > max ? 'over' : (n < min && n > 0) ? 'warn' : ''; };
            meter('[data-meter-title]', (val(cfg.seoTitle) || val(cfg.title)).length, 30, 60);
            meter('[data-meter-desc]', val(cfg.desc).length, 70, 160);
            $('[data-serp-card]', serp).classList.toggle('mobile', mobile);
        };
        $$('[data-serp-mode]').forEach(function (b) { b.addEventListener('click', function () { mobile = b.getAttribute('data-serp-mode') === 'mobile'; $$('[data-serp-mode]').forEach(function (x) { x.classList.toggle('on', x === b); }); renderSerp(); }); });

        var socialImg = cfg.ogImageUrl || '';
        var renderSocial = function () {
            var t = val(cfg.ogTitle) || val(cfg.seoTitle) || val(cfg.title) || 'Your page title';
            var d = val(cfg.ogDesc) || val(cfg.desc) || 'Your page description appears here.';
            var set = function (sel, v) { var n = $(sel); if (n) { n.textContent = v; } };
            set('[data-fb-title]', cut(t, 70)); set('[data-fb-desc]', cut(d, 110)); set('[data-tw-title]', cut(t, 70)); set('[data-tw-desc]', cut(d, 120));
            ['[data-fb-img]', '[data-tw-img]'].forEach(function (s) { var n = $(s); if (n) { n.style.backgroundImage = socialImg ? 'url("' + socialImg + '")' : ''; n.classList.toggle('empty', !socialImg); } });
        };
        var fileIn = el(cfg.ogImage);
        if (fileIn) { fileIn.addEventListener('change', function () { if (fileIn.files && fileIn.files[0]) { socialImg = URL.createObjectURL(fileIn.files[0]); renderSocial(); } }); }

        // ---------- tabs
        $$('[data-rm-tab]').forEach(function (b) {
            b.addEventListener('click', function () {
                var tab = b.getAttribute('data-rm-tab');
                $$('[data-rm-tab]').forEach(function (x) { var on = x === b; x.classList.toggle('on', on); x.setAttribute('aria-selected', on ? 'true' : 'false'); });
                $$('[data-rm-panel]').forEach(function (p) { p.hidden = p.getAttribute('data-rm-panel') !== tab; });
            });
        });

        // ---------- keyword uniqueness + link suggestions
        var checkKeyword = function () {
            var kw = val(cfg.keyword).trim();
            state.duplicate = kw ? null : [];
            render();
            var ul = $('[data-rm-links]', panel);
            if (!kw) { ul.innerHTML = '<li class="st-empty-sm">Set a focus keyword to get suggestions.</li>'; return; }
            fetch(cfg.urls.keyword + '?kw=' + encodeURIComponent(kw) + '&kind=' + cfg.kind + '&pk=' + (cfg.pk || ''), { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (r) { return r.json(); }).then(function (d) { state.duplicate = d.used_by; render(); }).catch(function () { state.duplicate = []; render(); });
            fetch(cfg.urls.links + '?q=' + encodeURIComponent(kw + ' ' + val(cfg.title)) + '&kind=' + cfg.kind + '&pk=' + (cfg.pk || ''), { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (r) { return r.json(); }).then(function (d) {
                    ul.innerHTML = d.results.length ? d.results.map(function (x) { return '<li><span><b>' + esc(x.title) + '</b><small>' + esc(x.kind) + ' &middot; ' + esc(x.url) + '</small></span><button type="button" class="st-btn st-btn-sm" data-copy-link="' + esc(x.url) + '">Copy link</button></li>'; }).join('') : '<li class="st-empty-sm">No related pages found yet.</li>';
                }).catch(function () { ul.innerHTML = '<li class="st-empty-sm">Suggestions are unavailable right now.</li>'; });
        };
        panel.addEventListener('click', function (e) {
            var b = e.target.closest('[data-copy-link]'); if (!b) { return; }
            var url = location.protocol + '//' + cfg.host + b.getAttribute('data-copy-link');
            var done = function () { var o = b.textContent; b.textContent = 'Copied'; setTimeout(function () { b.textContent = o; }, 1300); };
            if (navigator.clipboard) { navigator.clipboard.writeText(url).then(done, done); } else { done(); }
        });

        // ---------- wire up
        var form = document.getElementById('st-editor');
        var schedule = function () { clearTimeout(timer); timer = setTimeout(function () { render(); renderSerp(); renderSocial(); }, 250); };
        form.addEventListener('input', schedule);
        form.addEventListener('change', schedule);
        var kwField = el(cfg.keyword);
        if (kwField) { kwField.addEventListener('input', function () { clearTimeout(kwTimer); kwTimer = setTimeout(checkKeyword, 600); }); }
        state.duplicate = null;
        render(); renderSerp(); renderSocial(); checkKeyword();
        setTimeout(schedule, 800); // pick up the rich editor once it has initialised
    }

    return { analyze: analyze, parse: parse, mount: mount };
});
