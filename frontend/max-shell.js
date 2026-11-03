(() => {
  'use strict';
  const root=document.documentElement;
  const query=new URLSearchParams(location.search);
  const requested=query.get('max')==='1'||new URLSearchParams(location.hash.slice(1)).has('WebAppData');
  const sections=new Set(['feed','map','calendar','saved','registrations','passport','teams','challenges','schoolboard','achievements','leaderboard','reminders']);
  let bridge=null,launchUsed=false,sessionReady=false;
  let finishLoading=()=>{};
  const ready=requested?new Promise(resolve=>{finishLoading=resolve;setTimeout(resolve,5000);}):Promise.resolve();
  function report(message){if(typeof toast==='function')toast(message);}
  function active(){return !!bridge;}
  function launchTarget(value){
    if(typeof value!=='string'||value.length>512)return null;
    if(sections.has(value))return {view:value};
    const match=/^event_([1-9][0-9]{0,9})$/.exec(value);
    return match?{event:Number(match[1])}:null;
  }
  async function applyLaunch(){
    if(!bridge||launchUsed||!sessionReady)return;
    launchUsed=true;
    const target=launchTarget(bridge.initDataUnsafe?.start_param);
    if(!target)return;
    try{if(target.view)await navigate(target.view);else await openEvent(target.event);}catch{report('Не удалось открыть ссылку на событие. Найди его в ленте.');}
  }
  function updateBack(){
    if(document.querySelector("#application")?.hidden)sessionReady=false;
    if(!bridge?.BackButton)return;
    const modal=document.querySelector('dialog[open]');
    const elsewhere=document.querySelector('#main')?.dataset.view;
    const expanded=document.querySelector('#map-panel')?.classList.contains('map-expanded');
    try{(modal||expanded||sessionReady&&elsewhere&&elsewhere!=='feed')?bridge.BackButton.show():bridge.BackButton.hide();}catch{}
  }
  async function back(){
    const nav=document.querySelector('#nav-dialog');if(nav?.open){nav.close();return;}
    if(document.querySelector('#location-dialog')?.open){window.LocationSearch?.close();return;}
    if(document.querySelector('#modal')?.open){closeModal();return;}
    if(document.querySelector('#map-panel')?.classList.contains('map-expanded')){document.querySelector('[data-action="map-expand"]')?.click();return;}
    if(sessionReady)try{await navigate('feed');}catch{report('Не удалось открыть ленту.');}
  }
  function refreshViewport(){
    const local=window.visualViewport?.height||window.innerHeight;
    if(Number.isFinite(local)&&local>100)root.style.setProperty('--max-viewport-height',`${Math.round(local)}px`);
  }
  function connected(){
    finishLoading();
    const candidate=window.WebApp;
    if(!candidate||typeof candidate.initData!=='string'||!candidate.initData)return;
    bridge=candidate;root.dataset.miniapp='max';
    try{bridge.ready?.();bridge.BackButton?.onClick(back);}catch{}
    refreshViewport();updateBack();applyLaunch();
  }
  if(requested){
    root.dataset.miniapp='preview';
    if(window.WebApp)connected();
    else{const script=document.createElement('script');script.src='https://st.max.ru/js/max-web-app.js';script.async=true;script.onload=connected;script.onerror=()=>{finishLoading();report('MAX Bridge не загрузился. Сайт продолжает работать в обычном режиме.');};document.head.append(script);}
  }
  window.addEventListener('app-session-ready',()=>{sessionReady=true;applyLaunch();updateBack();});
  window.addEventListener('session-expired',()=>{sessionReady=false;updateBack();});
  window.addEventListener('resize',refreshViewport,{passive:true});window.visualViewport?.addEventListener('resize',refreshViewport,{passive:true});
  document.addEventListener('input',event=>{if(bridge&&event.target.closest('#modal form'))try{bridge.enableClosingConfirmation?.();}catch{}});
  new MutationObserver(()=>{updateBack();if(bridge&&!document.querySelector('#modal')?.open)try{bridge.disableClosingConfirmation?.();}catch{}}).observe(document.body,{attributes:true,subtree:true,attributeFilter:['open','data-view','hidden']});
  document.addEventListener('click',event=>{
    if(!bridge)return;
    const link=event.target.closest('a[href]');if(!link||link.hasAttribute('download'))return;
    let url;try{url=new URL(link.href,location.href);}catch{return;}
    if(!['http:','https:'].includes(url.protocol)||url.origin===location.origin)return;
    const open=url.hostname==='max.ru'&&url.searchParams.has('startapp')?bridge.openMaxLink:bridge.openLink;
    if(typeof open!=='function')return;
    event.preventDefault();try{open.call(bridge,url.href);}catch{report('Не удалось открыть ссылку. Попробуй открыть сайт в браузере.');}
  });
  async function prepareCertificate(id){
    const issued=await Api.request(`/events/${id}/certificate-link`,{method:'POST'});
    const url=new URL(issued.path,location.origin);
    if(url.origin!==location.origin||url.protocol!=='https:')throw new Error('Скачивание в MAX доступно после размещения сайта по HTTPS.');
    openModal(`<div class="modal-kicker">СЕРТИФИКАТ УЧАСТИЯ</div><h2 class="modal-heading">Твой результат — с тобой.</h2><p class="form-hint">Файл HTML откроется в браузере. Для PDF выбери «Печать  Сохранить как PDF». Ссылка действует 5 минут.</p><button class="primary-button" type="button" data-max-download="${esc(url.href)}" data-filename="${esc(issued.filename)}">Скачать сертификат</button><p class="form-hint">Если ссылка истекла, закрой окно и создай её заново в паспорте.</p>`,'certificate');
  }
  async function download(url,name){
    const target=new URL(url,location.origin);
    if(!bridge||target.protocol!=='https:'||target.origin!==location.origin||target.pathname!=='/api/v1/exports/certificate')throw new Error('Ссылка на сертификат недоступна.');
    if(typeof bridge.downloadFile!=='function')throw new Error('Обнови MAX для скачивания файлов или открой сайт в обычном браузере.');
    const result=await bridge.downloadFile(target.href,name);
    if(result?.status==='downloading')report('Сертификат передан на скачивание.');
  }
  async function scan(){
    if(typeof bridge?.openCodeReader!=='function')return null;
    const result=await bridge.openCodeReader(true);
    return typeof result?.value==='string'?result.value:null;
  }
  window.MaxShell={ready,active,initData:()=>bridge?.initData||'',launchTarget,prepareCertificate,download,scan,canScan:()=>typeof bridge?.openCodeReader==='function'};
})();
