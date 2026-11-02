const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function setup(href){
  let ready;const calls=[],changes=[];
  const context={URL,location:{href},window:{addEventListener:(event,fn)=>{assert.equal(event,'app-session-ready');ready=fn;}},history:{replaceState:(_,__,url)=>{changes.push(url);context.location.href=new URL(url,href).href;}},openEvent:async id=>calls.push(id),toast:()=>{}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../event-link.js'),'utf8'),context);
  return {calls,changes,ready};
}
test('An event from a reminder opens only after normal sign-in and is consumed once',async()=>{
  const a=setup('https://example.org/?event=42#feed');assert.deepEqual(a.calls,[]);
  await a.ready();await a.ready();assert.deepEqual(a.calls,[42]);assert.deepEqual(a.changes,['/#feed']);
});
test('Invalid event targets never open cards or change the URL',async()=>{
  for(const value of ['-1','0','javascript:alert(1)','1/../../secret','999999999999']){
    const a=setup('https://example.org/?event='+encodeURIComponent(value));await a.ready();assert.deepEqual(a.calls,[]);assert.deepEqual(a.changes,[]);
  }
});
