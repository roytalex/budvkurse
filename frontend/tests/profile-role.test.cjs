const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../app-live.js'),'utf8');
function profile(role){
  let html='';
  const context={state:{me:{role,name:'Тест',email:'test@example.org',grade:8,school_id:1,city_id:1},cities:[]},roles:{student:'Ученик',organizer:'Организатор'},esc:String,options:()=>'',schoolOptions:()=>'',canOrganize:()=>role==='organizer',openModal:value=>html=value};
  for(const name of ['geoFields','profileForm'])vm.runInNewContext(source.split('\n').find(line=>line.startsWith('function '+name+'(')),context);
  context.profileForm();return html;
}
test('Organizer profile contains city and MAX contact but no student fields',()=>{
  const html=profile('organizer');
  assert.match(html,/name="city_id"/);assert.match(html,/name="max_contact_url"/);
  assert.doesNotMatch(html,/name="(?:grade|school_id)"/);
  assert.doesNotMatch(html,/data-geo-open="school"/);
});
test('Student profile retains grade and school',()=>{
  const html=profile('student');
  assert.match(html,/name="grade"/);assert.match(html,/name="school_id"/);
});
