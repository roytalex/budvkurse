                                                                            
window.LocationSearch=(()=>{
  let context=null, rows=[], serial=0, controller=null, manualMap=null,manualMarker=null;
  const dialog=document.createElement('dialog');dialog.id='location-dialog';document.body.append(dialog);
  function cityId(){return context?.form ? (context.form.elements.city_id?.value||'') : (state.city||'');}
  function open(kind,form=null){
    if(!state.me)return;
    context={kind,form};rows=[];serial++;controller?.abort();
    if(kind==='school'&&!cityId()){toast('Сначала выбери населённый пункт');return;}
    const title={city:'Найди свой населённый пункт',school:'Выбери школу',place:'Найди адрес или площадку'}[kind];
    dialog.innerHTML=`<button type="button" class="modal-close icon-button" data-geo-close aria-label="Закрыть поиск">×</button><h2>${title}</h2><p>${kind==='city'?'Города, посёлки, сёла и деревни России. У одноимённых мест проверяй регион.':kind==='school'?`Поиск в ${esc(cityName(cityId()))}. Введи название или номер школы, лицея, гимназии.`:'Введи улицу, дом или название места. Выбор подставит адрес и точку на карте.'}</p><form id="location-search-form"><label class="form-field">${kind==='city'?'Название и регион':kind==='school'?'Название или номер':'Адрес'}<div class="location-input-row"><input name="query" placeholder="${kind==='city'?'Например: Выборг, Ленинградская область':kind==='school'?'Например: школа 12 или лицей':'Например: улица Ленина, 10'}" maxlength="150" required autocomplete="off"><button class="primary-button" type="submit">Найти</button></div></label></form><div id="location-status" role="status"></div><div id="location-results" class="location-results"></div>${kind!=='place'&&canOrganize()?'<button type="button" class="secondary-button" data-geo-manual>Не найдено? Добавить вручную</button>':''}<p class="location-credit">Поиск: <a href="https://photon.komoot.io/" target="_blank" rel="noopener noreferrer">Photon</a> · © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>. Возможны пропуски; это не полный государственный реестр.</p>`;
    if(!dialog.open)dialog.showModal();dialog.querySelector('input').focus();
  }
  function close(){serial++;controller?.abort();manualMap?.remove();manualMap=null;manualMarker=null;dialog.close();context=null;rows=[];}
  async function search(form){
    const seq=++serial;controller?.abort();controller=new AbortController();
    let q=form.elements.query.value.trim();if(/^\d+$/.test(q)&&context.kind==='school')q='школа '+q;
    if(q.length<2){$('#location-status').textContent='Введи хотя бы два символа';return;}
    $('#location-status').textContent='Ищем…';$('#location-results').innerHTML='';rows=[];
    const result=await Api.request('/locations/search?'+Api.query({q,kind:context.kind,city_id:context.kind==='city'?'':cityId()}),{signal:controller.signal});
    if(seq!==serial||!dialog.open||!state.me)return;
    rows=result.items;
    $('#location-status').textContent=result.warning||(!rows.length?'Ничего не найдено. Попробуй другое название или добавь регион.':`Найдено вариантов: ${rows.length}. Если нужного нет — уточни запрос.`);
    $('#location-results').innerHTML=rows.map((r,i)=>`<button type="button" class="location-result" data-geo-result="${i}"><span class="location-symbol">${context.kind==='school'?'▤':''}</span><span><b>${esc(r.name)}</b><small>${esc(r.label)}</small><em>${esc(r.source)}</em></span><span>Выбрать </span></button>`).join('');
  }
  async function apply(selection){
    if(!context)return;
    const active=context,form=context.form,kind=context.kind;
    await refreshCatalogs();
    if(!state.me||!dialog.open||context!==active)return;
    if(form?.isConnected){
      form.elements.city_id.innerHTML=options(state.cities,selection.city.id,'Выбери населённый пункт');
      form.elements.school_id.innerHTML=schoolOptions(selection.city.id,selection.school?.id,'Без школы');
      if(form.id==='event-form'){
        if(selection.school)EventMap.applySchool(selection.school);
        else EventMap.pickerCity(selection.city.id);
      }
    }else{
      state.city=String(selection.city.id);state.school=selection.school?String(selection.school.id):'';state.page=1;
      EventMap.invalidateCity();await loadView();
    }
    close();toast(kind==='school'?'Школа выбрана':'Населённый пункт выбран');
  }
  function manual(){
    if(context.kind==='city'){manualCity();return;}
    const id=cityId();dialog.innerHTML=`<button type="button" class="modal-close icon-button" data-geo-close aria-label="Закрыть">×</button><h2>Добавить школу</h2><p>${esc(cityName(id))}. Укажи настоящее название и адрес. Координаты можно выбрать позже на карте мероприятия.</p><form id="location-manual-form" data-city-id="${id}"><label class="form-field">Название<input name="name" maxlength="200" required></label><label class="form-field">Адрес<input name="address" maxlength="1000" required></label><div class="form-grid"><label class="form-field">Широта, если известна<input name="latitude" type="number" min="-90" max="90" step="any"></label><label class="form-field">Долгота, если известна<input name="longitude" type="number" min="-180" max="180" step="any"></label></div><div id="location-status" class="form-error" role="alert"></div><button class="primary-button" type="submit">Добавить и выбрать</button></form>`;
  }
  function manualCity(){
    dialog.innerHTML=`<button type="button" class="modal-close icon-button" data-geo-close aria-label="Закрыть">×</button><h2>Добавить населённый пункт</h2><p>Укажи настоящее название и регион. Нажми на карту, чтобы выбрать центр населённого пункта.</p><form id="location-manual-city"><label class="form-field">Название<input name="name" maxlength="120" required></label><label class="form-field">Регион<input name="region" maxlength="120" required></label><div id="location-manual-map"></div><div class="form-grid"><label class="form-field">Широта<input name="latitude" type="number" min="-85" max="85" step="any" required></label><label class="form-field">Долгота<input name="longitude" type="number" min="-180" max="180" step="any" required></label></div><div id="location-status" class="form-error" role="alert"></div><button class="primary-button" type="submit">Добавить и выбрать</button></form>`;
    if(window.L){manualMap=L.map('location-manual-map',{scrollWheelZoom:false,maxBounds:[[-85,-180],[85,180]],maxBoundsViscosity:1,minZoom:2,maxZoom:19}).setView([57,60],3);Basemap.add(manualMap);manualMap.attributionControl.setPrefix(false);manualMap.on('click',e=>{const f=$('#location-manual-city');f.elements.latitude.value=e.latlng.lat.toFixed(6);f.elements.longitude.value=e.latlng.lng.toFixed(6);if(manualMarker)manualMarker.remove();manualMarker=L.circleMarker(e.latlng,{color:'#7055dc',radius:9}).addTo(manualMap);});}
  }
  dialog.addEventListener('submit',async event=>{
    event.preventDefault();event.stopPropagation();const form=event.target;
    const active=context,button=form.querySelector('[type=submit]');if(button.disabled)return;button.disabled=true;
    try{if(form.id==='location-search-form')await search(form);else if(form.id==='location-manual-city'){
      const fd=new FormData(form);const selected=await Api.request('/locations/cities/manual',{method:'POST',body:{name:fd.get('name').trim(),region:fd.get('region').trim(),country_code:'RU',latitude:Number(fd.get('latitude')),longitude:Number(fd.get('longitude'))}});if(context===active)await apply(selected);
    }else{
      const fd=new FormData(form);const coord=k=>fd.get(k)===''?null:Number(fd.get(k));
      const school=await Api.request('/locations/schools/manual',{method:'POST',body:{city_id:Number(form.dataset.cityId),name:fd.get('name').trim(),address:fd.get('address').trim(),latitude:coord('latitude'),longitude:coord('longitude')}});
      if(context===active)await apply({city:{id:school.city_id},school});
    }}catch(error){if(error.name!=='AbortError'&&error.status!==401&&dialog.open)$('#location-status').textContent=error.message;}finally{button.disabled=false;}
  });
  dialog.addEventListener('click',async event=>{
    event.stopPropagation();const button=event.target.closest('button');if(!button||button.disabled)return;
    if(button.hasAttribute('data-geo-close')){close();return;}
    if(button.hasAttribute('data-geo-manual')){serial++;controller?.abort();manual();return;}
    if(!button.hasAttribute('data-geo-result'))return;
    const row=rows[Number(button.dataset.geoResult)];if(!row)return;
    const active=context;button.disabled=true;
    try{if(context.kind==='place'){
      if(context.form?.id==='event-form')EventMap.setPlace(row);else{clearFilters();renderChrome();EventMap.focus(row.latitude,row.longitude);}
      close();toast('Место выбрано');
    }else{const selected=await Api.request('/locations/select',{method:'POST',body:{token:row.token}});if(context===active)await apply(selected);}
    }catch(error){if(dialog.open&&error.status!==401)$('#location-status').textContent=error.message;}finally{button.disabled=false;}
  });
  dialog.addEventListener('cancel',close);
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-geo-open]');if(!button)return;
    event.preventDefault();event.stopImmediatePropagation();open(button.dataset.geoOpen,button.closest('form'));
  },true);
  window.addEventListener('session-expired',close);
  return {open,close};
})();
