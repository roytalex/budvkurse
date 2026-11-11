                                                                     
(() => {
  function annotate(){
    document.querySelectorAll('form').forEach(form=>{
      let count=0;
      form.querySelectorAll('label.form-field').forEach(label=>{
        const field=label.querySelector('input:not([type=checkbox]):not([type=hidden]),select,textarea');
        if(!field)return;
        const optional=!field.required&&(field.tagName!=='SELECT'||[...field.options].some(o=>o.value===''));
        let mark=label.querySelector('.optional-star');
        if(optional){count++;if(!mark){mark=document.createElement('span');mark.className='optional-star';mark.textContent=' *';mark.title='Необязательное поле';mark.setAttribute('aria-label','необязательное поле');let title=label.querySelector('.field-title');if(!title){title=document.createElement('span');title.className='field-title';for(const node of [...label.childNodes]){if(node===field)break;if(node.nodeType===Node.TEXT_NODE)title.append(node);}label.insertBefore(title,field);}title.append(mark);}}
        else mark?.remove();
      });
      let note=form.querySelector('.optional-note');
      if(count&&!note){note=document.createElement('p');note.className='optional-note';note.textContent='* - необязательное поле, можно оставить пустым.';form.prepend(note);}
      if(!count)note?.remove();
    });
  }
  let scheduled=false;
  new MutationObserver(()=>{if(!scheduled){scheduled=true;requestAnimationFrame(()=>{scheduled=false;annotate();});}}).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['required']});
  annotate();
})();
