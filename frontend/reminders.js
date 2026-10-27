'use strict';
window.Reminders = (() => {
  let timer=0,epoch=0,rows=[],running=false,controller=null;
  const seen=new Set();
  const key=r=>`${r.event.id}:${r.event.starts_at}`;
  function badge(){document.querySelectorAll('[data-reminder-count]').forEach(el=>{const n=rows.filter(r=>r.unread).length;el.textContent=n;el.hidden=!n;});}
  function stop(){epoch++;clearTimeout(timer);controller?.abort();controller=null;running=false;rows=[];seen.clear();badge();}
  async function poll(){
    clearTimeout(timer);
    if(!state.me||running)return;
    if(document.hidden){timer=setTimeout(poll,60000);return;}
    const gen=epoch,userId=state.me.id;
    running=true;controller=new AbortController();
    try{
      const result=await Api.all('/me/reminders',{},controller.signal);
      if(gen!==epoch||state.me?.id!==userId)return;
      rows=result;badge();
      const fresh=rows.filter(r=>r.unread&&!seen.has(key(r)));
      fresh.forEach(r=>seen.add(key(r)));
      if(fresh.length)toast(fresh.length===1?`Скоро: ${fresh[0].event.title}. Открой напоминания.`:`Напоминаний о событиях: ${fresh.length}. Открой колокольчик.`);
      if(state.view==='reminders')render();
    }catch{}finally{if(gen===epoch){running=false;timer=setTimeout(poll,60000);}}
  }
  function start(){stop();poll();}
  function refresh(){epoch++;clearTimeout(timer);controller?.abort();controller=null;running=false;return poll();}
  function settings(id){
    const plan=state.plans.find(p=>p.event.id===Number(id));
    const minutes=plan?.reminder_minutes_before??'';
    const choices=[['','Выключено'],[0,'В момент начала'],[15,'За 15 минут'],[60,'За час'],[1440,'За день'],[10080,'За неделю']];
    if(minutes!==''&&!choices.some(([value])=>value===minutes))choices.push([minutes,`За ${minutes} мин.`]);
    openModal(`<div class="modal-kicker">ЛИЧНЫЙ КАЛЕНДАРЬ</div><h2 class="modal-heading">Помним о важном.</h2><form id="reminder-form" data-event="${Number(id)}"><label class="form-field">Когда напомнить<select name="minutes">${choices.map(([value,label])=>`<option value="${value}" ${value===minutes?'selected':''}>${label}</option>`).join('')}</select></label><p class="form-hint">Событие появится в твоём календаре. Это не регистрация на мероприятие. Напоминания работают внутри открытого сайта; доставка в MAX появится позже.</p><div class="form-error" role="alert"></div><button type="submit" class="primary-button">Сохранить</button></form>`,'reminder');
  }
  async function submit(form){
    const value=new FormData(form).get('minutes');
    await Api.request('/me/plans/'+form.dataset.event,{method:'PUT',body:{reminder_minutes_before:value===''?null:Number(value)}});
    await refreshPersonal();closeModal();await loadView();await refresh();toast(value===''?'Напоминание выключено':'Напоминание сохранено');
  }
  function render(){
    const sorted=[...rows].sort((a,b)=>Number(b.unread)-Number(a.unread)||new Date(a.reminder_at)-new Date(b.reminder_at));
    $('#results-count').textContent=`Напоминаний: ${rows.length}`;
    $('#achievements-panel').innerHTML=`<div class="reminder-intro"><span class="editorial-kicker">ВРЕМЯ ДЛЯ ТВОИХ ПЛАНОВ</span><h2>Сначала интерес.<br>Потом — встреча.</h2><p>Выбирай время напоминания в карточке события. Пока сайт открыт, мы проверяем планы каждую минуту. Уведомления о завершившихся и отменённых событиях здесь не появляются.</p></div><div class="reminder-list">${sorted.map(r=>`<article class="reminder-row ${r.unread?'is-due':''}"><div class="reminder-date"><b>${new Date(r.event.starts_at).getDate()}</b><span>${esc(new Date(r.event.starts_at).toLocaleDateString('ru-RU',{month:'short'}))}</span></div><div><span class="activity-tag">${r.read?'Прочитано':r.unread?'Пора вспомнить':'Запланировано'}</span><h3><button data-event="${r.event.id}">${esc(r.event.title)}</button></h3><p>Начало: ${dt(r.event.starts_at)}</p><small>Напоминание: ${dt(r.reminder_at)}</small></div><div class="activity-actions"><button class="secondary-button" data-reminder-settings="${r.event.id}">Настроить</button>${r.unread?`<button class="primary-button" data-reminder-read="${r.event.id}">Прочитано</button>`:''}</div></article>`).join('')||'<div class="empty-state"><h3>Планы начинаются с интереса.</h3><p>Открой событие и нажми «Настроить напоминание».</p><button class="primary-button" data-view="feed">Найти мероприятие</button></div>'}</div>`;
  }
  async function show(signal){
    const gen=epoch,userId=state.me?.id;
    $('#achievements-panel').innerHTML='<div class="loading-state">Загружаем напоминания…</div>';
    const result=await Api.all('/me/reminders',{},signal);
    if(signal.aborted||gen!==epoch||state.me?.id!==userId||state.view!=='reminders')return;
    rows=result;badge();render();
  }
  async function read(id){
    const row=rows.find(r=>r.event.id===Number(id));if(!row)return;
    await Api.request(`/me/reminders/${id}/read`,{method:'PUT',body:{starts_at:row.event.starts_at}});
    epoch++;clearTimeout(timer);controller?.abort();controller=null;running=false;
    row.read=true;row.unread=false;badge();if(state.view==='reminders')render();timer=setTimeout(poll,60000);
  }
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&state.me)poll();});
  return {start,stop,refresh,show,settings,submit,read};
})();
