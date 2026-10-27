const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function app(){
  let click,expire,closed,focused=0;
  const classes=new Set();
  const menu={open:false,addEventListener:(name,fn)=>{if(name==='close')closed=fn;},showModal(){this.open=true;},close(){this.open=false;closed();},contains:element=>!!element.inside};
  const opener={focus(){focused++;},closest:selector=>selector==='[data-nav-open]'?opener:null};
  const document={querySelector:()=>menu,body:{classList:{add:x=>classes.add(x),remove:x=>classes.delete(x)}},addEventListener:(name,fn)=>{if(name==='click')click=fn;}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../editorial.js'),'utf8'),{document,window:{addEventListener:(name,fn)=>{if(name==='session-expired')expire=fn;}}});
  return {menu,opener,click:target=>click({target}),classes,expire,focused:()=>focused};
}

test('Все разделы открываются в диалоге, закрытие возвращает фокус и прокрутку',()=>{
  const a=app();a.click(a.opener);assert.equal(a.menu.open,true);assert.equal(a.classes.has('navigation-open'),true);
  a.menu.close();assert.equal(a.classes.has('navigation-open'),false);assert.equal(a.focused(),1);
});
test('Выбор раздела и истечение сессии закрывают меню',()=>{
  const a=app();a.click(a.opener);
  a.click({inside:true,closest:selector=>selector.startsWith('[data-view]')?{}:null});
  assert.equal(a.menu.open,false);
  a.click(a.opener);a.expire();assert.equal(a.menu.open,false);assert.equal(a.classes.size,0);
});
