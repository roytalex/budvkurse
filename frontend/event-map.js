                                                                 
window.EventMap = (() => {
  let pickerObserver=null,pickerFrame=0;
  let map=null,layer=null,picker=null,pickerMarker=null,controller=null,sequence=0,timer,cityKey=null;
  const markers=new Map();let positionCircle=null;
  const bounds=[[-85.05112878,-180],[85.05112878,180]];
  function addTiles(instance){Basemap.add(instance);}
  function constrain(instance){const size=instance.getSize();if(!size.x||!size.y)return;instance.setMinZoom(Math.max(1,Math.ceil(Math.log2(Math.max(size.x,size.y)/256)*4)/4));instance.panInsideBounds(bounds,{animate:false});}
  function options(){return {scrollWheelZoom:false,minZoom:1,maxBounds:bounds,maxBoundsViscosity:1,worldCopyJump:false,bounceAtZoomLimits:false,zoomSnap:.25,maxZoom:19};}
  function create(){if(map)return true;if(!window.L){$('#map-list').innerHTML='<p>Карта недоступна. Открой ленту событий.</p>';return false;}map=L.map('event-map',options()).setView([55.75,37.62],10);addTiles(map);layer=L.layerGroup().addTo(map);map.attributionControl.setPrefix(false);map.zoomControl.setPosition('topright');map.on('moveend',schedule);map.on('resize',()=>constrain(map));L.control.scale({imperial:false}).addTo(map);wheelHint(map);return true;}
  function schedule(){clearTimeout(timer);if(state.view==='map'&&state.me)timer=setTimeout(load,180);}
  async function load(){
    if(!map||state.view!=='map'||!state.me)return;
    const current=++sequence;controller?.abort();controller=new AbortController();
    $('#map-summary').textContent='Обновляем события…';
    const b=map.getBounds();const query={...filtersQuery(),west:Math.max(-180,b.getWest()),east:Math.min(180,b.getEast()),south:Math.max(-90,b.getSouth()),north:Math.min(90,b.getNorth())};
    try{
      const events=await Api.all('/events/map',query,controller.signal);
      if(current!==sequence||state.view!=='map'||!state.me)return;
      layer.clearLayers();markers.clear();
      const groups=new Map();for(const e of events){const key=`${e.latitude},${e.longitude}`;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(e);}
      let count=0;
      for(const group of groups.values()){
        const e=group[0],n=++count;
        const marker=L.marker([e.latitude,e.longitude],{title:group.map(x=>x.title).join(', '),icon:L.divIcon({className:'event-map-marker',html:`<span class="pin-bubble ${group.every(x=>x.school_id)?'school-pin':''}"><b class="pin-digit">${n}</b>${group.length>1?`<i>${group.length}</i>`:''}</span>`,iconSize:[40,45],iconAnchor:[20,42]})}).addTo(layer);
        marker.bindPopup(`<div class="map-popup">${group.map(x=>`<div class="popup-event"><b>${esc(x.title)}</b><p>${dateRange(x)}</p><button class="primary-button" data-event="${x.id}">Подробнее </button></div>`).join('')}</div>`,{maxWidth:300});
        marker.on('popupopen',()=>{marker.getPopup().getElement().querySelectorAll('[data-event]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();openEvent(button.dataset.event).catch(showError);}));});
        for(const x of group){markers.set(x.id,marker);x.mapNumber=n;}
        marker.on('click',()=>{$('#map-list').querySelectorAll('[data-map-row]').forEach(row=>row.classList.toggle('selected',group.some(x=>x.id===Number(row.dataset.mapRow))));$('#map-list').querySelector(`[data-map-row="${e.id}"]`)?.scrollIntoView({block:'nearest',behavior:'smooth'});});
      }
      $('#map-summary').textContent=`В этой области: ${events.length}`;$('#results-count').textContent=`На карте: ${events.length}`;
      $('#map-list').innerHTML=events.length?events.map(e=>`<article class="map-event-row" data-map-row="${e.id}"><span class="map-event-number ${e.school_id?'school-pin':''}">${e.mapNumber}</span><div><div class="map-event-kind">${esc(cityName(e.city_id))} · ${esc(e.school_id?schoolName(e.school_id):'Городская площадка')}</div><h3><button data-event="${e.id}">${esc(e.title)}</button></h3><p>${dateRange(e)}</p><p>${esc(e.address||e.place_name||'')}</p><button class="map-row-link" data-map-focus="${e.id}">Показать точку </button></div></article>`).join(''):'<div class="map-empty"><h3>В этой области пока нет событий</h3><p>Отдаляй карту или выбери другой город. Онлайн-события доступны в ленте.</p></div>';
    }catch(error){if(current!==sequence||error.name==='AbortError'||error.status===401)return;layer.clearLayers();markers.clear();$('#map-summary').textContent='Не удалось обновить карту';$('#map-list').innerHTML=`<div class="map-empty"><p>${esc(error.message)}</p><button data-action="refresh" class="secondary-button">Повторить</button></div>`;}
  }
  function city(){if(!create())return;const school=state.schools.find(x=>x.id===Number(state.school));const city=state.cities.find(x=>x.id===Number(state.city));const location=school?.latitude!=null?school:city;if(location)map.setView([Math.max(-85,Math.min(85,location.latitude)),location.longitude],school?.latitude!=null?13:10,{animate:false});else map.setView([55.75,37.62],4,{animate:false});schedule();}
  function show(){if(!create())return;requestAnimationFrame(()=>{if(state.view!=='map')return;map.invalidateSize();constrain(map);const key=state.city+':'+state.school;if(cityKey!==key){cityKey=key;city();}else schedule();});}
  function pause(){clearTimeout(timer);sequence++;controller?.abort();$('#map-panel').classList.remove('map-expanded');document.body.classList.remove('map-expanded-body');const button=$('[data-action="map-expand"]');if(button)button.textContent=' На весь экран';}
  function stop(){pause();layer?.clearLayers();markers.clear();cityKey=null;if(positionCircle){map.removeLayer(positionCircle);positionCircle=null;}closePicker();}
  function world(){if(!create())return;map.invalidateSize();map.fitWorld({animate:false});constrain(map);schedule();}
  function focus(lat,lng){if(!create())return;cityKey=state.city+':'+state.school;map.setView([lat,lng],14,{animate:false});schedule();}
  function select(id){const marker=markers.get(id);if(marker){map.panTo(marker.getLatLng());marker.openPopup();}}
  function closePicker(){pickerObserver?.disconnect();pickerObserver=null;cancelAnimationFrame(pickerFrame);pickerFrame=0;if(picker){picker.remove();picker=null;pickerMarker=null;}}
  function openPicker(event){
    closePicker();if(!$('#place-map'))return;
    try {
    if(!window.L)throw new Error('Map library unavailable');
    const city=state.cities.find(c=>c.id===Number($('#event-form').elements.city_id.value));const point=event.latitude!=null?[event.latitude,event.longitude]:city?[city.latitude,city.longitude]:[55.75,37.62];
    picker=L.map('place-map',options()).setView(point,event.latitude!=null?13:10);addTiles(picker);picker.attributionControl.setPrefix(false);
    wheelHint(picker);L.control.scale({imperial:false}).addTo(picker);
    picker.on('click',e=>{const form=$('#event-form');if(!form)return;form.elements.latitude.value=e.latlng.lat.toFixed(6);form.elements.longitude.value=e.latlng.lng.toFixed(6);pickerCoordinates();});
    pickerCoordinates();requestAnimationFrame(resizePicker);
    if(window.ResizeObserver){pickerObserver=new ResizeObserver(()=>{cancelAnimationFrame(pickerFrame);pickerFrame=requestAnimationFrame(resizePicker);});pickerObserver.observe($('#place-map'));}
    }catch{closePicker();$('#place-map').innerHTML='<div class="picker-recovery"><span>Карта не загрузилась. Повтори загрузку или выбери место через «Найти адрес».</span><button type="button" class="secondary-button" data-action="picker-retry">Повторить загрузку карты</button></div>';}
  }
  function retryPicker(){const form=$('#event-form');if(!form)return;const lat=form.elements.latitude.value,lng=form.elements.longitude.value;openPicker({latitude:lat!==''&&lng!==''?Number(lat):null,longitude:lat!==''&&lng!==''?Number(lng):null});}
  function resizePicker(){if(picker&&!$('#offline-fields')?.hidden){picker.invalidateSize();constrain(picker);}}
  function pickerCoordinates(){if(!picker)return;const form=$('#event-form');if(!form)return;const lat=form.elements.latitude.value,lng=form.elements.longitude.value;if(pickerMarker){picker.removeLayer(pickerMarker);pickerMarker=null;}if(lat!==''&&lng!==''&&Number.isFinite(+lat)&&Number.isFinite(+lng)&&Math.abs(+lat)<=85.0512&&Math.abs(+lng)<=180){pickerMarker=L.marker([+lat,+lng],{draggable:true,icon:L.divIcon({className:'place-pin',html:'<span><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/></svg></span>',iconSize:[36,42],iconAnchor:[18,38]})}).addTo(picker);pickerMarker.on('dragend',()=>{const p=pickerMarker.getLatLng();form.elements.latitude.value=p.lat.toFixed(6);form.elements.longitude.value=p.lng.toFixed(6);pointStatus();});picker.panTo([+lat,+lng],{animate:false});pointStatus();}}
  function pickerCity(id){const city=state.cities.find(c=>c.id===Number(id));if(picker&&city)picker.setView([city.latitude,city.longitude],10,{animate:false});}
  function pointStatus(){const form=$('#event-form'),target=$('#picker-point-status');if(form&&target)target.textContent=`Точка выбрана: ${Number(form.elements.latitude.value).toFixed(5)}, ${Number(form.elements.longitude.value).toFixed(5)}. Метку можно перетащить.`;}
  function setPlace(row){const form=$('#event-form');if(!form)return;form.elements.address.value=row.address||row.label;form.elements.place_name.value=row.name;form.elements.latitude.value=row.latitude;form.elements.longitude.value=row.longitude;pickerCoordinates();picker?.setView([row.latitude,row.longitude],16);}
  function applySchool(school){const form=$('#event-form');if(!form)return;form.elements.place_name.value=school.name;form.elements.address.value=school.address;form.elements.latitude.value=school.latitude??'';form.elements.longitude.value=school.longitude??'';pickerCoordinates();if(school.latitude!=null)picker?.setView([school.latitude,school.longitude],16);else{pickerCity(school.city_id);if($('#picker-point-status'))$('#picker-point-status').textContent='У школы нет координат. Найди адрес или поставь точку на карте.';}}
  function expand(){const panel=$('#map-panel'),expanded=panel.classList.toggle('map-expanded');document.body.classList.toggle('map-expanded-body',expanded);const button=panel.querySelector('[data-action="map-expand"]');if(button)button.textContent=expanded?' Свернуть':' На весь экран';requestAnimationFrame(()=>{map?.invalidateSize();if(map)constrain(map);});}
  function expandPicker(){const element=$('#place-map');element?.classList.toggle('picker-expanded');const button=$('[data-action="picker-expand"]');if(button)button.textContent=element?.classList.contains('picker-expanded')?' Уменьшить карту':' Увеличить карту';requestAnimationFrame(resizePicker);}
  function locate(edit=false){if(!navigator.geolocation){toast('Браузер не поддерживает определение местоположения');return;}const user=state.me?.id;toast('Определяем местоположение…');navigator.geolocation.getCurrentPosition(position=>{if(state.me?.id!==user)return;const {latitude:lat,longitude:lng,accuracy}=position.coords;if(edit){const form=$('#event-form');if(!form)return;form.elements.latitude.value=lat.toFixed(6);form.elements.longitude.value=lng.toFixed(6);pickerCoordinates();picker?.setView([lat,lng],15);toast('Точка выбрана. Укажи адрес и название площадки.');}else{if(state.view!=='map')return;clearFilters();renderChrome();focus(lat,lng);if(positionCircle)map.removeLayer(positionCircle);positionCircle=L.circle([lat,lng],{radius:Math.min(accuracy,5000),color:'#7055dc',fillOpacity:.12}).addTo(map);}},()=>toast('Не удалось определить местоположение. Разреши доступ в браузере или найди адрес.'),{timeout:10000,maximumAge:60000});}
  function wheelHint(instance){const container=instance.getContainer();container.title='Масштаб: кнопки +/−, два пальца или Ctrl + колесо мыши';container.addEventListener('wheel',event=>{if(event.ctrlKey){event.preventDefault();instance.setZoom(instance.getZoom()+(event.deltaY<0?.5:-.5));}},{passive:false});}
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&$('#map-panel').classList.contains('map-expanded')&&!$('#modal').open&&!$('#location-dialog')?.open)expand();});
  return {retryPicker,setPlace,applySchool,expand,expandPicker,locate,show,pause,stop,world,city,focus,select,openPicker,closePicker,resizePicker,pickerCoordinates,pickerCity,invalidateCity:()=>{cityKey=null;}};
})();
