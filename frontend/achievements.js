'use strict';
window.Achievements = (() => {
  function cards(items) {
    return `<div class="achievement-grid">${items.map(a=>`<article class="achievement-card ${a.earned?'earned':''}"><div class="achievement-top"><span class="achievement-symbol" aria-hidden="true"><svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M8 3h8v7a4 4 0 0 1-8 0zM8 5H4v3a4 4 0 0 0 4 4m8-7h4v3a4 4 0 0 1-4 4M12 14v6M7 21h10"/></svg></span><span class="achievement-label">${a.earned?'Получено':'Впереди'}</span></div><h3>${esc(a.title)}</h3><p>${esc(a.description)}</p><div class="achievement-progress"><span>${a.progress} / ${a.target}</span><b>+${a.points} баллов</b></div><progress value="${a.progress}" max="${a.target}" aria-label="${esc(a.title)}: ${a.progress} из ${a.target}"></progress></article>`).join('')}</div>`;
  }
  function stats(data) {
    return `<div class="achievement-stats"><div><strong>${data.attendance_count}</strong><span>Посещено событий</span></div><div><strong>${data.olympiad_count}</strong><span>Из них олимпиад</span></div><div><strong>${data.earned_count}</strong><span>Достижений</span></div><div><strong>${data.rank?('#'+data.rank):'-'}</strong><span>Место в рейтинге</span></div></div>`;
  }
  function hero(data) {
    return `<div class="collection-hero"><div><span class="editorial-kicker">КОЛЛЕКЦИЯ ТВОЕГО ОПЫТА</span><h2>Каждый шаг<br><em>имеет значение.</em></h2><p>Здесь - то, что ты уже попробовал.<br>И то, что ещё впереди.</p><button class="primary-button" data-view="leaderboard">К общему рейтингу </button></div><div class="collection-art"><span class="collection-points"><b>${data.points}</b><small>баллов за достижения</small></span></div></div>`;
  }
  function podium(items,page){
    if(page!==1||!items.length)return '';
    const leaders=items.filter(u=>u.rank<=3).slice(0,3);
    if(!leaders.length)return '';
    return `<section class="podium-section" aria-label="Лидеры рейтинга"><div class="editorial-section-heading"><span>НА ВЕРШИНЕ</span><h2>Вдохновляют действовать</h2></div><div class="podium-grid" data-count="${leaders.length}">${leaders.map((u,i)=>`<button class="podium-card ${u.rank===1?'champion':''}" data-achievement-user="${u.user_id}"><span class="podium-rank">МЕСТО ${u.rank}</span><span class="podium-initial" aria-hidden="true">${esc(u.name.slice(0,1).toUpperCase())}</span><b>${esc(u.name)}</b><span class="podium-score">${u.points}<small>баллов</small></span><span class="podium-visits">${u.attendance_count} событий · ${u.earned_count} наград</span><span class="podium-open">Паспорт участника </span></button>`).join('')}</div></section>`;
  }
  function boardHtml(mine,board,page){
    const rows=board.items.map(u=>`<button class="leaderboard-row ${u.user_id===state.me.id?'is-me':''}" data-achievement-user="${u.user_id}" role="listitem" aria-label="${esc(u.name)}, место ${u.rank}, ${u.points} баллов"><span class="leaderboard-rank ${u.rank<=3?'top-rank':''}">${u.rank}</span><span class="leaderboard-avatar" aria-hidden="true">${esc(u.name.slice(0,1).toUpperCase())}</span><span class="leaderboard-person"><b>${esc(u.name)}${u.user_id===state.me.id?' <small>Это ты</small>':''}</b><span>Событий: ${u.attendance_count} · Олимпиад: ${u.olympiad_count} · Наград: ${u.earned_count}</span></span><span class="leaderboard-points"><b>${u.points}</b><small>баллов</small></span></button>`).join('');
    return `<div class="ranking-stage"><div><span class="editorial-kicker">ОТ ИНТЕРЕСА К РЕЗУЛЬТАТУ</span><h2>Твои действия.<br><em>Твои достижения.</em></h2><p>За каждым баллом - событие,<br>на котором ты действительно был.</p><span class="ranking-total">${board.total} участников в общем зачёте</span></div><div class="ranking-art" role="img" aria-label="Школьники и преподаватель"></div></div><div class="ranking-layout"><div class="ranking-main">${podium(board.items,page)}<div class="editorial-section-heading"><span>ОБЩИЙ ЗАЧЁТ</span><h2>Каждое участие считается</h2></div>${rows?`<div class="ranking-table-head"><span>Место / Участник</span><span>Баллы</span></div><div class="leaderboard" role="list" aria-label="Участники рейтинга">${rows}</div>`:'<div class="empty-state"><h3>Первое место пока свободно</h3><p>После первого подтверждённого посещения участник появится здесь.</p><button class="primary-button" data-view="feed">Найти мероприятие</button></div>'}</div><aside class="ranking-aside"><div class="my-standing"><span class="editorial-kicker">ТВОЙ РЕЗУЛЬТАТ</span><strong>${mine.rank?'#'+mine.rank:'-'}</strong><p>${mine.rank?'место в общем рейтинге':'Первое событие - первый шаг'}</p><div class="standing-metrics"><span><b>${mine.points}</b>баллов</span><span><b>${mine.earned_count}</b>наград</span></div><button class="primary-button" data-view="achievements">Мои достижения </button><button class="text-button" data-view="passport">Паспорт активности </button></div><div class="ranking-rules"><span>КАК ЭТО РАБОТАЕТ</span><p>Посещай события. Организатор подтверждает участие, а достижения приносят баллы.</p><p>При равных баллах сравниваем число посещений. Одинаковый результат - одинаковое место.</p><button class="round-link" data-view="schoolboard"><span>Рейтинг школ</span></button></div></aside></div>`;
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
    panel.innerHTML=boardHtml(mine,board,page);
    $('#pagination').innerHTML=board.total>20?`<button data-page="${page-1}" ${page===1?'disabled':''}> Назад</button><span>${page} / ${Math.ceil(board.total/20)}</span><button data-page="${page+1}" ${page*20>=board.total?'disabled':''}>Дальше </button>`:'';
  }
  async function participants(id) {
    openModal('<div class="loading-state">Загружаем участников…</div>','participants');
    const sequence=detailNumber;
    try {
      const [event, rows] = await Promise.all([Api.request('/events/'+id),Api.all(`/events/${id}/registrations`)]);
      if(sequence!==detailNumber || !state.me)return;
      const ended=event.status==='published' && new Date(event.ends_at)<=new Date();
      $('#modal-content').innerHTML=`<div class="modal-kicker">ПОСЕЩЕНИЯ И ДОСТИЖЕНИЯ</div><h2 class="modal-heading">Участники</h2><p>${esc(event.title)}</p><p class="form-hint">${ended?'Отметь тех, кто действительно посетил мероприятие. Ошибочную отметку можно снять.':'Подтвердить посещение можно после окончания опубликованного мероприятия.'} Записано: ${rows.filter(x=>x.status==='registered').length}.</p><button class="primary-button" data-scanner="${id}">Сканировать QR участника</button>${rows.map(u=>`<div class="attendance-row"><div><b>${esc(u.participant_name||'Участник '+u.user_id)}</b><small>${u.grade?u.grade+' класс · ':''}${u.attended?'Посещение подтверждено':u.status==='registered'?'Записан':'Отменил запись'}</small></div>${u.attended?`<button class="secondary-button" data-attendance="${u.user_id}" data-event-id="${id}" data-attended="false">Снять отметку</button>`:u.status==='registered'?`<button class="${ended?'primary':'secondary'}-button" data-attendance="${u.user_id}" data-event-id="${id}" data-attended="true" ${!ended||u.user_id===state.me.id||u.user_id===event.organizer_id?'disabled':''}>Посетил</button>`:''}</div>`).join('')||'<div class="empty-state"><h3>Участников пока нет</h3><p>Здесь появятся пользователи, записавшиеся через сайт.</p></div>'}`;
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
