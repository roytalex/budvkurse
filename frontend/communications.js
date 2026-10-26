                                                                               
window.Communications = (() => {
  let lastReminderCount=null;
  let timer, epoch=0, selection=0, active=null, conversations=[], messages=[], older=false, busy=false;
  const drafts=new Map();
  const valid=(user,version)=>state.me?.id===user&&epoch===version;
  const panel=()=>$('#communications-panel');
  function badge(name,value){document.querySelectorAll(`[data-unread="${name}"]`).forEach(el=>{el.textContent=value>99?'99+':String(value);el.hidden=!value;});}
  function stop(){clearTimeout(timer);lastReminderCount=null;epoch++;selection++;active=null;conversations=[];messages=[];drafts.clear();busy=false;badge('messages',0);badge('reminders',0);if(panel())panel().innerHTML='';}
  function start(){stop();poll();}
  async function summary(){const user=state.me?.id,version=epoch;if(!user)return;const data=await Api.request('/me/communications/summary');if(!valid(user,version))return;badge('messages',data.messages);badge('reminders',data.reminders);return data;}
  async function poll(){
    const version=epoch;
    try{if(state.me&&!document.hidden){const counts=await summary();if(counts&&valid(state.me?.id,version)){const changed=lastReminderCount!==null&&counts.reminders!==lastReminderCount;lastReminderCount=counts.reminders;if(changed&&state.view==='reminders'&&!$('#modal').open)await show();}if(state.view==='messages'&&!busy){await loadConversations();if(active)await updateMessages();}}}
    catch(error){if(state.view==='messages'&&$('#chat-status'))$('#chat-status').textContent='Нет связи. Повторяем подключение…';}
    finally{if(version===epoch&&state.me)timer=setTimeout(poll,state.view==='messages'?5000:30000);}
  }
  function listMarkup(){return conversations.map(c=>`<button class="conversation-row ${c.id===active?'selected':''}" data-conversation="${c.id}" aria-pressed="${c.id===active}"><span class="chat-avatar">${esc(c.partner_name.slice(0,1))}</span><span class="conversation-text"><strong>${esc(c.partner_name)}</strong><span>${esc(c.event_title)}</span><small>${esc(c.last_message||'Начни разговор')}</small></span>${c.unread?`<span class="unread-badge">${c.unread}</span>`:''}</button>`).join('')||'<div class="comms-empty"><b>Здесь будут твои диалоги</b><p>Открой мероприятие и нажми «Написать организатору».</p><button class="secondary-button" data-view="feed">Найти событие</button></div>';}
  async function loadConversations(signal){
    const user=state.me?.id,version=epoch;
    const data=await Api.all('/me/conversations',{},signal);
    if(!valid(user,version)||state.view!=='messages')return;
    conversations=data;
    if($('#conversation-list'))$('#conversation-list').innerHTML=listMarkup();
  }
  async function show(signal){
    const user=state.me.id,version=epoch,view=state.view;
    panel().innerHTML='<div class="loading-state">Загружаем…</div>';
    if(view==='messages'){
      await loadConversations(signal);
      if(!valid(user,version)||state.view!==view||signal?.aborted)return;
      panel().innerHTML=`<div class="messages-layout"><aside class="conversation-list" id="conversation-list" aria-label="Диалоги">${listMarkup()}</aside><section class="chat-pane" id="chat-pane" aria-label="Переписка"><div class="comms-empty"><h3>На связи с организатором</h3><p>Выбери диалог слева. Переписку видите только вы двое.</p></div></section></div>`;
      $('#results-count').textContent=`Диалогов: ${conversations.length}`;
      if(active&&conversations.some(c=>c.id===active))await selectConversation(active);
    }else{
      const rows=await Api.all('/me/reminders',{},signal);
      if(!valid(user,version)||state.view!==view||signal?.aborted)return;
      $('#results-count').textContent=`Напоминаний: ${rows.length}`;
      panel().innerHTML=`<p class="comms-explanation">Напоминания появляются здесь, когда приходит выбранное время. При закрытом сайте они будут доступны после входа. Пропущенные напоминания доступны ещё неделю после начала события.</p><div class="reminder-list">${rows.map(r=>`<article class="reminder-card ${r.unread?'unread':''}"><span class="reminder-symbol">◷</span><div><span class="mini-label">${r.unread?'НОВОЕ НАПОМИНАНИЕ':'ПРОЧИТАНО'}</span><h3><button data-event="${r.event.id}">${esc(r.event.title)}</button></h3><p>${dateRange(r.event)}</p><small>${r.minutes_before===0?'В момент начала':'За '+r.minutes_before+' мин. до начала'}</small><div class="manage-actions"><button data-event="${r.event.id}">Открыть событие</button>${r.unread?`<button data-reminder-read="${r.event.id}" data-due="${esc(r.due_at)}">Отметить прочитанным</button>`:''}<button data-reminder="${r.event.id}">Настроить</button></div></div></article>`).join('')||'<div class="comms-empty"><h3>Всё под контролем</h3><p>Пока нет наступивших напоминаний. В карточке события нажми «Напомнить» и выбери время.</p><button class="secondary-button" data-view="calendar">Открыть календарь</button></div>'}</div>`;
    }
    await summary();
  }
  function remember(){const input=$('#message-text');if(active&&input){const old=drafts.get(active);drafts.set(active,{body:input.value,client_id:old?.body===input.value?old.client_id:null});}}
  function messageMarkup(m){return `<article class="chat-message ${m.sender_id===state.me.id?'outgoing':'incoming'}" data-message-id="${m.id}"><p>${esc(m.body)}</p><time datetime="${esc(m.created_at)}">${dt(m.created_at)}</time></article>`;}
  function drawMessages(scroll=true,prepend=false){const box=$('#message-history');if(!box)return;const top=box.scrollTop,height=box.scrollHeight;box.innerHTML=`${older?'<button class="chat-older secondary-button" data-chat-older="true">Предыдущие сообщения</button>':''}${messages.map(messageMarkup).join('')||'<p class="chat-intro">Задай вопрос о мероприятии — организатор увидит его в сообщениях.</p>'}`;box.scrollTop=scroll?box.scrollHeight:top+(prepend?box.scrollHeight-height:0);}
  async function markRead(){
    const box=$('#message-history');if(document.hidden||state.view!=='messages'||!active||!messages.length||$('#modal').open||!box||box.scrollHeight-box.scrollTop-box.clientHeight>80)return;
    await Api.request(`/conversations/${active}/read`,{method:'POST',body:{message_id:messages.at(-1).id}});
  }
  async function selectConversation(id){
    remember();const sequence=++selection;active=Number(id);messages=[];older=false;
    const user=state.me.id,version=epoch,c=conversations.find(c=>c.id===active);
    if(!c)return;
    $('.messages-layout')?.classList.add('chat-open');$('#conversation-list').innerHTML=listMarkup();
    $('#chat-pane').innerHTML='<div class="loading-state">Открываем диалог…</div>';
    const result=await Api.request(`/conversations/${active}/messages`);
    if(!valid(user,version)||selection!==sequence||state.view!=='messages')return;
    messages=result.items;older=result.has_more;
    $('#chat-pane').innerHTML=`<header class="chat-header"><button class="chat-back secondary-button" data-chat-back="true" aria-label="Вернуться к диалогам">←</button><div><h2>${esc(c.partner_name)}</h2><span>${esc(c.event_title)}${c.event_id?'':' · Событие удалено'}</span></div>${c.event_id?`<button class="secondary-button" data-event="${c.event_id}">Событие ↗</button>`:''}</header><div class="message-history" id="message-history" role="log" aria-label="История сообщений" aria-live="polite"></div><p id="chat-status" class="chat-status" role="status">${c.partner_active?'Сообщения обновляются автоматически':'Собеседник сейчас недоступен'}</p><form id="message-form" class="message-compose" data-conversation="${active}"><label for="message-text" class="sr-only">Сообщение организатору или участнику</label><textarea id="message-text" name="body" placeholder="Напиши сообщение…" maxlength="4000" rows="2" required ${c.partner_active?'':'disabled'}>${esc(drafts.get(active)?.body||'')}</textarea><button class="primary-button" type="submit" ${c.partner_active?'':'disabled'}>Отправить ↑</button><div class="form-error" role="alert"></div></form>`;
    drawMessages();$('#message-text').addEventListener('input',remember);
    $('#message-history').addEventListener('scroll',()=>{clearTimeout(markRead.timer);markRead.timer=setTimeout(()=>markRead().catch(()=>{}),300);});
    await markRead();await summary();
  }
  async function updateMessages(){
    const id=active,sequence=selection,user=state.me.id,version=epoch;
    if(!$('#message-history'))return;
    const box=$('#message-history'),atBottom=box.scrollHeight-box.scrollTop-box.clientHeight<80;
    const q=messages.length?'?after_id='+messages.at(-1).id:'';
    const result=await Api.request(`/conversations/${id}/messages`+q);
    if(!valid(user,version)||selection!==sequence||state.view!=='messages'||active!==id)return;
    if(result.items.length){if(!messages.length)older=result.has_more;const known=new Set(messages.map(m=>m.id));messages.push(...result.items.filter(m=>!known.has(m.id)));drawMessages(atBottom);}
    $('#chat-status').textContent='Сообщения обновляются автоматически';
    await markRead();
  }
  async function send(form){
    const id=Number(form.dataset.conversation),text=String(new FormData(form).get('body')||'').trim();
    if(!text)throw new Error('Напиши текст сообщения.');
    const user=state.me.id,version=epoch;
    const previous=drafts.get(id);const client_id=previous?.body===text&&previous.client_id?previous.client_id:crypto.randomUUID();
    drafts.set(id,{body:text,client_id});busy=true;
    try{
      await Api.request(`/conversations/${id}/messages`,{method:'POST',body:{body:text,client_id}});
      if(!valid(user,version))return;
                                                                             
      if(form.isConnected&&form.elements.body.value.trim()===text){form.elements.body.value='';drafts.delete(id);}
      else if(drafts.get(id)?.body===text)drafts.delete(id);
      if(active===id&&state.view==='messages')await updateMessages();
      await loadConversations();await summary();
    }finally{if(valid(user,version))busy=false;}
  }
  async function reminderForm(id){
    const user=state.me.id,version=epoch;await refreshPersonal();if(!valid(user,version))return;
    const plan=state.plans.find(p=>p.event.id===Number(id));const minutes=plan?plan.reminder_minutes_before:60;
    const choices=[[null,'Не напоминать'],[0,'В момент начала'],[15,'За 15 минут'],[30,'За 30 минут'],[60,'За час'],[180,'За 3 часа'],[1440,'За день'],[10080,'За неделю']];
    if(minutes!==null&&!choices.some(([v])=>v===minutes))choices.push([minutes,`За ${minutes} мин.`]);
    openModal(`<h2 class="modal-heading">Напомнить о мероприятии</h2><p class="modal-description">Событие будет сохранено в твоих планах. Напоминание появится в разделе «Напоминания»; если сайт закрыт — увидишь его при следующем входе.</p><form id="reminder-form" data-event="${id}"><label class="form-field">Когда напомнить<select name="minutes" required>${choices.map(([value,label])=>`<option value="${value??'off'}" ${value===minutes?'selected':''}>${label}</option>`).join('')}</select></label><div class="form-error" role="alert"></div><div class="form-actions"><button class="primary-button" type="submit">Сохранить</button></div></form>`);
  }
  async function saveReminder(form){const value=form.elements.minutes.value;await Api.request('/me/plans/'+form.dataset.event,{method:'PUT',body:{reminder_minutes_before:value==='off'?null:Number(value)}});closeModal();await afterMutation();await summary();toast(value==='off'?'Напоминание выключено, событие осталось в планах':'Напоминание сохранено');}
  async function handleClick(d){
    if(d.contact){const row=await Api.request(`/events/${d.contact}/conversation`,{method:'POST'});remember();active=null;await navigate('messages');await selectConversation(row.id);return true;}
    if(d.conversation){await selectConversation(d.conversation);return true;}
    if(d.chatBack){remember();active=null;selection++;$('.messages-layout')?.classList.remove('chat-open');return true;}
    if(d.chatOlder){
      const id=active,sequence=selection;const result=await Api.request(`/conversations/${id}/messages?before_id=${messages[0].id}`);
      if(active!==id||sequence!==selection||state.view!=='messages')return true;
      messages=[...result.items,...messages];older=result.has_more;drawMessages(false,true);return true;
    }
    if(d.reminder){await reminderForm(d.reminder);return true;}
    if(d.reminderRead){await Api.request(`/me/reminders/${d.reminderRead}/read`,{method:'POST',body:{due_at:d.due}});await loadView();await summary();return true;}
    return false;
  }
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&typeof state!=='undefined'&&state.me)summary().catch(()=>{});});
  return {start,stop,show,send,saveReminder,handleClick,summary,remember};
})();
