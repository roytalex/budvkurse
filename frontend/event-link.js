(() => {
  'use strict';
  window.addEventListener('app-session-ready', async () => {
    const url = new URL(location.href);
    const id = url.searchParams.get('event');
    if (!id || !/^[1-9][0-9]{0,9}$/.test(id)) return;
    url.searchParams.delete('event');
    history.replaceState(null, '', url.pathname + url.search + url.hash);
    try { await openEvent(Number(id)); }
    catch { toast('Не удалось открыть событие. Найди его в ленте.'); }
  });
})();
