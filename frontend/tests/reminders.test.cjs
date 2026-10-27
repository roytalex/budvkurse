const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

function setup(){
  const nodes={'#results-count':{},'#achievements-panel':{innerHTML:''}},badge={},pending=[],writes=[];
  let renders=0;
  const state={me:{id:1},view:'reminders',plans:[]};
  const ctx={window:{},document:{hidden:false,querySelectorAll:()=>[badge],addEventListener(){}},state,Set,AbortController,
    setTimeout:()=>1,clearTimeout(){},toast(){},dt:x=>x,esc:x=>String(x).replaceAll('<','&lt;'),$:s=>nodes[s],
    Api:{all:()=>new Promise(resolve=>pending.push(resolve)),request:async(path,data)=>{writes.push({path,data});}},
    openModal:()=>renders++};
  vm.runInNewContext(fs.readFileSync(require.resolve('../reminders.js'),'utf8'),ctx);
  return {api:ctx.window.Reminders,state,pending,nodes,badge,writes};
}
const row={event:{id:5,title:'<img src=x onerror=evil()>',starts_at:'2030-10-20T12:00:00Z'},reminder_at:'2030-10-20T11:00:00Z',unread:true,read:false};
test('Напоминания экранируют название, показывают время и отправляют точную версию даты при прочтении',async()=>{
  const a=setup(),job=a.api.show(new AbortController().signal);a.pending.shift()([row]);await job;
  assert.ok(a.nodes['#achievements-panel'].innerHTML.includes('&lt;img'));assert.equal(a.badge.textContent,1);
  await a.api.read(5);assert.equal(a.writes[0].path,'/me/reminders/5/read');assert.equal(a.writes[0].data.body.starts_at,row.event.starts_at);assert.equal(a.badge.hidden,true);
});
test('Запоздалый ответ напоминаний не раскрывает данные после выхода из аккаунта',async()=>{
  const a=setup(),job=a.api.show(new AbortController().signal);a.api.stop();a.state.me={id:2};a.pending.shift()([row]);await job;
  assert.ok(!a.nodes['#achievements-panel'].innerHTML.includes('onerror'));assert.equal(a.badge.hidden,true);
});
test('Ответ напоминаний не заменяет другой раздел после навигации',async()=>{
  const a=setup(),job=a.api.show(new AbortController().signal);a.state.view='feed';a.nodes['#achievements-panel'].innerHTML='Другая страница';a.pending.shift()([row]);await job;
  assert.equal(a.nodes['#achievements-panel'].innerHTML,'Другая страница');
});
