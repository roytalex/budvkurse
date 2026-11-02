'use strict';
window.MaxSettings = (() => {
  async function open() {
    const userId = state.me?.id;
    if (!userId) return;
    const info = await Api.request('/integrations/max/connection');
    if (state.me?.id !== userId) return;
    const native = window.MaxShell?.active();
    openModal(`<div class="modal-kicker">MAX · НАПОМИНАНИЯ</div><h2 class="modal-heading">Встретимся вовремя.</h2><p class="form-hint">${info.enabled ? 'MAX подключён. Бот напомнит о выбранных событиях, даже когда сайт закрыт.' : info.connected ? 'Уведомления приостановлены. Подключи их снова внутри мини-приложения.' : 'Подключи свой MAX к этому аккаунту, чтобы получать напоминания от бота.'}</p><p>После записи на событие напоминание ставится за час. В карточке можно изменить время или выключить его. Команда /stop в боте отключает все сообщения-напоминания.</p>${!info.available ? '<p class="form-hint">Администратор ещё не настроил бота MAX. Напоминания внутри сайта продолжают работать.</p>' : !info.enabled && native ? '<button class="primary-button" data-max-connection="connect">Разрешить напоминания в MAX</button>' : !info.enabled ? '<p class="form-hint">Открой бота, нажми «Открыть приложение», войди в этот же аккаунт и подключи MAX в профиле.</p>' : ''}${info.bot_url ? `<p><a class="secondary-button" href="${esc(info.bot_url)}" target="_blank" rel="noopener noreferrer">Открыть бота MAX ↗</a></p>` : ''}${info.connected ? '<button class="text-button danger" data-max-connection="disconnect">Отключить MAX от аккаунта</button>' : ''}<div class="form-error" role="alert"></div>`, 'max-settings');
  }
  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-max-connection]');
    if (!button || button.disabled) return;
    button.disabled = true;
    const userId = state.me?.id;
    try {
      const action = button.dataset.maxConnection;
      if (action === 'connect') {
        const initData = window.MaxShell?.initData();
        if (!initData) throw new Error('Открой приложение из бота MAX и повтори подключение.');
        await Api.request('/integrations/max/connection', {method:'POST', body:{init_data:initData}});
      } else if (action === 'disconnect') {
        await Api.request('/integrations/max/connection', {method:'DELETE'});
      }
      if (state.me?.id !== userId) return;
      await open();
      if (action === 'connect') toast('Напоминания MAX подключены');
      if (action === 'disconnect') toast('MAX отключён от аккаунта');
    } catch (error) {
      if (state.me?.id === userId) toast(error.message);
    } finally {
      if (button.isConnected) button.disabled = false;
    }
  });
  return {open};
})();
