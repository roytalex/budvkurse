const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
function harness(){
  const timers=new Map(),frames=new Map(),events={},controls=[],layers=[];let next=1,observer;
  function element(){return {dataset:{},children:[],clientWidth:320,clientHeight:290,setAttribute(k,v){this[k]=v;},append(...items){this.children.push(...items);},addEventListener(k,fn){this[k]=fn;}};}
  const container=element();
  const map={getContainer:()=>container,on:(key,fn)=>events[key]=fn,invalidateSize(){},hasLayer:layer=>layer.added,removeLayer(layer){layer.added=false;layer.removed=true;}};
  const L={DomUtil:{create:element},DomEvent:{disableClickPropagation(){},disableScrollPropagation(){}},control:()=>({addTo(){this.box=this.onAdd();controls.push(this);},remove(){this.removed=true;}}),maplibreGL:options=>{
    const glEvents={},gl={on:(key,fn)=>glEvents[key]=fn,isStyleLoaded:()=>true,areTilesLoaded:()=>true,resize(){this.resized=true;},triggerRepaint(){}};
    const layer={options,gl,glEvents,on(key,fn){this[key]=fn;return this;},getMaplibreMap:()=>gl,addTo(){this.added=true;this.add();}};layers.push(layer);return layer;
  }};
  const window={maplibregl:{},devicePixelRatio:3,ResizeObserver:true};
  vm.runInNewContext(fs.readFileSync(require.resolve('../basemap.js'),'utf8'),{window,L,document:{createElement:element},ResizeObserver:class{constructor(fn){observer=this;this.callback=fn;}observe(){}disconnect(){this.disconnected=true;}},setTimeout(fn){const id=next++;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id),requestAnimationFrame(fn){const id=next++;frames.set(id,fn);return id;},cancelAnimationFrame:id=>frames.delete(id)});
  window.Basemap.add(map);
  return {container,layers,controls,timers,events,observer,frames};
}
test('Map load clears watchdog; retina rendering is bounded',()=>{
  const a=harness();assert.equal(a.container.dataset.basemapState,'loading');assert.equal(a.layers[0].options.pixelRatio,2);
  a.layers[0].glEvents.load();assert.equal(a.container.dataset.basemapState,'ready');assert.equal(a.timers.size,0);
});
test('A stalled map offers retry and discards the previous renderer',()=>{
  const a=harness();[...a.timers.values()][0]();assert.equal(a.container.dataset.basemapState,'error');
  a.controls[0].box.children[1].click();assert.equal(a.layers.length,2);assert.equal(a.layers[0].removed,true);
  a.layers[1].glEvents.idle();assert.equal(a.container.dataset.basemapState,'ready');
});
test('Lost context shows recovery, resizing repaints, closing cleans watchers',()=>{
  const a=harness();a.layers[0].glEvents.webglcontextlost();assert.equal(a.container.dataset.basemapState,'error');
  a.observer.callback();[...a.frames.values()][0]();assert.equal(a.layers[0].gl.resized,true);
  a.events.unload();assert.equal(a.observer.disconnected,true);assert.equal(a.timers.size,0);assert.equal(a.frames.size,0);
});
