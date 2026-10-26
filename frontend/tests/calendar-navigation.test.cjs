const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const EventDates=require('../event-utils.js');


function controller(Api={}){
  const context={window:{addEventListener(){}},document:{querySelector:()=>({value:''})},EventDates,Api,Date};
  const source=fs.readFileSync(require.resolve('../app-live.js'),'utf8').split("document.addEventListener('click',async event=>")[0];
  vm.runInNewContext(source+`;loadView=async()=>{};navigate=async v=>{state.view=v;};toast=()=>{};globalThis.subject={state,handleClick};`,context);
  context.subject.state.me={id:1};return context.subject;
}
test('Переход из карточки декабря сбрасывает октябрьские фильтры и выбирает 31 декабря',async()=>{
  const {state,handleClick}=controller();state.year=2026;state.month=9;state.filters={date:'2026-10-23'};state.city='2';state.calendarMode='mine';
  await handleClick({dataset:{showCalendar:'2026-12-31T12:00:00Z',calendarTarget:'all'}});
  assert.equal(state.view,'calendar');assert.equal(state.year,2026);assert.equal(state.month,11);assert.equal(state.day,'2026-12-31');
  assert.equal(state.calendarMode,'all');assert.equal(state.city,'');assert.equal(Object.keys(state.filters).length,0);
});
test('Ближайшее событие ищется за пределами открытого месяца и учитывает город',async()=>{
  let sent;const {state,handleClick}=controller({query:q=>{sent=q;return '';},request:async()=>({items:[{starts_at:'2090-12-31T12:00:00Z'}]})});
  state.view='calendar';state.city='3';state.filters={date:'2026-10-23'};
  await handleClick({dataset:{action:'calendar-nearest'}});
  assert.equal(sent.date_to,undefined);assert.equal(sent.city_id,'3');assert.equal(sent.sort,'date');assert.equal(state.year,2090);assert.equal(state.month,11);
});
test('Ответ поиска не возвращает пользователя в календарь после перехода в другой раздел',async()=>{
  let finish;const {state,handleClick}=controller({query:()=>'',request:()=>new Promise(r=>finish=r)});
  state.view='calendar';state.year=2026;const job=handleClick({dataset:{action:'calendar-nearest'}});state.view='feed';
  finish({items:[{starts_at:'2090-12-31T12:00:00Z'}]});await job;assert.equal(state.view,'feed');assert.equal(state.year,2026);
});
test('Нейтральная карта не содержит подписей, политических границ и ссылок на CARTO',()=>{
  const style=JSON.parse(fs.readFileSync(require.resolve('../neutral-map.json'),'utf8'));
  assert.ok(style.layers.length>0);assert.ok(style.layers.every(l=>l.type!=='symbol'&&l['source-layer']!=='boundary'));
  assert.equal(style.glyphs,undefined);assert.equal(style.sprite,undefined);
  for(const name of ['event-map.js','location-search.js','basemap.js'])assert.doesNotMatch(fs.readFileSync(require.resolve('../'+name),'utf8'),/cartocdn|carto\.com/);
});
