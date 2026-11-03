'use strict';
window.MaxSettings = (() => {
  let command = '', owner = null;
  async function open() {
    const userId = state.me?.id;
    if (!userId) return;
    const info = await Api.request('/integrations/max/connection');
    if (state.me?.id !== userId) return;
    command = ''; owner = null;
    const native = window.MaxShell?.active();
    openModal(`<div class="modal-kicker">MAX · НАПОМИНАНИЯ</div><h2 class="modal-heading">Встретимся вовремя.</h2><p class="form-hint">${info.enabled ? 'MAX подключён. Бот напомнит о выбранных событиях, даже когда сайт закрыт.' : info.connected ? 'Напоминания приостановлены. Подтверди подключение, чтобы включить их снова.' : 'Подключи свой MAX к этому аккаунту, чтобы получать напоминания от бота.'}</p><p>После записи на событие напоминание ставится за час. В карточке можно изменить время или выключить его. Команда /stop отключает напоминания, сохраняя записи на мероприятия.</p>${!info.available ? '<p class="form-hint">Бот MAX пока не настроен. Напоминания внутри сайта продолжают работать.</p>' : !info.enabled ? `<div class="form-actions">${native ? '<button class="primary-button" data-max-connection="connect">Разрешить напоминания в MAX</button>' : ''}<button class="${native?'secondary':'primary'}-button" data-max-connection="pair">Подключить через бота</button></div><p class="form-hint">Работает и в обычном браузере. Создадим одноразовую ссылку, а ты подтвердишь подключение в MAX.</p>` : ''}<div class="form-actions"><button class="secondary-button" data-max-connection="open">Проверить подключение</button>${info.bot_url ? `<a class="secondary-button" href="${esc(info.bot_url)}" target="_blank" rel="noopener noreferrer">Открыть бота MAX </a>` : ''}</div>${info.connected ? '<button class="text-button danger" data-max-connection="disconnect">Отключить MAX от аккаунта</button>' : ''}<p class="form-hint">Для доставки сервер проекта должен работать. Отменённые события и выключенные напоминания не отправляются.</p><div class="form-error" role="alert"></div>`, 'max-settings');
  }
  async function pair(userId) {
    const result = await Api.request('/integrations/max/connection/link', {method:'POST'});
    if (state.me?.id !== userId) return;
    const url = new URL(result.url);
    if (url.protocol !== 'https:' || url.hostname !== 'max.ru' || !/^\/connect [A-Za-z0-9_-]{32}$/.test(result.command)) throw new Error('Не удалось создать ссылку подключения. Попробуй ещё раз.');
    command = result.command; owner = userId;
    openModal(`<div class="modal-kicker">MAX · ПОДКЛЮЧЕНИЕ</div><h2 class="modal-heading">Один шаг в боте.</h2><p>Открой бота по кнопке и нажми в его сообщении «Подключить напоминания». Проверь, что бот показывает имя твоего аккаунта.</p><p><a class="primary-button" href="${esc(result.url)}" target="_blank" rel="noopener noreferrer">Открыть бота и подтвердить </a></p><p class="form-hint">Ссылка действует 10 минут, до ${esc(new Date(result.expires_at).toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'}))}. Не пересылай её другим людям. Новая ссылка заменяет предыдущую.</p><details><summary>Кнопка открыла только чат?</summary><p class="form-hint">Скопируй команду, отправь её в чат боту и нажми кнопку подтверждения в ответе.</p><label class="form-field">Команда подключения<input id="max-pair-command" readonly autocomplete="off" spellcheck="false" value="${esc(result.command)}"></label><button class="secondary-button" data-max-connection="copy">Скопировать команду</button></details><div class="form-actions"><button class="primary-button" data-max-connection="open">Проверить подключение</button><button class="secondary-button" data-max-connection="cancel-pair">Отменить ссылку</button></div>`, 'max-settings');
  }
  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-max-connection]');
    if (!button || button.disabled) return;
    button.disabled = true;
    const userId = state.me?.id;
    if (!userId) { button.disabled = false; return; }
    try {
      const action = button.dataset.maxConnection;
      if (action === 'pair') { await pair(userId); return; }
      if (action === 'copy') {
        if (!command || owner !== userId) throw new Error('Создай новую ссылку подключения.');
        try { await navigator.clipboard.writeText(command); toast('Команда скопирована. Отправь её боту MAX.'); }
        catch { document.querySelector('#max-pair-command')?.select(); toast('Выделил команду. Скопируй её вручную и отправь боту.'); }
        return;
      }
      if (action === 'connect') {
        const initData = window.MaxShell?.initData();
        if (!initData) throw new Error('Открой приложение из бота MAX или выбери «Подключить через бота».');
        await Api.request('/integrations/max/connection', {method:'POST', body:{init_data:initData}});
      } else if (action === 'disconnect') {
        await Api.request('/integrations/max/connection', {method:'DELETE'});
      } else if (action === 'cancel-pair') {
        await Api.request('/integrations/max/connection/link', {method:'DELETE'});
      }
      if (state.me?.id !== userId) return;
      await open();
      if (action === 'connect') toast('Напоминания MAX подключены');
      if (action === 'disconnect') toast('MAX отключён от аккаунта');
      if (action === 'cancel-pair') toast('Ссылка подключения отменена');
    } catch (error) {
      if (state.me?.id === userId) toast(error.message);
    } finally {
      if (button.isConnected) button.disabled = false;
    }
  });
  return {open};
})();
