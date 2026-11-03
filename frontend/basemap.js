window.Basemap = (() => {
  const credits = '<a href="https://openfreemap.org/" target="_blank" rel="noopener">OpenFreeMap</a> · <a href="https://openmaptiles.org/" target="_blank" rel="noopener">OpenMapTiles</a> · © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';
  function add(map) {
    let layer=null, notice=null, removed=false, deadline=null, observer=null, frame=0;
    const container=map.getContainer();
    function state(value){container.dataset.basemapState=value;container.setAttribute('aria-busy',String(value==='loading'));}
    function clearNotice(){if(notice){notice.remove();notice=null;}}
    function ready(){if(removed)return;clearTimeout(deadline);clearNotice();state('ready');}
    function disposeLayer(){
      if(!layer)return;
      if(map.hasLayer(layer)){
        if(!layer.getMaplibreMap())layer.onRemove=()=>layer.getContainer()?.remove();
        map.removeLayer(layer);
      }
      layer=null;
    }
    function failed(){
      if(removed)return;
      clearTimeout(deadline);state('error');
      if(notice)return;
      notice=L.control({position:'bottomleft'});
      notice.onAdd=()=>{
        const box=L.DomUtil.create('div','basemap-error');box.setAttribute('role','status');
        const label=document.createElement('span');
        label.textContent='Карта не загрузилась. Повтори загрузку. Место также можно выбрать через поиск адреса.';
        const retry=document.createElement('button');retry.type='button';retry.textContent='Повторить';
        retry.addEventListener('click',()=>{clearNotice();disposeLayer();start();});
        box.append(label,retry);L.DomEvent.disableClickPropagation(box);L.DomEvent.disableScrollPropagation(box);return box;
      };
      notice.addTo(map);
    }
    function resize(){
      if(removed||!container.clientWidth||!container.clientHeight)return;
      map.invalidateSize({pan:false});
      const gl=layer?.getMaplibreMap();
      if(gl){gl.resize();gl.triggerRepaint();}
    }
    function queueResize(){cancelAnimationFrame(frame);frame=requestAnimationFrame(resize);}
    function start(){
      if(removed)return;
      state('loading');clearTimeout(deadline);deadline=setTimeout(failed,15000);
      if(!window.maplibregl||!L.maplibreGL){failed();return;}
      try{
        layer=L.maplibreGL({style:'/neutral-map.json',interactive:false,renderWorldCopies:false,
          pixelRatio:Math.min(window.devicePixelRatio||1,2),attributionControl:{customAttribution:credits}});
        layer.on('add',()=>{
          const gl=layer.getMaplibreMap();
          gl.on('error',failed);
          gl.on('load',ready);
          gl.on('webglcontextlost',failed);
          gl.on('webglcontextrestored',()=>{queueResize();});
          gl.on('idle',()=>{if(gl.isStyleLoaded()&&gl.areTilesLoaded())ready();});
        });
        layer.addTo(map);
      }catch{disposeLayer();failed();}
    }
    if(window.ResizeObserver){observer=new ResizeObserver(queueResize);observer.observe(container);}
    map.on('resize',queueResize);
    map.on('unload',()=>{removed=true;clearTimeout(deadline);cancelAnimationFrame(frame);observer?.disconnect();clearNotice();});
    start();
  }
  return {add};
})();
