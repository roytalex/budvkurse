(() => {
  'use strict';
  const menu=document.querySelector('#nav-dialog');
  let opener=null;
  function closeMenu(){
    if(menu.open)menu.close();
  }
  menu.addEventListener('close',()=>{
    document.body.classList.remove('navigation-open');
    opener?.focus();
  });
  document.addEventListener('click',event=>{
    if(event.target.closest('[data-nav-open]')){
      opener=event.target.closest('[data-nav-open]');
      if(!menu.open){menu.showModal();document.body.classList.add('navigation-open');}
    }
    if(event.target.closest('[data-nav-close]'))closeMenu();
    if(menu.contains(event.target)&&event.target.closest('[data-view],[data-action],a[href^="#"]'))closeMenu();
    if(event.target===menu){
      const bounds=menu.getBoundingClientRect();
      if(event.clientX<bounds.left||event.clientX>bounds.right||event.clientY<bounds.top||event.clientY>bounds.bottom)closeMenu();
    }
    if(event.target.closest('[data-action="browse-events"]'))document.querySelector('.page-heading').scrollIntoView({behavior:document.documentElement.dataset.motion==='off'?'instant':'smooth',block:'start'});
  });
  window.addEventListener('session-expired',closeMenu);
})();
