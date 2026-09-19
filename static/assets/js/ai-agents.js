/* AI Agents showcase: agent picker, sample-run terminal, avatar tilt. Vanilla JS. */
(function () {
    'use strict';

    var apps = document.querySelectorAll('[data-aa]');
    if (!apps.length) { return; }
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var fine = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    Array.prototype.forEach.call(apps, function (app) {
        var tabs = Array.prototype.slice.call(app.querySelectorAll('.aa-pick'));
        var panels = Array.prototype.slice.call(app.querySelectorAll('.aa-panel'));
        var timers = [];

        function stopTyping() { timers.forEach(clearTimeout); timers = []; }

        // Reveal the terminal lines one by one, typing each character.
        function run(panel) {
            stopTyping();
            var lis = Array.prototype.slice.call(panel.querySelectorAll('.aa-lines li'));
            if (!lis.length) { return; }
            var full = lis.map(function (li) { return li.getAttribute('data-full') || li.textContent; });
            lis.forEach(function (li, i) { li.setAttribute('data-full', full[i]); });
            if (reduce) { lis.forEach(function (li, i) { li.textContent = full[i]; li.classList.remove('is-typing'); li.hidden = false; }); return; }
            lis.forEach(function (li) { li.textContent = ''; li.hidden = true; li.classList.remove('is-typing'); });
            var delay = 150;
            lis.forEach(function (li, i) {
                var text = full[i];
                timers.push(setTimeout(function () {
                    li.hidden = false; li.classList.add('is-typing');
                    var n = 0;
                    (function step() {
                        n += 1 + (text.length > 40 ? 1 : 0);
                        li.textContent = text.slice(0, n);
                        if (n < text.length) { timers.push(setTimeout(step, 14)); }
                        else { li.classList.remove('is-typing'); }
                    })();
                }, delay));
                delay += Math.max(320, text.length * 15) + 260;
            });
        }

        function select(i, focus, skipRun) {
            tabs.forEach(function (t, j) {
                var on = i === j;
                t.setAttribute('aria-selected', on ? 'true' : 'false');
                t.tabIndex = on ? 0 : -1;
                if (panels[j]) { panels[j].hidden = !on; }
            });
            if (focus) { tabs[i].focus(); }
            // keep the chosen agent visible in the horizontal roster on small screens
            if (tabs[i].scrollIntoView && window.innerWidth < 1100) {
                var box = tabs[i].parentNode, off = tabs[i].offsetLeft - (box.clientWidth - tabs[i].offsetWidth) / 2;
                box.scrollTo ? box.scrollTo({ left: off, behavior: reduce ? 'auto' : 'smooth' }) : (box.scrollLeft = off);
            }
            if (!skipRun) { run(panels[i]); }
        }

        tabs.forEach(function (t, i) {
            t.addEventListener('click', function () { select(i); });
            t.addEventListener('keydown', function (e) {
                var n = tabs.length, k = e.key, to = null;
                if (k === 'ArrowDown' || k === 'ArrowRight') { to = (i + 1) % n; }
                else if (k === 'ArrowUp' || k === 'ArrowLeft') { to = (i - 1 + n) % n; }
                else if (k === 'Home') { to = 0; }
                else if (k === 'End') { to = n - 1; }
                if (to !== null) { e.preventDefault(); select(to, true); }
            });
        });

        Array.prototype.forEach.call(app.querySelectorAll('.aa-replay'), function (b) {
            b.addEventListener('click', function () { run(b.closest('.aa-panel')); });
        });

        // 3D tilt on the avatar (mouse only, off for reduced motion)
        if (fine && !reduce) {
            Array.prototype.forEach.call(app.querySelectorAll('[data-tilt]'), function (el) {
                el.addEventListener('pointermove', function (e) {
                    var r = el.getBoundingClientRect();
                    var x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
                    el.style.setProperty('--ry', (x * 16).toFixed(2) + 'deg');
                    el.style.setProperty('--rx', (-y * 16).toFixed(2) + 'deg');
                });
                el.addEventListener('pointerleave', function () { el.style.setProperty('--ry', '0deg'); el.style.setProperty('--rx', '0deg'); });
            });
        }

        // deep link: #aa-scout or ?agent=scout
        var wanted = null;
        var m = /^#aa-([a-z0-9-]+)$/.exec(location.hash || '');
        if (m) { wanted = m[1]; }
        var qs = /[?&]agent=([a-z0-9-]+)/.exec(location.search || '');
        if (!wanted && qs) { wanted = qs[1]; }
        var startIdx = 0;
        if (wanted) { tabs.forEach(function (t, i) { if (t.getAttribute('data-slug') === wanted) { startIdx = i; } }); }
        select(startIdx, false, true);

        // type the first sample run once the showcase is on screen
        var started = false;
        function startOnce() { if (!started) { started = true; run(panels[startIdx]); } }
        if ('IntersectionObserver' in window) {
            var io = new IntersectionObserver(function (en) {
                if (en[0].isIntersecting) { startOnce(); io.disconnect(); }
            }, { threshold: 0.25 });
            io.observe(app);
        } else { startOnce(); }

        window.addEventListener('hashchange', function () {
            var mm = /^#aa-([a-z0-9-]+)$/.exec(location.hash || '');
            if (!mm) { return; }
            tabs.forEach(function (t, i) { if (t.getAttribute('data-slug') === mm[1]) { select(i); app.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' }); } });
        });
    });
})();
