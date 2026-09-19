/* Rizen Digital - futuristic homepage behaviour. No dependencies. */
(function () {
  'use strict';
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // Reveal on scroll
  var items = $$('.hf-r');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  } else { items.forEach(function (el) { el.classList.add('in'); }); }

  // Spotlight glow that follows the cursor
  $$('[data-hf-glow]').forEach(function (c) {
    c.addEventListener('pointermove', function (e) {
      var r = c.getBoundingClientRect();
      c.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      c.style.setProperty('--my', (e.clientY - r.top) + 'px');
    }, { passive: true });
  });

  // Hero console tilt (fine pointers only)
  var tilt = document.querySelector('[data-hf-tilt]');
  if (tilt && !reduce && window.matchMedia('(pointer: fine)').matches) {
    var box = tilt.parentNode;
    box.addEventListener('pointermove', function (e) {
      var r = box.getBoundingClientRect();
      tilt.style.setProperty('--ry', (((e.clientX - r.left) / r.width - .5) * 8).toFixed(2) + 'deg');
      tilt.style.setProperty('--rx', (((e.clientY - r.top) / r.height - .5) * -8).toFixed(2) + 'deg');
    }, { passive: true });
    box.addEventListener('pointerleave', function () { tilt.style.setProperty('--rx', '0deg'); tilt.style.setProperty('--ry', '0deg'); });
  }

  // Agent activity feed rotates
  var feed = $$('[data-hf-feed] li');
  if (feed.length > 1 && !reduce) {
    var i = 0;
    setInterval(function () {
      feed[i].classList.remove('on'); i = (i + 1) % feed.length; feed[i].classList.add('on');
    }, 2600);
  }

  // Counters
  var counters = $$('[data-hf-count]');
  function run(el) {
    var end = +el.getAttribute('data-hf-count'), t0 = null;
    function step(t) {
      if (t0 === null) t0 = t;
      var p = Math.min((t - t0) / 1200, 1);
      el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  if ('IntersectionObserver' in window && !reduce) {
    var co = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { run(e.target); co.unobserve(e.target); } });
    }, { threshold: 0.2 });
    counters.forEach(function (c) { c.textContent = '0'; co.observe(c); });
  }

  // Pricing toggle
  var btns = $$('[data-hf-bill]');
  btns.forEach(function (b) {
    b.addEventListener('click', function () {
      var mode = b.getAttribute('data-hf-bill');
      btns.forEach(function (x) { var on = x === b; x.classList.toggle('on', on); x.setAttribute('aria-pressed', on); });
      $$('[data-monthly]').forEach(function (el) { el.textContent = el.getAttribute('data-' + mode); });
    });
  });
})();
