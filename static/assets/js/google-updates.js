/* Google Updates: interactive timeline, finder, readiness checklist, tabs. Vanilla JS, no dependencies. */
(function () {
    'use strict';

    var $ = function (s, r) { return (r || document).querySelector(s); };
    var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    var typesData = {};
    try { typesData = JSON.parse(($('#gu-types') || {}).textContent || '{}'); } catch (e) { typesData = {}; }

    /* ---------- generic tab widget (core-update steps + home teaser) ---------- */
    function initTabs(root, tabSel, panelSel) {
        var tabs = $$(tabSel, root), panels = $$(panelSel, root);
        if (!tabs.length) { return; }
        function select(i, focus) {
            tabs.forEach(function (t, j) {
                var on = i === j;
                t.setAttribute('aria-selected', on ? 'true' : 'false');
                t.tabIndex = on ? 0 : -1;
                if (panels[j]) { panels[j].hidden = !on; }
            });
            if (focus) { tabs[i].focus(); }
        }
        tabs.forEach(function (t, i) {
            t.addEventListener('click', function () { select(i); });
            t.addEventListener('keydown', function (e) {
                var n = tabs.length, k = e.key;
                if (k === 'ArrowRight' || k === 'ArrowDown') { e.preventDefault(); select((i + 1) % n, true); }
                else if (k === 'ArrowLeft' || k === 'ArrowUp') { e.preventDefault(); select((i - 1 + n) % n, true); }
                else if (k === 'Home') { e.preventDefault(); select(0, true); }
                else if (k === 'End') { e.preventDefault(); select(n - 1, true); }
            });
        });
        $$('[data-step-next]', root).forEach(function (b, i) {
            b.addEventListener('click', function () { select(Math.min(i + 1, tabs.length - 1), true); });
        });
    }
    var steps = $('#gu-steps');
    if (steps) { initTabs(steps, '[role="tab"]', '[role="tabpanel"]'); }
    $$('[data-gu-tabs]').forEach(function (root) { initTabs(root, '[role="tab"]', '[role="tabpanel"]'); });

    /* ---------- animated counters ---------- */
    var counters = $$('[data-count]');
    if (counters.length && 'IntersectionObserver' in window && !reduceMotion) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                if (!en.isIntersecting) { return; }
                io.unobserve(en.target);
                var el = en.target, end = parseInt(el.getAttribute('data-count'), 10) || 0, start = null;
                function tick(ts) {
                    if (start === null) { start = ts; }
                    var p = Math.min((ts - start) / 900, 1);
                    el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
                    if (p < 1) { requestAnimationFrame(tick); }
                }
                requestAnimationFrame(tick);
            });
        }, { threshold: 0.4 });
        counters.forEach(function (c) { io.observe(c); });
    }

    /* ---------- timeline ---------- */
    var list = $('#gu-list');
    if (list) {
        var items = $$('.gu-item', list);
        var searchInput = $('#gu-search'), chips = $$('#gu-chips .gu-chip'), yearBtns = $$('#gu-years .gu-year');
        var countEl = $('#gu-count'), sortBtn = $('#gu-sort'), expandBtn = $('#gu-expand'), resetBtn = $('#gu-reset'), emptyEl = $('#gu-empty');
        var state = { types: {}, year: null, q: '', order: 'desc' };
        var text = new Map();
        items.forEach(function (li) { text.set(li, li.textContent.toLowerCase().replace(/\s+/g, ' ')); });

        function fillTodo(li) {
            var ul = $('.gu-todo', li);
            if (!ul || ul.children.length) { return; }
            var d = typesData[ul.getAttribute('data-todo')];
            if (!d) { return; }
            d.todo.forEach(function (t) { var x = document.createElement('li'); x.textContent = t; ul.appendChild(x); });
        }
        function setOpen(li, open) {
            var head = $('.gu-head', li), panel = $('.gu-panel', li);
            if (open) { fillTodo(li); }
            head.setAttribute('aria-expanded', open ? 'true' : 'false');
            panel.hidden = !open;
            li.classList.toggle('is-open', open);
        }
        function visibleItems() { return items.filter(function (li) { return !li.hidden; }); }

        function syncUrl() {
            var p = new URLSearchParams();
            var t = Object.keys(state.types).filter(function (k) { return state.types[k]; });
            if (t.length) { p.set('type', t.join(',')); }
            if (state.year) { p.set('year', state.year); }
            if (state.q) { p.set('q', state.q); }
            if (state.order === 'asc') { p.set('sort', 'asc'); }
            var qs = p.toString();
            try { history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash); } catch (e) { /* ignore */ }
        }

        function apply() {
            var active = Object.keys(state.types).filter(function (k) { return state.types[k]; });
            var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
            var shown = 0;
            items.forEach(function (li) {
                var ok = (!active.length || active.indexOf(li.getAttribute('data-type')) > -1) &&
                    (!state.year || li.getAttribute('data-year') === String(state.year));
                if (ok && terms.length) {
                    var hay = text.get(li);
                    ok = terms.every(function (w) { return hay.indexOf(w) > -1; });
                }
                li.hidden = !ok;
                if (ok) { shown++; }
            });
            var sorted = items.slice().sort(function (a, b) {
                var d = a.getAttribute('data-ts') < b.getAttribute('data-ts') ? -1 : 1;
                return state.order === 'asc' ? d : -d;
            });
            sorted.forEach(function (li) { list.appendChild(li); });

            chips.forEach(function (c) { c.setAttribute('aria-pressed', state.types[c.getAttribute('data-type')] ? 'true' : 'false'); });
            yearBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(state.year) === b.getAttribute('data-year') ? 'true' : 'false'); });
            var filtered = active.length || state.year || state.q;
            countEl.textContent = filtered ? 'Showing ' + shown + ' of ' + items.length + ' updates' : 'Showing all ' + items.length + ' updates';
            resetBtn.hidden = !filtered;
            emptyEl.hidden = shown !== 0;
            list.hidden = shown === 0;
            sortBtn.textContent = state.order === 'desc' ? 'Newest first' : 'Oldest first';
            sortBtn.setAttribute('data-order', state.order);
            var vis = visibleItems();
            expandBtn.textContent = vis.length && vis.every(function (li) { return li.classList.contains('is-open'); }) ? 'Collapse all' : 'Expand all';
            syncUrl();
        }

        function clearFilters() { state.types = {}; state.year = null; state.q = ''; searchInput.value = ''; apply(); }

        chips.forEach(function (c) {
            c.addEventListener('click', function () {
                var k = c.getAttribute('data-type');
                state.types[k] = !state.types[k];
                apply();
            });
        });
        yearBtns.forEach(function (b) {
            b.addEventListener('click', function () {
                var y = b.getAttribute('data-year');
                state.year = String(state.year) === y ? null : y;
                apply();
            });
        });
        var t;
        searchInput.addEventListener('input', function () {
            clearTimeout(t);
            t = setTimeout(function () { state.q = searchInput.value.trim(); apply(); }, 120);
        });
        sortBtn.addEventListener('click', function () { state.order = state.order === 'desc' ? 'asc' : 'desc'; apply(); });
        expandBtn.addEventListener('click', function () {
            var vis = visibleItems();
            var allOpen = vis.length && vis.every(function (li) { return li.classList.contains('is-open'); });
            vis.forEach(function (li) { setOpen(li, !allOpen); });
            apply();
        });
        resetBtn.addEventListener('click', clearFilters);
        $$('[data-gu-clear]').forEach(function (b) { b.addEventListener('click', clearFilters); });

        items.forEach(function (li) {
            $('.gu-head', li).addEventListener('click', function () {
                setOpen(li, !li.classList.contains('is-open'));
                apply();
            });
        });
        $$('.gu-copy', list).forEach(function (b) {
            b.addEventListener('click', function () {
                var url = location.origin + location.pathname + '#' + b.getAttribute('data-slug');
                var done = function () { var old = b.textContent; b.textContent = 'Link copied'; setTimeout(function () { b.textContent = old; }, 1600); };
                if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(url).then(done, done); }
                else { var ta = document.createElement('textarea'); ta.value = url; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) { /* ignore */ } document.body.removeChild(ta); done(); }
            });
        });

        function openFromHash() {
            var id = decodeURIComponent((location.hash || '').slice(1));
            var li = id && document.getElementById(id);
            if (!li || !li.classList || !li.classList.contains('gu-item')) { return; }
            if (li.hidden) { clearFilters(); }
            setOpen(li, true);
            apply();
            li.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
            li.classList.add('is-flash');
            setTimeout(function () { li.classList.remove('is-flash'); }, 1700);
        }

        // read initial state from the URL
        var params = new URLSearchParams(location.search);
        (params.get('type') || '').split(',').filter(Boolean).forEach(function (k) { state.types[k] = true; });
        if (params.get('year')) { state.year = params.get('year'); }
        if (params.get('q')) { state.q = params.get('q'); searchInput.value = state.q; }
        if (params.get('sort') === 'asc') { state.order = 'asc'; }
        apply();
        openFromHash();
        window.addEventListener('hashchange', openFromHash);

        window.guShowType = function (type) {
            state.types = {}; state.types[type] = true; state.year = null; state.q = ''; searchInput.value = '';
            apply();
            var tl = $('#gu-timeline');
            if (tl) { tl.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' }); }
        };
    }

    /* ---------- update finder ---------- */
    var qs = $('#gu-questions'), out = $('#gu-finder-out');
    if (qs && out) {
        var boxes = $$('input[type="checkbox"]', qs);
        var latestByType = function (type) {
            return $$('.gu-item[data-type="' + type + '"]').sort(function (a, b) {
                return a.getAttribute('data-ts') < b.getAttribute('data-ts') ? 1 : -1;
            }).slice(0, 3);
        };
        var el = function (tag, cls, txt) { var n = document.createElement(tag); if (cls) { n.className = cls; } if (txt) { n.textContent = txt; } return n; };
        var renderFinder = function () {
            var score = {};
            boxes.forEach(function (b) {
                if (!b.checked) { return; }
                b.getAttribute('data-types').split(' ').forEach(function (t) { score[t] = (score[t] || 0) + 1; });
            });
            var keys = Object.keys(score).sort(function (a, b) { return score[b] - score[a]; });
            out.textContent = '';
            if (!keys.length) { out.appendChild(el('p', 'gu-out-empty', 'Your personalised results will appear here as you tick the boxes.')); return; }
            out.appendChild(el('h3', '', 'Update families to watch'));
            out.appendChild(el('p', '', 'Ordered by how closely each matches what you selected.'));
            keys.forEach(function (k) {
                var d = typesData[k]; if (!d) { return; }
                var box = el('div', 'gu-res gu-t-' + k);
                box.appendChild(el('h4', '', d.label));
                box.appendChild(el('p', '', d.blurb));
                var ul = el('ul');
                latestByType(k).forEach(function (li) {
                    var x = el('li'), a = el('a', '', $('.gu-title', li).textContent + ' (' + $('.gu-date', li).textContent + ')');
                    a.href = '#' + li.id; x.appendChild(a); ul.appendChild(x);
                });
                box.appendChild(ul);
                var btn = el('button', '', 'See all ' + d.label.toLowerCase() + ' updates →');
                btn.type = 'button';
                btn.addEventListener('click', function () { if (window.guShowType) { window.guShowType(k); } });
                box.appendChild(btn);
                out.appendChild(box);
            });
        };
        boxes.forEach(function (b) { b.addEventListener('change', renderFinder); });
    }

    /* ---------- readiness checklist ---------- */
    var checkRoot = $('#gu-check');
    if (checkRoot) {
        var KEY = 'gu-readiness-v1';
        var checks = $$('input[data-check]', checkRoot);
        var ringFg = $('#gu-ring-fg'), ring = $('#gu-ring'), num = $('#gu-score-num'), label = $('#gu-score-label'), msg = $('#gu-score-msg');
        var next = $('#gu-next'), nextList = $('#gu-next-list');
        var saved = {};
        try { saved = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { saved = {}; }
        checks.forEach(function (c) { c.checked = !!saved[c.getAttribute('data-check')]; });

        var bands = [
            [90, 'Update-ready', 'Excellent. Keep monitoring Search Console through each rollout and keep improving.', '#0e7a5f'],
            [75, 'Strong', 'You match most of what recent updates reward. Close the remaining gaps below.', '#0e7a5f'],
            [50, 'On track', 'A solid base, with clear gains available. Start with the fixes listed below.', '#b25e00'],
            [25, 'Needs work', 'Several risk areas. Prioritise the fixes below before the next core update.', '#c0362a'],
            [0, 'Getting started', 'Lots of room to improve, which also means lots of upside.', '#c0362a']
        ];
        var updateScore = function () {
            var total = checks.length, on = checks.filter(function (c) { return c.checked; }).length;
            var pct = Math.round(on / total * 100);
            var band = bands.filter(function (b) { return pct >= b[0]; })[0];
            if (!on) { band = [0, 'Not started', 'Tick the boxes that are true for your site to see your score.', '#4356d6']; }
            num.textContent = pct;
            ring.style.setProperty('--p', pct);
            ringFg.style.stroke = band[3];
            label.textContent = band[1];
            msg.textContent = band[2];
            $$('[data-pillar]', checkRoot).forEach(function (fs) {
                var cs = $$('input[data-check]', fs), n = cs.filter(function (c) { return c.checked; }).length;
                $('[data-pillar-score]', fs).textContent = n + '/' + cs.length;
            });
            var todo = checks.filter(function (c) { return !c.checked; }).slice(0, 3);
            nextList.textContent = '';
            todo.forEach(function (c) {
                var li = document.createElement('li');
                li.textContent = c.parentNode.querySelector('.gu-check-text').firstChild.textContent;
                nextList.appendChild(li);
            });
            next.hidden = !on || !todo.length;
        };
        checks.forEach(function (c) {
            c.addEventListener('change', function () {
                saved[c.getAttribute('data-check')] = c.checked;
                try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (e) { /* ignore */ }
                updateScore();
            });
        });
        $('#gu-check-reset').addEventListener('click', function () {
            checks.forEach(function (c) { c.checked = false; });
            saved = {};
            try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
            updateScore();
        });
        updateScore();
    }
})();
