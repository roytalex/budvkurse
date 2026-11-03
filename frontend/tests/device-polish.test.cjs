const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function harness(){
  const handlers={},root={dataset:{},style:{setProperty(k,v){this[k]=v;}}};
  let editing=false,focused=-1;
  const days=Array.from({length:30},(_,index)=>({focus(){focused=index;}}));
  const document={documentElement:root,activeElement:{matches:()=>editing},querySelector:()=>null,querySelectorAll:selector=>selector.startsWith('.month-day')?days:[],addEventListener:(type,fn)=>handlers[type]=fn};
  const viewport={height:844,scale:1,addEventListener:(type,fn)=>handlers['viewport-'+type]=fn};
  const window={innerHeight:844,visualViewport:viewport,addEventListener:(type,fn)=>handlers['window-'+type]=fn};
  vm.runInNewContext(fs.readFileSync(require.resolve('../device-polish.js'),'utf8'),{document,window,requestAnimationFrame:fn=>fn(),MutationObserver:class{observe(){}}});
  return {document,root,handlers,viewport,window,setEditing:value=>editing=value,focused:()=>focused,key(index,key,extra={}){let prevented=false;handlers.keydown({target:{closest:()=>days[index]},key,preventDefault(){prevented=true;},...extra});return prevented;}};
}

test('Calendar keyboard moves by day and week and stays inside the current month',()=>{
  const app=harness();
  assert.equal(app.key(0,'ArrowLeft'),true);assert.equal(app.focused(),0);
  app.key(3,'ArrowDown');assert.equal(app.focused(),10);
  app.key(29,'ArrowRight');assert.equal(app.focused(),29);
  app.key(14,'Home');assert.equal(app.focused(),0);
  app.key(14,'End');assert.equal(app.focused(),29);
  assert.equal(app.key(5,'Enter'),false);
  assert.equal(app.key(5,'ArrowRight',{ctrlKey:true}),false);
});

test('Bottom navigation yields space to an on-screen keyboard and returns after blur',()=>{
  const app=harness();
  app.setEditing(true);app.viewport.height=450;app.handlers['viewport-resize']();
  assert.equal(app.root.dataset.keyboard,'open');
  app.setEditing(false);app.handlers.focusout();
  assert.equal(app.root.dataset.keyboard,'closed');
});

test('Pinch zoom does not masquerade as a keyboard',()=>{
  const app=harness();app.setEditing(true);app.viewport.height=400;app.viewport.scale=2;
  app.handlers['viewport-resize']();assert.equal(app.root.dataset.keyboard,'closed');
});

test('Dialog follows keyboard height and visual viewport offset',()=>{
  const app=harness();app.setEditing(true);app.viewport.height=380;app.viewport.offsetTop=44;
  app.handlers['viewport-resize']();
  assert.equal(app.root.style['--visible-height'],'380px');
  assert.equal(app.root.style['--visible-top'],'44px');
  app.viewport.offsetTop=72;app.handlers['viewport-scroll']();
  assert.equal(app.root.style['--visible-top'],'72px');
  app.setEditing(false);app.viewport.height=844;app.viewport.offsetTop=0;app.handlers.focusout();
  assert.equal(app.root.style['--visible-height'],'844px');
  assert.equal(app.root.style['--visible-top'],'0px');
});
test('Zoom does not shrink the dialog to a pinched viewport',()=>{
  const app=harness();app.viewport.height=300;app.viewport.scale=2;app.handlers['viewport-resize']();
  assert.equal(app.root.style['--visible-height'],'844px');
});

test('Focused input scrolls above the keyboard without moving the page',()=>{
  const app=harness();app.setEditing(true);
  const scroller={scrollTop:0,getBoundingClientRect:()=>({top:0,bottom:400})};
  app.document.activeElement.closest=()=>scroller;
  app.document.activeElement.getBoundingClientRect=()=>({top:380,bottom:430});
  app.viewport.height=400;app.handlers['viewport-resize']();
  assert.equal(scroller.scrollTop,54);
});