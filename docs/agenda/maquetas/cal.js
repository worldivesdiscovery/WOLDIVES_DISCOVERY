// Draws a Monday-first month. states: {day: 'busy'|'am'|'pm'|'past'|'sel'|'sel-mid'|'blocked'}, labels: {day: 'text'}
function drawMonth(el, year, month, states, labels){
  const first=new Date(Date.UTC(year,month-1,1)), days=new Date(Date.UTC(year,month,0)).getUTCDate();
  const lead=(first.getUTCDay()+6)%7; let h='<thead><tr>'+['L','M','X','J','V','S','D'].map(d=>`<th>${d}</th>`).join('')+'</tr></thead><tbody><tr>';
  for(let i=0;i<lead;i++) h+='<td class="out"></td>';
  for(let d=1;d<=days;d++){ const c=(lead+d-1)%7; if(c===0&&d>1) h+='</tr><tr>'; h+=`<td class="${states[d]||''}">${d}${labels&&labels[d]?`<small>${labels[d]}</small>`:''}</td>`; }
  h+='</tr></tbody>'; el.innerHTML=h;
}
