const $=s=>document.querySelector(s);
const DEF={}; FEATURES.forEach(f=>{const m=META[f];DEF[f]=(Number(m.min)+Number(m.max))/2});
const S=$('#sliders');let init={...DEF};
function drawResult(r){$('#result').innerHTML=`<div class="res"><div><div class="muted sm">HEAT VULNERABILITY INDEX</div><div class="bandname">${r.band} proxy band</div><h1>${Number(r.score).toFixed(1)} / 100</h1><p>${r.guidance}</p><p class="muted sm">Formula-generated proxy label, not an official assessment.</p></div></div>`;$('#drv').innerHTML=(r.drivers||[]).map(d=>`<div class="item"><span>${d.label}</span><b>${Number(d.delta).toFixed(2)}</b></div>`).join('');$('#int').innerHTML='<p class="muted sm">Intervention effects are not calibrated with observed outcomes in this dataset.</p>'}
async function run(){const vals=getVals(S);const r=await api('/api/predict',vals);if(r.error)return toast(r.error);drawResult(r)}
buildSliders(S,init,debounce(run,120),false);run();
$('#go').onclick=run;$('#reset').onclick=()=>{FEATURES.forEach(f=>setVal(S,f,DEF[f]));run()};
