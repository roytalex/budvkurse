const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const D=require('../event-utils.js');

test('Многодневное событие есть в каждом дне пересечения, но не после окончания в полночь',()=>{
  const event={starts_at:new Date(2030,10,10,15).toISOString(),ends_at:new Date(2030,10,13,0).toISOString()};
  assert.equal(D.occursOn(event,'2030-11-10'),true);
  assert.equal(D.occursOn(event,'2030-11-11'),true);
  assert.equal(D.occursOn(event,'2030-11-12'),true);
  assert.equal(D.occursOn(event,'2030-11-13'),false);
});
test('Месяц корректно переходит через год',()=>{
  const b=D.monthBounds(2030,11);
  assert.equal(new Date(b.date_from).getMonth(),11);
  assert.equal(new Date(b.date_to).getFullYear(),2031);
  assert.equal(new Date(b.date_to).getMonth(),0);
});
function client(fetch,initial={access_token:'old',refresh_token:'refresh'}){
  const storage=new Map(initial?[['vkurse-session-v2',JSON.stringify(initial)]]:[]);
  const context={window:{dispatchEvent(){}},sessionStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},fetch,FormData,URL,URLSearchParams,Event};
  vm.runInNewContext(fs.readFileSync(require.resolve('../api-client.js'),'utf8'),context);
  return context.window.Api;
}
const response=(status,data)=>({status,ok:status>=200&&status<300,json:async()=>data});
test('Одновременные 401 используют один refresh, а не два',async()=>{
  let refreshes=0;
  const api=client(async(url,options)=>{
    if(url.endsWith('/auth/refresh')){refreshes++;await new Promise(r=>setTimeout(r,5));return response(200,{access_token:'new',refresh_token:'rotated'});}
    return options.headers.Authorization==='Bearer new'?response(200,{ok:true}):response(401,{detail:'expired'});
  });
  const result=await Promise.all([api.request('/events'),api.request('/cities')]);
  assert.equal(refreshes,1);assert.ok(result.every(r=>r.ok));
});
test('При разрыве сети клиент сообщает ошибку и сохраняет сессию для повтора',async()=>{
  const api=client(async()=>{throw new TypeError('offline');});
  await assert.rejects(api.request('/events'),{status:0});assert.equal(api.hasSession(),true);
});
test('Завершение сессии не позволяет запоздалому запросу вернуть данные прошлого аккаунта',async()=>{
  let resolve;const api=client(()=>new Promise(r=>resolve=r));
  const pending=api.request('/me');api.clear();resolve(response(200,{name:'old-user'}));
  await assert.rejects(pending,{status:401});assert.equal(api.hasSession(),false);
});
test('Карта и календарь дочитывают все страницы, включая более 100 событий',async()=>{
  const api=client(async url=>{const page=Number(new URL('http://test'+url).searchParams.get('page'));return response(200,{page,limit:100,total:205,items:Array.from({length:page===3?5:100},(_,i)=>({id:(page-1)*100+i}))});});
  const items=await api.all('/events');assert.equal(items.length,205);assert.equal(items[204].id,204);
});
