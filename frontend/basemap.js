
window.Basemap = (() => {
  const credits = '<a href="https://openfreemap.org/" target="_blank" rel="noopener">OpenFreeMap</a> · <a href="https://openmaptiles.org/" target="_blank" rel="noopener">OpenMapTiles</a> · © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';
  function add(map) {
    let layer=null, notice=null, removed=false;
    function clearNotice(){if(notice){notice.remove();notice=null;}}
    function failed(){
      if(removed||notice)return;
      notice=L.control({position:'bottomleft'});
      notice.onAdd=()=>{
        const box=L.DomUtil.create('div','basemap-error');
        box.setAttribute('role','status');
        const label=document.createElement('span');
        label.textContent='Не удалось загрузить подложку карты. Проверь интернет и поддержку WebGL в браузере.';
        const retry=document.createElement('button');retry.type='button';retry.textContent='Повторить';
        retry.addEventListener('click',()=>{clearNotice();if(layer){map.removeLayer(layer);layer=null;}start();});
        box.append(label,retry);L.DomEvent.disableClickPropagation(box);L.DomEvent.disableScrollPropagation(box);return box;
      };
      notice.addTo(map);
    }
    function start(){
      if(!window.maplibregl||!L.maplibreGL){failed();return;}
      try{
        layer=L.maplibreGL({style:'/neutral-map.json',interactive:false,renderWorldCopies:false,
          attributionControl:{customAttribution:credits}});

        layer.on('add',()=>{
          const gl=layer.getMaplibreMap();
          gl.on('error',failed);
          gl.on('idle',()=>{if(gl.isStyleLoaded()&&gl.areTilesLoaded())clearNotice();});
        });
        layer.addTo(map);
      }catch(error){

        if(layer&&map.hasLayer(layer)){
          if(!layer.getMaplibreMap())layer.onRemove=()=>layer.getContainer()?.remove();
          map.removeLayer(layer);
        }
        layer=null;failed();
      }
    }
    map.on('unload',()=>{removed=true;clearNotice();});
    start();
  }
  return {add};
})();
