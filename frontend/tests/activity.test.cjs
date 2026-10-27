const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

function setup(request=async()=>({})){
  const elements=new Map();let stopped=0;
  const context={window:{},Date,Map,Promise,Number,String,Math,URL,Uint8ClampedArray,FormData,
    setTimeout:()=>1,clearTimeout(){},cancelAnimationFrame(){},requestAnimationFrame:()=>1,
    state:{view:'passport',page:1,me:{id:1,role:'student'}},detailNumber:0,
    esc:v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;'),
    dt:v=>String(v),categories:{project:'Проекты'},
    $:s=>{if(!elements.has(s))elements.set(s,{innerHTML:'',textContent:'',hidden:false,play:async()=>{}});return elements.get(s);},
    Api:{request,query:q=>new URLSearchParams(q).toString()},toast(){},loadView:async()=>{},
    navigator:{mediaDevices:{getUserMedia:async()=>({getTracks:()=>[{stop(){stopped++;}}]})}},
  };
  context.openModal=(html)=>{context.window.Activity.stop();context.detailNumber++;context.$('#modal-content').innerHTML=html;};
  vm.runInNewContext(fs.readFileSync(require.resolve('../activity.js'),'utf8'),context);
  return {context,subject:context.window.Activity,element:context.$,stopped:()=>stopped};
}
const passport={summary:{name:'<script>alert(1)</script>',attendance_count:1,olympiad_count:0,points:10,achievements:[]},interests:['Код'],visits:{items:[{event_id:2,title:'Первое событие',category:'project',ends_at:'2026-01-01'}],total:1}};

test('Паспорт экранирует имя и предлагает сертификат собственного посещения',async()=>{
  const app=setup(async()=>passport);await app.subject.show({aborted:false});
  const html=app.element('#achievements-panel').innerHTML;
  assert.match(html,/data-certificate="2"/);assert.doesNotMatch(html,/<script>/);assert.match(html,/&lt;script&gt;/);
});
test('Ответ паспорта после перехода в другой раздел не отрисовывается',async()=>{
  let resolve;const app=setup(()=>new Promise(r=>resolve=r));const pending=app.subject.show({aborted:false});
  app.context.state.view='feed';resolve(passport);await pending;
  assert.doesNotMatch(app.element('#achievements-panel').innerHTML,/ПАСПОРТ АКТИВНОСТИ/);
});
test('Поздно полученная камера отключается после закрытия сканера',async()=>{
  let resolve,stops=0;const app=setup();app.context.navigator.mediaDevices.getUserMedia=()=>new Promise(r=>resolve=r);
  const pending=app.subject.handleClick({scanCamera:''});app.subject.stop();
  resolve({getTracks:()=>[{stop:()=>stops++}]});await pending;assert.equal(stops,1);
});
test('Открытая камера выключается при закрытии модального окна',async()=>{
  const app=setup();await app.subject.handleClick({scanCamera:''});app.subject.stop();assert.equal(app.stopped(),1);
});
test('Челленджи показывают серверный месяц и завершённый значок',async()=>{
  const app=setup(async()=>({month:'2026-10',history:[],challenges:[{title:'Три события',description:'Посети 3 события',earned:true,progress:3,target:3}]}));
  app.context.state.view='challenges';await app.subject.show({aborted:false});
  assert.match(app.element('#achievements-panel').innerHTML,/Значок получен/);assert.match(app.element('#achievements-panel').innerHTML,/2026-10/);
});
