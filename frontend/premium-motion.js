(() => {
  'use strict';
  const root=document.documentElement;
  const enabled=()=>root.dataset.motion!=='off';
  const active=new Set();
  const revealed=new WeakSet();
  let frame=0, intro=null;
  function play(element,frames,options){
    if(!enabled()||!element.animate)return;
    const animation=element.animate(frames,options);active.add(animation);
    animation.onfinish=animation.oncancel=()=>active.delete(animation);
    return animation;
  }
  let firstVisit=false;
  try{firstVisit=!sessionStorage.getItem('vkurse-intro-v3');sessionStorage.setItem('vkurse-intro-v3','1');}catch{}
  if(firstVisit&&enabled()&&document.body.animate){
    intro=document.createElement('div');intro.className='intro-burst';intro.setAttribute('aria-hidden','true');intro.innerHTML='<div>будь<span>в курсе </span></div>';document.body.append(intro);
    const animation=play(intro,[{clipPath:'inset(0 0 0 0)'},{clipPath:'inset(0 0 0 0)',offset:.3},{clipPath:'inset(0 0 100% 0)'}],{duration:850,easing:'cubic-bezier(.76,0,.24,1)'});
    animation.finished.catch(()=>{}).finally(()=>{intro?.remove();intro=null;});
  }
  const revealSelector='[data-photo-reveal],.hero-word,.story-step,.organizer-story>div:last-child,.final-opportunity h2';
  const observer='IntersectionObserver' in window?new IntersectionObserver(entries=>entries.forEach(entry=>{
    if(!entry.isIntersecting)return;
    observer.unobserve(entry.target);
    const photo=entry.target.hasAttribute('data-photo-reveal');
    const frames=photo?[{clipPath:'inset(12% 0 88% 0)',opacity:.6},{clipPath:getComputedStyle(entry.target).clipPath,opacity:1}]:[{transform:'translateY(32px)',opacity:0},{transform:'translateY(0)',opacity:1}];
    play(entry.target,frames,{duration:photo?900:700,easing:'cubic-bezier(.2,.7,.2,1)',delay:entry.target.classList.contains('hero-accent')?120:0});
  }),{threshold:.12}):null;
  document.querySelectorAll(revealSelector).forEach(el=>{if(!revealed.has(el)){revealed.add(el);observer?.observe(el);}});
  function updateScroll(){
    frame=0;if(!enabled()||document.hidden)return;
    const height=window.innerHeight;
    document.querySelectorAll('[data-parallax],[data-scroll-type]').forEach(el=>{
      const bounds=el.parentElement.getBoundingClientRect();if(bounds.bottom<0||bounds.top>height)return;
      const amount=Math.max(-1,Math.min(1,(bounds.top-height/2)/height));
      el.style.transform=el.hasAttribute('data-parallax')?`translateY(${amount*20-15}px)`:`translateX(${amount*12}px)`;
    });
  }
  function queue(){if(!frame&&enabled())frame=requestAnimationFrame(updateScroll);}
  window.addEventListener('scroll',queue,{passive:true});window.addEventListener('resize',queue,{passive:true});
  const pointer=window.matchMedia('(pointer:fine)');
  document.querySelectorAll('[data-magnetic]').forEach(button=>{
    button.addEventListener('pointermove',event=>{if(!enabled()||!pointer.matches)return;const box=button.getBoundingClientRect();button.style.transform=`translate(${(event.clientX-box.left-box.width/2)*.08}px,${(event.clientY-box.top-box.height/2)*.13}px)`;});
    button.addEventListener('pointerleave',()=>{button.style.transform='';});
  });
  const main=document.querySelector('#main');
  new MutationObserver(()=>{
    play(document.querySelector('.page-heading'),[{opacity:.25,transform:'translateY(12px)'},{opacity:1,transform:'translateY(0)'}],{duration:350,easing:'ease-out'});queue();
  }).observe(main,{attributes:true,attributeFilter:['data-view']});
  new MutationObserver(()=>{
    if(!enabled()){
      [...active].forEach(a=>a.cancel());intro?.remove();intro=null;
      cancelAnimationFrame(frame);frame=0;
      document.querySelectorAll('[data-parallax],[data-scroll-type],[data-magnetic]').forEach(el=>{el.style.transform='';});
    }else queue();
  }).observe(root,{attributes:true,attributeFilter:['data-motion']});
  let display='grid';try{if(localStorage.getItem('vkurse-catalog-display')==='list')display='list';}catch{}
  function setDisplay(value){
    document.querySelector('#events').dataset.display=value;
    document.querySelectorAll('button[data-display]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.display===value)));
  }
  setDisplay(display);
  document.addEventListener('click',event=>{
    const button=event.target.closest('button[data-display]');if(!button)return;
    setDisplay(button.dataset.display);try{localStorage.setItem('vkurse-catalog-display',button.dataset.display);}catch{}
    play(document.querySelector('#events'),[{opacity:.3},{opacity:1}],{duration:250});
  });
  queue();
})();
