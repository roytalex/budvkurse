'use strict';
window.Achievements = (() => {
  const symbols = {first_step:'✦',explorer:'◈',active_ten:'✺',regular:'✹',olympiad_start:'✧',olympiad_three:'♜',olympiad_ten:'♛'};
  function cards(items) {
    return `<div class="achievement-grid">${items.map(a=>`<article class="achievement-card ${a.earned?'earned':''}"><div class="achievement-top"><span class="achievement-symbol" aria-hidden="true">${symbols[a.code]||'✦'}</span><span class="achievement-label">${a.earned?'Получено':'Впереди'}</span></div><h3>${esc(a.title)}</h3><p>${esc(a.description)}</p><div class="achievement-progress"><span>${a.progress} / ${a.target}</span><b>+${a.points} баллов</b></div><progress value="${a.progress}" max="${a.target}" aria-label="${esc(a.title)}: ${a.progress} из ${a.target}"></progress></article>`).join('')}</div>`;
  }
  function stats(data) {
    return `<div class="achievement-stats"><div><strong>${data.attendance_count}</strong><span>Посещено событий</span></div><div><strong>${data.olympiad_count}</strong><span>Из них олимпиад</span></div><div><strong>${data.earned_count}</strong><span>Достижений</span></div><div><strong>${data.rank?('#'+data.rank):'—'}</strong><span>Место в рейтинге</span></div></div>`;
  }
  function hero(data) {
    return `<div class="achievement-hero"><div><span class="achievement-eyebrow">ТВОЯ ИСТОРИЯ УЧАСТИЯ</span><h2>Впечатления становятся<br>достижениями.</h2><p>Посещай события, открывай награды и поднимайся в общем рейтинге.</p><button class="hero-button" data-view="${state.view==='leaderboard'?'achievements':'leaderboard'}">${state.view==='leaderboard'?'Мои достижения':'Посмотреть рейтинг'} ↗</button></div><div class="achievement-score"><span aria-hidden="true">✦</span><strong>${data.points}</strong><small>баллов за достижения</small></div></div>`;
  }
  async function show(signal) {
    const view = state.view, page = state.page;
    const panel = $('#achievements-panel');
    panel.innerHTML='<div class="loading-state">Загружаем достижения…</div>';
    const [mine, board] = await Promise.all([
      Api.request('/me/achievements',{signal}),
      view==='leaderboard'?Api.request('/achievements/leaderboard?'+Api.query({page,limit:20}),{signal}):null
    ]);
    if(signal.aborted || state.view!==view || state.page!==page || !state.me)return;
    $('#results-count').textContent=board?`Участников в рейтинге: ${board.total}`:`Получено: ${mine.earned_count} из ${mine.achievements.length}`;
    if(!board){
      panel.innerHTML=hero(mine)+stats(mine)+`<div class="achievement-section"><h2>Коллекция достижений</h2><p>Посещение подтверждает организатор или администратор после окончания события. Запись и добавление в календарь сами по себе не дают баллов.</p></div>`+cards(mine.achievements);
      return;
    }
    panel.innerHTML=hero(mine)+`<div class="leaderboard-note"><b>${mine.rank?`Твоё место — ${mine.rank}. Баллов: ${mine.points}.`:'Твоя история только начинается.'}</b><span>Рейтинг виден каждому пользователю сайта. Сначала идут баллы за награды, при равенстве — число посещений. Одинаковый результат даёт одинаковое место.</span></div>`+(board.items.length?`<div class="leaderboard" role="list" aria-label="Участники рейтинга">${board.items.map(u=>`<button class="leaderboard-row ${u.user_id===state.me.id?'is-me':''}" data-achievement-user="${u.user_id}" role="listitem" aria-label="${esc(u.name)}, место ${u.rank}, ${u.points} баллов"><span class="leaderboard-rank ${u.rank<=3?'top-rank':''}">${u.rank}</span><span class="leaderboard-avatar" aria-hidden="true">${esc(u.name.slice(0,1).toUpperCase())}</span><span class="leaderboard-person"><b>${esc(u.name)}${u.user_id===state.me.id?' <small>Это ты</small>':''}</b><span>Событий: ${u.attendance_count} · Олимпиад: ${u.olympiad_count} · Наград: ${u.earned_count}</span></span><span class="leaderboard-points"><b>${u.points}</b><small>баллов</small></span></button>`).join('')}</div>`:'<div class="empty-state"><span>✦</span><h3>Первое место пока свободно</h3><p>После первого подтверждённого посещения участник появится здесь.</p><button class="primary-button" data-view="feed">Найти мероприятие</button></div>');
    $('#pagination').innerHTML=board.total>20?`<button data-page="${page-1}" ${page===1?'disabled':''}>← Назад</button><span>${page} / ${Math.ceil(board.total/20)}</span><button data-page="${page+1}" ${page*20>=board.total?'disabled':''}>Дальше →</button>`:'';
  }
  async function participants(id) {
    openModal('<div class="loading-state">Загружаем участников…</div>','participants');
    const sequence=detailNumber;
    try {
      const [event, rows] = await Promise.all([Api.request('/events/'+id),Api.all(`/events/${id}/registrations`)]);
      if(sequence!==detailNumber || !state.me)return;
      const ended=event.status==='published' && new Date(event.ends_at)<=new Date();
      $('#modal-content').innerHTML=`<div class="modal-kicker">ПОСЕЩЕНИЯ И ДОСТИЖЕНИЯ</div><h2 class="modal-heading">Участники</h2><p>${esc(event.title)}</p><p class="form-hint">${ended?'Отметь тех, кто действительно посетил мероприятие. Ошибочную отметку можно снять.':'Подтвердить посещение можно после окончания опубликованного мероприятия.'} Записано: ${rows.filter(x=>x.status==='registered').length}.</p>${ended?`<button class="primary-button" data-scanner="${id}">Сканировать QR участника</button>`:''}${rows.map(u=>`<div class="attendance-row"><div><b>${esc(u.participant_name||'Участник '+u.user_id)}</b><small>${u.grade?u.grade+' класс · ':''}${u.attended?'Посещение подтверждено':u.status==='registered'?'Записан':'Отменил запись'}</small></div>${u.attended?`<button class="secondary-button" data-attendance="${u.user_id}" data-event-id="${id}" data-attended="false">Снять отметку</button>`:u.status==='registered'?`<button class="${ended?'primary':'secondary'}-button" data-attendance="${u.user_id}" data-event-id="${id}" data-attended="true" ${!ended||u.user_id===state.me.id||u.user_id===event.organizer_id?'disabled':''}>Посетил</button>`:''}</div>`).join('')||'<div class="empty-state"><h3>Участников пока нет</h3><p>Здесь появятся пользователи, записавшиеся через сайт.</p></div>'}`;
    } catch(error) {
      if(sequence===detailNumber && error.status!==401)$('#modal-content').innerHTML=`<h2>Не удалось загрузить участников</h2><p>${esc(error.message)}</p><button class="primary-button" data-participants="${id}">Повторить</button>`;
    }
  }
  async function handleClick(d) {
    if(d.achievementUser){
      openModal('<div class="loading-state">Загружаем награды…</div>','achievements');
      const sequence=detailNumber;
      try {
        const user=await Api.request(`/users/${d.achievementUser}/achievements`);
        if(sequence===detailNumber && state.me)$('#modal-content').innerHTML=`<div class="modal-kicker">ДОСТИЖЕНИЯ УЧАСТНИКА</div><h2 class="modal-heading">${esc(user.name)}</h2><p>${user.points} баллов за достижения</p><button class="primary-button" data-passport-user="${user.user_id}">Открыть паспорт активности</button>${stats(user)}${cards(user.achievements)}`;
      }catch(error){if(sequence===detailNumber && error.status!==401)$('#modal-content').innerHTML=`<h2>Не удалось загрузить достижения</h2><p>${esc(error.message)}</p>`;}
      return true;
    }
    if(d.attendance){
      await Api.request(`/events/${d.eventId}/attendance/${d.attendance}`,{method:'PUT',body:{attended:d.attended==='true'}});
      await refreshPersonal();
      await participants(d.eventId);
      toast(d.attended==='true'?'Посещение подтверждено. Достижения пересчитаны.':'Отметка снята. Рейтинг обновлён.');
      return true;
    }
    return false;
  }
  return {show,participants,handleClick};
})();
