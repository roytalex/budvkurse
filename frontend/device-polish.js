(() => {
  'use strict';
  const root = document.documentElement;
  const auth = document.querySelector('#auth-form-wrap');
  const menu = document.querySelector('#nav-dialog');
  function passwords() {
    auth?.querySelectorAll('input[type="password"]').forEach(input => {
      if (input.closest('.password-control')) return;
      const wrapper = document.createElement('span');
      input.setAttribute('aria-label', input.name === 'confirm' ? 'Повтори пароль' : 'Пароль');
      wrapper.className = 'password-control';
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'password-toggle';
      button.textContent = 'Показать';
      button.setAttribute('aria-label', input.name === 'confirm' ? 'Показать повтор пароля' : 'Показать пароль');
      button.setAttribute('aria-pressed', 'false');
      input.before(wrapper);
      wrapper.append(input, button);
      button.addEventListener('click', () => {
        const shown = input.type === 'password';
        input.type = shown ? 'text' : 'password';
        button.textContent = shown ? 'Скрыть' : 'Показать';
        button.setAttribute('aria-pressed', String(shown));
        button.setAttribute('aria-label', `${shown ? 'Скрыть' : 'Показать'} ${input.name === 'confirm' ? 'повтор пароля' : 'пароль'}`);
      });
    });
    auth?.querySelectorAll('input[type="email"]').forEach(input => {
      input.setAttribute('inputmode', 'email');
      input.setAttribute('autocapitalize', 'none');
      input.setAttribute('spellcheck', 'false');
    });
  }
  if (auth) new MutationObserver(passwords).observe(auth, {childList:true, subtree:true});
  passwords();
  const geography = document.querySelector('#geo-toolbar');
  if (geography) {
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'geography-toggle';
    toggle.setAttribute('aria-controls', 'geo-toolbar');
    toggle.setAttribute('aria-expanded', 'false');
    root.dataset.geography = 'collapsed';
    geography.before(toggle);
    const label = document.createElement('span');
    const symbol = document.createElement('b');
    symbol.setAttribute('aria-hidden', 'true');
    toggle.append(label, symbol);
    function geographyState() {
      toggle.hidden = geography.hidden;
      const city = document.querySelector('#geo-city');
      const school = document.querySelector('#geo-school');
      label.textContent = school?.value ? school.selectedOptions[0].text : city?.value ? city.selectedOptions[0].text : 'Город и школа';
      const expanded = root.dataset.geography === 'expanded';
      toggle.setAttribute('aria-expanded', String(expanded));
      symbol.textContent = expanded ? '−' : '+';
    }
    toggle.addEventListener('click', () => {
      root.dataset.geography = root.dataset.geography === 'expanded' ? 'collapsed' : 'expanded';
      geographyState();
    });
    new MutationObserver(geographyState).observe(geography, {attributes:true, attributeFilter:['hidden'], childList:true, subtree:true});
    geography.addEventListener('change', geographyState);
    geographyState();
  }
  function menuState() {
    document.querySelectorAll('[data-nav-open]').forEach(button => button.setAttribute('aria-expanded', String(!!menu?.open)));
  }
  if (menu) new MutationObserver(menuState).observe(menu, {attributes:true, attributeFilter:['open']});
  menuState();
  let maxHeight = window.innerHeight;
  function viewport() {
    const visual = window.visualViewport;
    const editing = document.activeElement?.matches('input:not([type="checkbox"]):not([type="radio"]),textarea,[contenteditable="true"]');
    if (!editing) maxHeight = window.innerHeight;
    const height = visual?.height || window.innerHeight;
    const keyboard = !!editing && (Math.max(maxHeight, window.innerHeight) - height > 150) && (!visual || visual.scale === 1);
    root.dataset.keyboard = keyboard ? 'open' : 'closed';
  }
  window.visualViewport?.addEventListener('resize', viewport, {passive:true});
  window.addEventListener('resize', viewport, {passive:true});
  window.addEventListener('orientationchange', () => { maxHeight = window.innerHeight; });
  document.addEventListener('focusin', viewport);
  document.addEventListener('focusout', () => requestAnimationFrame(viewport));
  document.addEventListener('keydown', event => {
    const day = event.target.closest?.('.month-day[data-calendar-day]');
    if (!day || event.altKey || event.ctrlKey || event.metaKey) return;
    const days = [...document.querySelectorAll('.month-day[data-calendar-day]')];
    const position = days.indexOf(day);
    const offsets = {ArrowLeft:-1, ArrowRight:1, ArrowUp:-7, ArrowDown:7};
    let target;
    if (event.key in offsets) target = position + offsets[event.key];
    else if (event.key === 'Home') target = 0;
    else if (event.key === 'End') target = days.length - 1;
    else return;
    event.preventDefault();
    days[Math.max(0, Math.min(days.length - 1, target))]?.focus();
  });
  viewport();
})();
