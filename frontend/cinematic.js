(() => {
  'use strict';
  const media = window.matchMedia('(prefers-reduced-motion: reduce)');
  let preference = '';
  try { preference = localStorage.getItem('budvkurse-motion') || ''; } catch {}
  const animations = new Set();
  const seen = new WeakSet();
  const selector = '.event-card,.explore-card,.achievement-card,.team-card,.school-score,.visit-row,.passport-cover,.challenge-banner,.achievement-hero,.auth-card,.agenda-card,.podium-card,.ranking-stage,.collection-hero,.my-standing,.team-intro';
  const enabled = () => !media.matches && preference !== 'off';
  const observer = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      if (!enabled() || !entry.target.animate) return;
      const animation = entry.target.animate([
        { opacity: .15, transform: 'translateY(18px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ], { duration: 520, easing: 'cubic-bezier(.2,.7,.2,1)', delay: Math.min(Array.from(entry.target.parentElement.children).indexOf(entry.target), 4) * 45 });
      animations.add(animation);
      animation.onfinish = animation.oncancel = () => animations.delete(animation);
    });
  }, { threshold: .08 }) : null;
  function observe(root) {
    if (!observer || !(root instanceof Element)) return;
    const targets = [...root.querySelectorAll(selector)];
    if (root.matches(selector)) targets.unshift(root);
    targets.forEach(element => {
      if (!seen.has(element)) { seen.add(element); observer.observe(element); }
    });
  }
  function update() {
    document.documentElement.dataset.motion = enabled() ? 'on' : 'off';
    if (!enabled()) [...animations].forEach(animation => animation.cancel());
    document.querySelectorAll('[data-motion-toggle]').forEach(button => {
      button.setAttribute('aria-pressed', String(enabled()));
      button.setAttribute('aria-label', media.matches ? 'Анимации отключены настройкой устройства' : enabled() ? 'Выключить анимации' : 'Включить анимации');
      button.title = button.getAttribute('aria-label');
      button.disabled = media.matches;
      button.querySelector('[data-motion-symbol]').textContent = enabled() ? 'Ⅱ' : '▷';
    });
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-motion-toggle]');
    if (!button) return;
    preference = enabled() ? 'off' : 'on';
    try { localStorage.setItem('budvkurse-motion', preference); } catch {}
    update();
  });
  media.addEventListener('change', update);
  update();
  observe(document.body);
  if (observer) {
    new MutationObserver(records => records.forEach(record => {
      record.removedNodes.forEach(node => {
        if (!(node instanceof Element)) return;
        observer.unobserve(node);
        node.querySelectorAll(selector).forEach(element => observer.unobserve(element));
      });
      record.addedNodes.forEach(observe);
    })).observe(document.body, { childList: true, subtree: true });
  }
})();
