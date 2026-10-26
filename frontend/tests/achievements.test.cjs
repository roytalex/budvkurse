const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function controller(request,all=async()=>[]) {
  const elements=new Map();
  const context={window:{},state:{view:'achievements',page:1,me:{id:1}},detailNumber:0,
    esc:v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;'),
    $:selector=>{if(!elements.has(selector))elements.set(selector,{innerHTML:'',textContent:''});return elements.get(selector);},
    Api:{request,all,query:q=>new URLSearchParams(q).toString()},refreshPersonal:async()=>{},toast:()=>{}};
  context.openModal=html=>{context.detailNumber++;context.$('#modal-content').innerHTML=html;};
  vm.runInNewContext(fs.readFileSync(require.resolve('../achievements.js'),'utf8'),context);
  return {...context,context,subject:context.window.Achievements};
}
const mine={points:10,attendance_count:1,olympiad_count:0,earned_count:1,rank:1,achievements:[{code:'first_step',title:'Первый шаг',description:'Посети 1 мероприятие',metric:'attendance_count',progress:1,target:1,points:10,earned:true}]};

test('Достижения показывают серверные баллы, прогресс и правило подтверждения',async()=>{
  const app=controller(async()=>mine);
  await app.subject.show({aborted:false});
  const html=app.$('#achievements-panel').innerHTML;
  assert.match(html,/Получено/);assert.match(html,/value="1" max="1"/);assert.match(html,/подтверждает организатор/);
  assert.equal(app.$('#results-count').textContent,'Получено: 1 из 1');
});
test('Рейтинг экранирует имя участника и поддерживает страницы',async()=>{
  const app=controller(async path=>path.startsWith('/me/')?mine:{total:21,items:[{...mine,user_id:2,name:'<img src=x onerror=alert(1)>',rank:1}]});
  app.state.view='leaderboard';await app.subject.show({aborted:false});
  const html=app.$('#achievements-panel').innerHTML;
  assert.doesNotMatch(html,/<img/);assert.match(html,/&lt;img/);assert.match(html,/data-achievement-user="2"/);
  assert.match(app.$('#pagination').innerHTML,/data-page="2"/);
});
test('Устаревший ответ не отрисовывает достижения после перехода в другой раздел',async()=>{
  let finish;const app=controller(()=>new Promise(resolve=>finish=resolve));
  const job=app.subject.show({aborted:false});app.state.view='feed';finish(mine);await job;
  assert.doesNotMatch(app.$('#achievements-panel').innerHTML,/Первый шаг/);
});
test('Участники получают кнопку посещения после окончания, подтверждённую отметку можно снять',async()=>{
  const rows=[{user_id:2,status:'registered',participant_name:'Ученик',attended:false},{user_id:3,status:'registered',participant_name:'Второй',attended:true}];
  const app=controller(async()=>({id:5,title:'Проект',status:'published',organizer_id:1,ends_at:'2000-01-01T00:00:00Z'}),async()=>rows);
  await app.subject.participants('5');
  assert.match(app.$('#modal-content').innerHTML,/data-attended="true" >Посетил/);
  assert.match(app.$('#modal-content').innerHTML,/data-attended="false">Снять отметку/);
});
