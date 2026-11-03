const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function app({saved='', reduced=false, storageFails=false, mobile=false}={}) {
  let clicked, changed, intersection, observed, cancelled=0, started=0;
  class Element {
    constructor(){this.children=[];this.parentElement={children:[this]};this.attrs={};this.symbol={};}
    querySelectorAll(){return [];}
    querySelector(){return this.symbol;}
    matches(){return true;}
    closest(){return this;}
    setAttribute(key,value){this.attrs[key]=value;}
    getAttribute(key){return this.attrs[key];}
    animate(){started++;return {cancel(){cancelled++;this.oncancel?.();}};}
  }
  const button=new Element(), body=new Element(), root={dataset:{}};
  const media={matches:reduced,addEventListener(_,fn){changed=fn;}};
  const storage={getItem(){if(storageFails)throw Error('blocked');return saved;},setItem(_,value){if(storageFails)throw Error('blocked');saved=value;}};
  class IntersectionObserver {
    constructor(callback){intersection=callback;}
    observe(element){observed=element;}
    unobserve(){}
  }
  class MutationObserver {observe(){}}
  const context={window:{matchMedia:query=>query.includes('max-width')?{matches:mobile,addEventListener(){}}:media,IntersectionObserver},IntersectionObserver,MutationObserver,Element,localStorage:storage,
    document:{body,documentElement:root,querySelectorAll:()=>[button],addEventListener(_,fn){clicked=fn;}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../cinematic.js'),'utf8'),context);
  return {root,button,media,click:()=>clicked({target:button}),change:()=>changed(),enter:()=>intersection([{target:observed,isIntersecting:true}]),cancelled:()=>cancelled,started:()=>started,saved:()=>saved};
}

test('Настройка уменьшения движения останавливает анимации и отключает переключатель',()=>{
  const a=app();a.enter();assert.equal(a.started(),1);
  a.media.matches=true;a.change();assert.equal(a.cancelled(),1);
  assert.equal(a.root.dataset.motion,'off');assert.equal(a.button.disabled,true);
});
test('Выбор без анимаций сохраняется и применяется при следующем открытии',()=>{
  const a=app();a.click();assert.equal(a.saved(),'off');assert.equal(a.root.dataset.motion,'off');
  const b=app({saved:a.saved()});b.enter();assert.equal(b.started(),0);assert.equal(b.button.attrs['aria-pressed'],'false');
});
test('Недоступное хранилище не ломает переключение анимаций',()=>{
  const a=app({storageFails:true});assert.equal(a.root.dataset.motion,'on');
  a.click();assert.equal(a.root.dataset.motion,'off');a.click();assert.equal(a.root.dataset.motion,'on');
});

test('Мобильный экран показывает контент без декоративных анимаций',()=>{
  const a=app({mobile:true,saved:'on'});a.enter();
  assert.equal(a.started(),0);assert.equal(a.root.dataset.motion,'off');
});
