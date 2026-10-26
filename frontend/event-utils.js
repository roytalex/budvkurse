                                                                                 
(function(root) {
  const pad = value => String(value).padStart(2,'0');
  const dateKey = value => {const d=new Date(value);return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;};
  const localInput = value => {if(!value)return '';const d=new Date(value);return `${dateKey(d)}T${pad(d.getHours())}:${pad(d.getMinutes())}`;};
  const dayBounds = key => {const from=new Date(key+'T00:00:00');const to=new Date(from);to.setDate(to.getDate()+1);return [from,to];};
  const occursOn = (event,key) => {const [from,to]=dayBounds(key);return new Date(event.starts_at)<to && new Date(event.ends_at)>from;};
  const monthBounds = (year,month) => ({date_from:new Date(year,month,1).toISOString(),date_to:new Date(year,month+1,1).toISOString()});
  const calendarPosition = value => {const d=new Date(value);return {year:d.getFullYear(),month:d.getMonth(),day:dateKey(d)};};
  const result = {dateKey,localInput,dayBounds,occursOn,monthBounds,calendarPosition};
  if(typeof module==='object') module.exports=result;else root.EventDates=result;
})(typeof window==='object'?window:this);
