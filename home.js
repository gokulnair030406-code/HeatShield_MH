let chart,month=5;
const mb=$('#homeMonths');mb.innerHTML=Object.entries(MONTHS).map(([k,v])=>`<button data-m="${k}" class="${k==5?'on':''}">${v}</button>`).join('');
mb.className='months';mb.onclick=e=>{const m=e.target.dataset.m;if(!m)return;month=+m;$$('button',mb).forEach(b=>b.classList.toggle('on',b.dataset.m==m));load()};
async function load(){
 const d=await api('/api/summary?month='+month);
 $('#heroAvg').textContent=d.avg;$('#heroMonth').textContent=MONTHS[month];
 const c=d.counts;
 $('#kpis').innerHTML=[['Stations',d.n,'Maharashtra'],['Average AI risk',d.avg+'/100',bandOf(d.avg)+' band'],['Avg temperature',d.avg_temp+'°C','Simulated'],['High + Very high',c['High']+c['Very high'],'locations at elevated risk']]
  .map(k=>`<div class="kpi"><span>${k[0]}</span><b>${k[1]}</b><small>${k[2]}</small></div>`).join('');
 $('#watch').innerHTML=d.top.map((r,i)=>`<a class="item" href="/map#${r.latitude},${r.longitude},${month}"><b>${i+1}</b><div class="n">${r.place}<small>${r.zone} · ${r.air_temp_c}°C</small></div><b>${r.ai_risk_score}</b>${pill(r.risk_band)}</a>`).join('');
 const lab=Object.values(MONTHS);
 if(chart)chart.destroy();
 Chart.defaults.color='#92a9bd';
 chart=new Chart($('#trend'),{type:'line',data:{labels:lab,datasets:[{data:d.trend,borderColor:'#ff9b62',backgroundColor:'#ff9b6233',fill:true,tension:.35,pointRadius:d.trend.map((_,i)=>i+3==month?8:4),pointBackgroundColor:'#f43f5e'}]},
  options:{plugins:{legend:{display:false}},scales:{y:{min:0,max:100,grid:{color:'#ffffff14'}},x:{grid:{display:false}}}}});
}
load();
