/* Rizen Studio: interactivity (vanilla JS, no dependencies) */
(function () {
    'use strict';
    var $ = function (s, r) { return (r || document).querySelector(s); };
    var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
    var el = function (tag, cls, html) { var n = document.createElement(tag); if (cls) { n.className = cls; } if (html != null) { n.innerHTML = html; } return n; };
    var esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var csrf = function () { var i = $('input[name=csrfmiddlewaretoken]'); return i ? i.value : ''; };

    /* ---------- theme ---------- */
    $$('[data-theme-toggle]').forEach(function (b) {
        b.addEventListener('click', function () {
            var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            try { localStorage.setItem('studio-theme', next); } catch (e) { /* ignore */ }
        });
    });

    /* ---------- sidebar (mobile) ---------- */
    $$('[data-toggle-side]').forEach(function (b) { b.addEventListener('click', function () { document.body.classList.toggle('side-open'); }); });
    $$('[data-close-side]').forEach(function (b) { b.addEventListener('click', function () { document.body.classList.remove('side-open'); }); });

    /* ---------- dropdown ---------- */
    $$('[data-dd]').forEach(function (dd) {
        var t = $('[data-dd-toggle]', dd);
        t.addEventListener('click', function (e) { e.stopPropagation(); var o = dd.classList.toggle('open'); t.setAttribute('aria-expanded', o ? 'true' : 'false'); });
    });
    document.addEventListener('click', function () { $$('[data-dd].open').forEach(function (d) { d.classList.remove('open'); }); });

    /* ---------- toasts ---------- */
    $$('[data-toast]').forEach(function (t) {
        $('[data-close-toast]', t).addEventListener('click', function () { t.remove(); });
        if (t.className.indexOf('success') > -1) { setTimeout(function () { t.style.transition = 'opacity .4s'; t.style.opacity = '0'; setTimeout(function () { t.remove(); }, 450); }, 5000); }
    });

    /* ---------- confirm dialog ---------- */
    var confirmDlg = $('#st-confirm');
    document.addEventListener('click', function (e) {
        var b = e.target.closest('[data-confirm]');
        if (!b || !confirmDlg || !confirmDlg.showModal) { return; }
        e.preventDefault();
        $('#st-confirm-text').textContent = b.getAttribute('data-confirm');
        $('#st-confirm-ok').textContent = b.getAttribute('data-confirm-ok') || 'Confirm';
        confirmDlg.returnValue = '';
        confirmDlg.showModal();
        confirmDlg.addEventListener('close', function once() {
            confirmDlg.removeEventListener('close', once);
            if (confirmDlg.returnValue === 'ok') {
                var form = b.form || b.closest('form');
                if (form) { if (form.requestSubmit) { form.requestSubmit(b); } else { form.submit(); } }
            }
        });
    });

    /* small text prompt dialog (used for links / image URLs) */
    function ask(title, placeholder, cb, value) {
        var dlg = el('dialog', 'st-confirm');
        dlg.innerHTML = '<form method="dialog"><h2>' + esc(title) + '</h2><p></p><input class="st-input" type="text" placeholder="' + esc(placeholder) + '" value="' + esc(value || '') + '"><div class="st-confirm-actions" style="margin-top:18px"><button value="cancel" class="st-btn">Cancel</button><button value="ok" class="st-btn st-btn-primary">Insert</button></div></form>';
        document.body.appendChild(dlg);
        dlg.addEventListener('close', function () { var v = $('input', dlg).value.trim(); var ok = dlg.returnValue === 'ok'; dlg.remove(); if (ok && v) { cb(v); } });
        dlg.showModal();
        $('input', dlg).focus();
    }

    /* ---------- command palette ---------- */
    var pal = $('#st-palette'), palQ = $('#st-palette-q'), palList = $('#st-palette-list'), palTimer, palSel = -1;
    function openPalette() { if (pal && pal.showModal && !pal.open) { pal.showModal(); palQ.value = ''; palQ.focus(); } }
    $$('[data-open-palette]').forEach(function (b) { b.addEventListener('click', openPalette); });
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPalette(); }
        else if (e.key === '/' && !/input|textarea|select/i.test((document.activeElement || {}).tagName || '') && !(document.activeElement && document.activeElement.isContentEditable)) { e.preventDefault(); openPalette(); }
        else if (e.key === 'Escape') { document.body.classList.remove('side-open'); }
    });
    if (pal) {
        pal.addEventListener('click', function (e) { if (e.target === pal) { pal.close(); } });
        palQ.addEventListener('input', function () {
            clearTimeout(palTimer);
            palTimer = setTimeout(function () {
                var q = palQ.value.trim();
                if (q.length < 2) { palList.innerHTML = '<p class="st-palette-hint">Type at least two letters. Try a page name, a city or a client.</p>'; return; }
                fetch(palQ.getAttribute('data-api') + '?q=' + encodeURIComponent(q), { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
                    .then(function (r) { return r.json(); })
                    .then(function (d) {
                        var last = '', html = '';
                        d.results.forEach(function (r) {
                            if (r.group !== last) { html += '<div class="st-pal-group">' + esc(r.group) + '</div>'; last = r.group; }
                            html += '<a class="st-pal-item" href="' + esc(r.url) + '"><b>' + esc(r.title) + '</b><small>' + esc(r.sub || '') + '</small></a>';
                        });
                        palList.innerHTML = html || '<p class="st-palette-hint">No matches for &ldquo;' + esc(q) + '&rdquo;.</p>';
                        palSel = -1;
                    }).catch(function () { palList.innerHTML = '<p class="st-palette-hint">Search is unavailable right now.</p>'; });
            }, 180);
        });
        palQ.addEventListener('keydown', function (e) {
            var items = $$('.st-pal-item', palList);
            if (!items.length) { return; }
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                palSel = (palSel + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
                items.forEach(function (i, n) { i.classList.toggle('sel', n === palSel); });
                items[palSel].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'Enter' && palSel > -1) { e.preventDefault(); location.href = items[palSel].href; }
        });
    }

    /* ---------- animated stat numbers ---------- */
    $$('[data-count]').forEach(function (n) {
        var end = parseInt(n.getAttribute('data-count'), 10) || 0;
        if (reduce || end < 2) { return; }
        var start = null;
        n.textContent = '0';
        requestAnimationFrame(function tick(ts) {
            if (start === null) { start = ts; }
            var p = Math.min((ts - start) / 800, 1);
            n.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
            if (p < 1) { requestAnimationFrame(tick); }
        });
    });

    /* ---------- list: bulk selection ---------- */
    var bulkForm = $('#st-bulk-form');
    if (bulkForm) {
        var checks = $$('[data-row-check]', bulkForm), all = $('[data-check-all]', bulkForm), bar = $('[data-bulkbar]', bulkForm), cnt = $('[data-bulk-count]', bulkForm);
        var refresh = function () {
            var n = checks.filter(function (c) { return c.checked; }).length;
            if (bar) { bar.hidden = n === 0; }
            if (cnt) { cnt.textContent = n; }
            if (all) { all.checked = n > 0 && n === checks.length; all.indeterminate = n > 0 && n < checks.length; }
        };
        checks.forEach(function (c) { c.addEventListener('change', refresh); });
        if (all) { all.addEventListener('change', function () { checks.forEach(function (c) { c.checked = all.checked; }); refresh(); }); }
    }

    /* ---------- editor ---------- */
    var editor = $('#st-editor');
    var dirty = false;
    function markDirty() {
        if (dirty) { return; }
        dirty = true;
        var sb = $('[data-savebar]'); if (sb) { sb.classList.add('dirty'); var n = $('[data-dirty-note]', sb); if (n) { n.textContent = 'You have unsaved changes'; } }
    }
    if (editor) {
        editor.addEventListener('input', markDirty);
        editor.addEventListener('change', markDirty);
        editor.addEventListener('submit', function () { dirty = false; });
        window.addEventListener('beforeunload', function (e) { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
    }

    // character counters
    $$('[data-counter-for]').forEach(function (c) {
        var f = document.getElementById(c.getAttribute('data-counter-for')), max = parseInt(c.getAttribute('data-max'), 10);
        if (!f) { return; }
        var upd = function () {
            var n = f.value.length; c.textContent = n + ' / ' + max;
            c.className = 'st-counter' + (n === 0 ? '' : n > max ? ' over' : n > max * 0.92 ? ' warn' : n >= max * 0.5 ? ' good' : '');
        };
        f.addEventListener('input', upd); upd();
    });

    // Google preview
    var serp = $('[data-serp]');
    if (serp) {
        var val = function (name) { var f = name && document.getElementById('id_' + name); return f ? f.value.trim() : ''; };
        var t = serp.getAttribute('data-title'), d = serp.getAttribute('data-desc'), s = serp.getAttribute('data-slug'), fb = serp.getAttribute('data-fallback');
        var pre = editor ? (editor.getAttribute('data-serp-prefix') || '') : '';
        var setMeter = function (sel, n, min, max) {
            var m = $(sel, serp); if (!m) { return; }
            m.style.setProperty('--w', Math.min(100, Math.round(n / max * 100)) + '%');
            m.className = n > max ? 'over' : (n < min && n > 0) ? 'warn' : '';
        };
        var render = function () {
            var title = val(t) || val(fb) || 'Your page title';
            var desc = val(d) || 'Add a meta description so searchers know what this page offers.';
            $('[data-serp-title]', serp).textContent = title;
            $('[data-serp-desc]', serp).textContent = desc;
            $('[data-serp-url]', serp).textContent = pre + (val(s) || '') + (val(s) === 'home' ? '' : '/');
            setMeter('[data-meter-title]', val(t).length || val(fb).length, 30, 60);
            setMeter('[data-meter-desc]', val(d).length, 70, 160);
        };
        [t, d, s, fb].forEach(function (n) { var f = n && document.getElementById('id_' + n); if (f) { f.addEventListener('input', render); } });
        render();
    }

    // auto-slug from title on new items
    if (editor) {
        var slugF = $('#id_slug') || $('#id_page_tag');
        var srcF = $('#id_title') || $('#id_page_name') || $('#id_client_name') || $('#id_city');
        if (slugF && srcF && !slugF.value) {
            var touched = false, auto = false;
            slugF.addEventListener('input', function () { if (!auto) { touched = true; } });
            srcF.addEventListener('input', function () {
                if (touched) { return; }
                slugF.value = srcF.value.toLowerCase().normalize('NFKD').replace(/[^\w\s-]/g, '').trim().replace(/[\s_]+/g, '-').replace(/-+/g, '-');
                auto = true; slugF.dispatchEvent(new Event('input', { bubbles: true })); auto = false;
            });
        }
    }

    // image dropzones: preview + drag highlight
    $$('[data-drop]').forEach(function (z) {
        var inp = $('input[type=file]', z), prev = $('.st-drop-preview', z);
        ['dragenter', 'dragover'].forEach(function (ev) { z.addEventListener(ev, function () { z.classList.add('drag'); }); });
        ['dragleave', 'drop'].forEach(function (ev) { z.addEventListener(ev, function () { z.classList.remove('drag'); }); });
        inp.addEventListener('change', function () {
            if (prev && inp.files && inp.files[0] && inp.files[0].type.indexOf('image/') === 0) { prev.src = URL.createObjectURL(inp.files[0]); prev.hidden = false; }
            if (inp.hasAttribute('data-auto-submit') && inp.files.length) { inp.form.submit(); }
        });
    });

    // FAQ builder
    var faqList = $('[data-faq-list]');
    if (faqList) {
        var total = $('#id_faqs-TOTAL_FORMS'), tpl = $('#st-faq-template');
        $('[data-add-faq]').addEventListener('click', function () {
            var n = parseInt(total.value, 10);
            var node = tpl.innerHTML.replace(/__prefix__/g, n);
            var wrap = el('div'); wrap.innerHTML = node;
            faqList.appendChild(wrap.firstElementChild);
            total.value = n + 1;
            var q = $('input[type=text]', faqList.lastElementChild); if (q) { q.focus(); }
            markDirty();
        });
        faqList.addEventListener('click', function (e) {
            var b = e.target.closest('[data-remove-faq]');
            if (b) { var card = b.closest('[data-faq]'); card.querySelectorAll('input,textarea').forEach(function (i) { i.value = ''; }); card.classList.add('removed'); markDirty(); }
        });
        faqList.addEventListener('change', function (e) {
            if (e.target.type === 'checkbox' && /-DELETE$/.test(e.target.name)) { e.target.closest('[data-faq]').classList.toggle('removed', e.target.checked); }
        });
    }

    /* ---------- rich text editor ---------- */
    function pickImage(cb) {
        var api = (window.STUDIO || {}).mediaApi;
        var dlg = el('dialog', 'st-palette');
        dlg.innerHTML = '<div class="st-palette-box"><div class="st-palette-input"><b>Insert image</b><span style="flex:1"></span><button class="st-btn st-btn-sm" type="button" data-url>Use a URL</button><kbd>Esc</kbd></div><div class="st-pick-grid"><p class="st-palette-hint">Loading&hellip;</p></div></div>';
        document.body.appendChild(dlg);
        dlg.addEventListener('close', function () { dlg.remove(); });
        dlg.addEventListener('click', function (e) { if (e.target === dlg) { dlg.close(); } });
        $('[data-url]', dlg).addEventListener('click', function () { dlg.close(); ask('Image address', 'https://…', cb); });
        dlg.showModal();
        var grid = $('.st-pick-grid', dlg);
        fetch(api, { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (d) {
            grid.innerHTML = '';
            if (!d.items.length) { grid.innerHTML = '<p class="st-palette-hint">No images yet. Upload some in the Media library first.</p>'; return; }
            d.items.forEach(function (i) {
                var b = el('button', '', '<img alt="' + esc(i.name) + '" src="' + esc(i.url) + '" loading="lazy">'); b.type = 'button';
                b.addEventListener('click', function () { dlg.close(); cb(i.url); });
                grid.appendChild(b);
            });
        }).catch(function () { grid.innerHTML = '<p class="st-palette-hint">Could not load the library.</p>'; });
    }

    function makeRich(ta) {
        var startRaw = !!(window.STUDIO && window.STUDIO.rawHtml);
        var wrap = el('div', 'st-rich'), bar = el('div', 'st-rich-bar'), area = el('div', 'st-rich-area'), foot = el('div', 'st-rich-foot', '<span data-words>0 words</span><span data-mode>Visual</span>');
        area.contentEditable = 'true'; area.setAttribute('role', 'textbox'); area.setAttribute('aria-multiline', 'true'); area.setAttribute('aria-label', 'Content editor');
        ta.parentNode.insertBefore(wrap, ta); wrap.appendChild(bar); wrap.appendChild(area); wrap.appendChild(ta); wrap.appendChild(foot);
        ta.classList.add('st-raw', 'st-mono');
        var raw = startRaw;
        var words = function () { var t = (raw ? ta.value.replace(/<[^>]+>/g, ' ') : area.innerText) || ''; var n = (t.match(/\S+/g) || []).length; $('[data-words]', foot).textContent = n + ' word' + (n === 1 ? '' : 's'); };
        var toArea = function () { area.innerHTML = ta.value; };
        // Tidy the browser's editing output: semantic tags, no inline styles or empty wrappers.
        var clean = function (html) {
            var box = el('div'); box.innerHTML = html;
            $$('[style]', box).forEach(function (n) { n.removeAttribute('style'); });
            $$('span', box).forEach(function (n) { if (!n.attributes.length) { while (n.firstChild) { n.parentNode.insertBefore(n.firstChild, n); } n.remove(); } });
            $$('b', box).forEach(function (n) { var s = el('strong'); s.innerHTML = n.innerHTML; n.replaceWith(s); });
            $$('i', box).forEach(function (n) { var s = el('em'); s.innerHTML = n.innerHTML; n.replaceWith(s); });
            $$('div', box).forEach(function (n) { if (!n.attributes.length) { var p = el('p'); p.innerHTML = n.innerHTML; n.replaceWith(p); } });
            return box.innerHTML;
        };
        var toTa = function () { ta.value = clean(area.innerHTML); };
        var setMode = function (r) {
            if (r === raw) { return; }
            if (r) { toTa(); } else { toArea(); }
            raw = r; area.hidden = r; ta.hidden = !r; $('[data-mode]', foot).textContent = r ? 'HTML' : 'Visual';
            var hb = $('[data-cmd="html"]', bar); if (hb) { hb.classList.toggle('on', r); }
            words();
        };
        toArea(); area.hidden = startRaw; ta.hidden = !startRaw; if (startRaw) { $('[data-mode]', foot).textContent = 'HTML'; }
        var cmds = [
            ['B', 'bold', 'Bold'], ['I', 'italic', 'Italic'], ['U', 'underline', 'Underline'], '|',
            ['H2', 'h2', 'Heading 2'], ['H3', 'h3', 'Heading 3'], ['P', 'p', 'Paragraph'], '|',
            ['&bull; List', 'ul', 'Bulleted list'], ['1. List', 'ol', 'Numbered list'], ['Quote', 'quote', 'Quote'], '|',
            ['Link', 'link', 'Add link'], ['Unlink', 'unlink', 'Remove link'], ['Image', 'image', 'Insert image'], ['&mdash;', 'hr', 'Divider'], '|',
            ['Clear', 'clear', 'Clear formatting'], ['&#8630;', 'undo', 'Undo'], ['&#8631;', 'redo', 'Redo'], '|',
            ['&lt;/&gt; HTML', 'html', 'Edit HTML'], ['&#x26F6;', 'full', 'Full screen']
        ];
        var run = function (c) {
            if (c === 'html') { setMode(!raw); return; }
            if (c === 'full') { wrap.classList.toggle('full'); return; }
            if (raw) { return; }
            area.focus();
            var ex = function (a, v) { document.execCommand(a, false, v); };
            switch (c) {
                case 'bold': case 'italic': case 'underline': ex(c); break;
                case 'h2': ex('formatBlock', '<h2>'); break; case 'h3': ex('formatBlock', '<h3>'); break; case 'p': ex('formatBlock', '<p>'); break;
                case 'quote': ex('formatBlock', '<blockquote>'); break;
                case 'ul': ex('insertUnorderedList'); break; case 'ol': ex('insertOrderedList'); break;
                case 'hr': ex('insertHorizontalRule'); break; case 'unlink': ex('unlink'); break;
                case 'clear': ex('removeFormat'); ex('formatBlock', '<p>'); break;
                case 'undo': ex('undo'); break; case 'redo': ex('redo'); break;
                case 'link': var sel = window.getSelection(), rng = sel.rangeCount ? sel.getRangeAt(0).cloneRange() : null;
                    ask('Link address', 'https://…', function (u) { area.focus(); if (rng) { sel.removeAllRanges(); sel.addRange(rng); } ex('createLink', u); toTa(); });
                    break;
                case 'image': var sel2 = window.getSelection(), rng2 = sel2.rangeCount ? sel2.getRangeAt(0).cloneRange() : null;
                    pickImage(function (u) { area.focus(); if (rng2) { sel2.removeAllRanges(); sel2.addRange(rng2); } ex('insertImage', u); toTa(); });
                    break;
            }
            toTa(); words(); markDirty();
        };
        cmds.forEach(function (c) {
            if (c === '|') { bar.appendChild(el('span', 'sep')); return; }
            var b = el('button', '', c[0]); b.type = 'button'; b.title = c[2]; b.setAttribute('aria-label', c[2]); b.setAttribute('data-cmd', c[1]);
            if (c[1] === 'html' && startRaw) { b.classList.add('on'); }
            b.addEventListener('mousedown', function (e) { e.preventDefault(); });
            b.addEventListener('click', function () { run(c[1]); });
            bar.appendChild(b);
        });
        area.addEventListener('input', function () { toTa(); words(); markDirty(); });
        area.addEventListener('paste', function (e) {   // paste as plain text with basic structure
            var html = (e.clipboardData || window.clipboardData).getData('text/html');
            if (html) { e.preventDefault(); var tmp = el('div'); tmp.innerHTML = html; $$('script,style,meta,link', tmp).forEach(function (n) { n.remove(); }); $$('*', tmp).forEach(function (n) { n.removeAttribute('style'); n.removeAttribute('class'); n.removeAttribute('id'); Array.prototype.slice.call(n.attributes).forEach(function (a) { if (/^on/i.test(a.name)) { n.removeAttribute(a.name); } }); }); document.execCommand('insertHTML', false, tmp.innerHTML); }
        });
        ta.addEventListener('input', function () { words(); });
        if (editor) { editor.addEventListener('submit', function () { if (!raw) { toTa(); } }); }
        words();
    }
    $$('textarea[data-editor="rich"]').forEach(makeRich);

    /* ---------- bulk tools ---------- */
    $$('[data-mode-tab]').forEach(function (r) {
        r.addEventListener('change', function () {
            $$('[data-mode-tab]').forEach(function (x) { x.closest('.st-tab').classList.toggle('on', x.checked); });
            $$('[data-mode-panel]').forEach(function (p) { p.hidden = p.getAttribute('data-mode-panel') !== r.value; });
        });
    });
    var csvFile = $('[data-csv-file]');
    if (csvFile) {
        csvFile.addEventListener('change', function () {
            var f = csvFile.files[0]; if (!f) { return; }
            var rd = new FileReader();
            rd.onload = function () { $('[data-csv-target]').value = String(rd.result).replace(/^﻿/, ''); };
            rd.readAsText(f);
        });
    }
    $$('[data-fill-sample]').forEach(function (b) { b.addEventListener('click', function () { $('[data-csv-target]').value = b.getAttribute('data-fill-sample'); }); });
    var selAll = $('[data-select-all-services]');
    if (selAll) { selAll.addEventListener('click', function () { var boxes = $$('input[name=services]'); var on = boxes.some(function (b) { return !b.checked; }); boxes.forEach(function (b) { b.checked = on; }); selAll.textContent = on ? 'Clear all' : 'Select all'; }); }

    /* ---------- media ---------- */
    $$('[data-copy]').forEach(function (b) {
        b.addEventListener('click', function () {
            var url = location.origin + b.getAttribute('data-copy');
            var done = function () { var o = b.innerHTML; b.textContent = 'Copied'; setTimeout(function () { b.innerHTML = o; }, 1400); };
            if (navigator.clipboard) { navigator.clipboard.writeText(url).then(done, done); } else { done(); }
        });
    });
})();
