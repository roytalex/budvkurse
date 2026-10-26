const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const crypto=require('node:crypto');

function subject(request){
  const context={window:{},document:{addEventListener(){},querySelectorAll:()=>[]},state:{me:{id:1},view:'feed'},
    Api:{request,all:async()=>[]},$:()=>null,crypto,clearTimeout,setTimeout,
    FormData:class{constructor(form){this.form=form;}get(){return this.form.text;}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../communications.js'),'utf8'),context);
  return context.window.Communications;
}
test('Повтор отправки после сбоя использует тот же client_id; новый текст получает другой',async()=>{
  const requests=[];
  const communication=subject(async(path,options)=>{requests.push(options.body);throw new Error('offline');});
  const form={dataset:{conversation:'7'},text:'Привет',isConnected:false};
  await assert.rejects(communication.send(form));
  await assert.rejects(communication.send(form));
  assert.equal(requests[0].client_id,requests[1].client_id);
  form.text='Другой вопрос';await assert.rejects(communication.send(form));
  assert.notEqual(requests[1].client_id,requests[2].client_id);
});
test('Выход из аккаунта очищает черновик и идентификатор повторной отправки',async()=>{
  const requests=[];const communication=subject(async(path,options)=>{requests.push(options.body);throw new Error('offline');});
  const form={dataset:{conversation:'7'},text:'Привет',isConnected:false};
  await assert.rejects(communication.send(form));communication.stop();await assert.rejects(communication.send(form));
  assert.notEqual(requests[0].client_id,requests[1].client_id);
});
