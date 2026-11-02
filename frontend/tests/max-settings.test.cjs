const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function setup(native=true){
  const listeners={},requests=[],modals=[],toasts=[],state={me:{id:1}};
  let info={available:true,connected:false,enabled:false,bot_url:'https://max.ru/school_bot'};
  const context={URL,window:{MaxShell:{active:()=>native,initData:()=>native?'signed-init-data':''}},document:{addEventListener:(name,fn)=>listeners[name]=fn},state,
    Api:{request:async(path,options)=>{requests.push({path,options});if(path.endsWith('/connection/link')&&options?.method==='POST')return {url:'https://max.ru/school_bot?start=connect_'+ 'a'.repeat(32),command:'/connect '+ 'a'.repeat(32),expires_at:'2026-11-02T18:00:00Z'};if(options?.method==='POST')info={...info,connected:true,enabled:true};if(options?.method==='DELETE')info={...info,connected:false,enabled:false};return info;}},
    openModal:html=>modals.push(html),esc:x=>String(x).replaceAll('<','&lt;'),toast:x=>toasts.push(x)};
  vm.runInNewContext(fs.readFileSync(require.resolve('../max-settings.js'),'utf8'),context);
  const click=async action=>{const button={dataset:{maxConnection:action},disabled:false,isConnected:true};await listeners.click({target:{closest:()=>button}});assert.equal(button.disabled,false);};
  return {context,requests,modals,toasts,click};
}

test('MAX notifications require explicit consent and send signed initData, not a user id',async()=>{
  const a=setup();assert.equal(a.requests.length,0);await a.context.window.MaxSettings.open();assert.ok(a.modals.at(-1).includes('Разрешить напоминания'));
  await a.click('connect');const request=a.requests.find(r=>r.options?.method==='POST');
  assert.equal(request.path,'/integrations/max/connection');assert.equal(request.options.body.init_data,'signed-init-data');assert.equal(request.options.body.max_user_id,undefined);
  assert.ok(a.modals.at(-1).includes('MAX подключён'));
  await a.click('disconnect');assert.ok(a.requests.some(r=>r.options?.method==='DELETE'));
});

test('Ordinary browser offers bot link and cannot submit fabricated identity',async()=>{
  const a=setup(false);await a.context.window.MaxSettings.open();assert.ok(a.modals.at(-1).includes('https://max.ru/school_bot'));assert.ok(!a.modals.at(-1).includes('data-max-connection="connect"'));
  await a.click('connect');assert.ok(!a.requests.some(r=>r.options?.method==='POST'));assert.ok(a.toasts.at(-1).includes('Открой приложение'));
});

test('Late MAX status cannot open a previous account settings',async()=>{
  const a=setup();let resolve;a.context.Api.request=()=>new Promise(r=>resolve=r);
  const job=a.context.window.MaxSettings.open();a.context.state.me={id:2};resolve({available:true});await job;assert.equal(a.modals.length,0);
});


test('Browser pairing creates a one-time link without enabling reminders before bot confirmation',async()=>{
  const a=setup(false);await a.context.window.MaxSettings.open();
  assert.ok(a.modals.at(-1).includes('data-max-connection="pair"'));
  await a.click('pair');
  assert.equal(a.requests.at(-1).path,'/integrations/max/connection/link');
  assert.ok(a.modals.at(-1).includes('Подключить напоминания'));
  assert.ok(a.modals.at(-1).includes('Не пересылай'));
  assert.ok(!a.toasts.includes('Напоминания MAX подключены'));
  await a.click('cancel-pair');
  assert.ok(a.requests.some(r=>r.path.endsWith('/connection/link')&&r.options?.method==='DELETE'));
});

test('A pairing link response is discarded after switching accounts',async()=>{
  const a=setup(false);let resolve;a.context.Api.request=()=>new Promise(r=>resolve=r);
  const job=a.click('pair');a.context.state.me={id:2};resolve({url:'https://max.ru/school_bot',command:'x'});
  await job;assert.equal(a.modals.length,0);
});
