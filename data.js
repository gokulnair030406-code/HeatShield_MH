let csvOut='';
function table(el,rows){if(!rows.length){el.innerHTML='';return}const k=Object.keys(rows[0]);
 el.innerHTML='<tr>'+k.map(c=>`<th>${c}</th>`).join('')+'</tr>'+rows.map(r=>'<tr>'+k.map(c=>`<td>${c==='risk_band'?pill(r[c]):r[c]}</td>`).join('')+'</tr>').join('')}
async function send(f){
 if(!f)return;const fd=new FormData();fd.append('file',f);$('#msg').innerHTML='<div class="muted">Scoring…</div>';
 const d=await (await fetch('/api/score_csv',{method:'POST',body:fd})).json();
 if(d.error){$('#results').hidden=true;$('#msg').innerHTML=`<div class="err">⚠ ${d.error}</div>`;return}
 $('#msg').innerHTML=`<div class="ok">✔ Processed ${d.total} rows. Skipped ${d.skipped} incomplete or non-numeric rows.</div>`;
 $('#results').hidden=false;csvOut=d.csv;
 $('#rk').innerHTML=[['Rows scored',d.total],['Average score',d.avg],['High + Very high',d.counts.High+d.counts['Very high']],['Low',d.counts.Low]].map(k=>`<div class="kpi"><span>${k[0]}</span><b>${k[1]}</b></div>`).join('');
 table($('#tbl'),d.rows)}
const dz=$('#drop');dz.onclick=()=>$('#file').click();$('#file').onchange=e=>send(e.target.files[0]);
['dragover','dragenter'].forEach(v=>dz.addEventListener(v,e=>{e.preventDefault();dz.classList.add('over')}));
['dragleave','drop'].forEach(v=>dz.addEventListener(v,e=>{e.preventDefault();dz.classList.remove('over')}));
dz.addEventListener('drop',e=>send(e.dataTransfer.files[0]));
$('#dl').onclick=()=>download('heatshield_scored.csv',csvOut);
api('/api/dataset?limit=12').then(d=>{$('#dsInfo').textContent=`${d.total} simulated records · 31 places · March to June`;table($('#demo'),d.rows)});
