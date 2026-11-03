const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

function app({inside=true,payload='calendar'}={}){
  const events={},listeners={},actions=[];
  const root={dataset:{},style:{setProperty(){}}};
  const main={dataset:{view:'feed'}},nav={open:false,close(){this.open=false;actions.push('nav-close');}},modal={open:false};
  const bridge=inside?{initData:'not-used-for-authentication',initDataUnsafe:{user:{id:999,role:'admin'},start_param:payload},ready(){actions.push('ready');},BackButton:{show(){},hide(){},onClick(fn){events.back=fn;}},openLink(url){actions.push(url);},downloadFile(url,name){actions.push({url,name});return Promise.resolve({status:'downloading'});}}:null;
  const window={WebApp:bridge,addEventListener:(name,fn)=>events[name]=fn,innerHeight:800};
  const document={documentElement:root,body:{},head:{append(){actions.push('sdk');}},addEventListener:(name,fn)=>listeners[name]=fn,
    querySelector:s=>s==='#main'?main:s==='#nav-dialog'?nav:s==='#modal'?modal:null};
  const context={window,document,URL,URLSearchParams,setTimeout:()=>0,location:{search:inside?'?max=1':'',hash:'',origin:'https://school.example',href:'https://school.example/'},
    MutationObserver:class{observe(){}},navigate:async x=>actions.push('view:'+x),openEvent:async x=>actions.push('event:'+x),closeModal:()=>{modal.open=false;actions.push('modal-close');},toast(){}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../max-shell.js'),'utf8'),context);
  return {api:window.MaxShell,events,listeners,actions,root,nav,modal,main};
}
test('MAX launch only navigates after normal account login; unsafe user never authenticates',async()=>{
  const a=app();assert.ok(!a.actions.includes('view:calendar'));a.events['app-session-ready']();await Promise.resolve();assert.ok(a.actions.includes('view:calendar'));assert.equal(a.root.dataset.miniapp,'max');
});
test('Launch payload only accepts known sections or numeric event IDs',()=>{
  const a=app();for(const value of ['https://evil.example','admin','event_-1','event_0','javascript:alert(1)',{},'a'.repeat(513)])assert.equal(a.api.launchTarget(value),null);
  assert.equal(a.api.launchTarget('event_123').event,123);
  assert.equal(a.api.launchTarget('manage').view,'manage');
});
test('Native back closes menu, then dialog, then returns to feed',async()=>{
  const a=app();a.events['app-session-ready']();a.nav.open=true;await a.events.back();assert.ok(a.actions.includes('nav-close'));a.modal.open=true;await a.events.back();assert.ok(a.actions.includes('modal-close'));await a.events.back();assert.ok(a.actions.includes('view:feed'));
});
test('Normal browser does not load MAX or alter its navigation',()=>{
  const a=app({inside:false});assert.equal(a.api.active(),false);assert.equal(a.root.dataset.miniapp,undefined);assert.deepEqual(a.actions,[]);
});
test('Native download rejects non-HTTPS, external host and arbitrary local routes',async()=>{
  const a=app();for(const url of ['http://school.example/api/v1/exports/certificate','https://evil.example/api/v1/exports/certificate','https://school.example/api/v1/me'])await assert.rejects(a.api.download(url,'file.html'));
  await a.api.download('https://school.example/api/v1/exports/certificate?token=test','certificate.html');assert.equal(a.actions.at(-1).name,'certificate.html');
});
