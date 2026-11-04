const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const BCOL={Low:'#2dd4bf',Moderate:'#facc15',High:'#fb923c','Very high':'#f43f5e'};
const bandOf=s=>s>=65?'Very high':s>=45?'High':s>=25?'Moderate':'Low';
const pill=b=>`<span class="pill b-${b.split(' ')[0]}">${b}</span>`;
const RAMP=[[0,[24,120,170]],[25,[45,212,191]],[45,[250,204,21]],[65,[251,146,60]],[100,[244,63,94]]];
function rampColor(v){v=Math.max(0,Math.min(100,v));for(let i=1;i<RAMP.length;i++){if(v<=RAMP[i][0]){const[a,ca]=RAMP[i-1],[b,cb]=RAMP[i],t=(v-a)/(b-a);return ca.map((c,k)=>Math.round(c+(cb[k]-c)*t))}}return RAMP[4][1]}
function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(()=>t.classList.remove('show'),3200)}
async function api(url,body){const r=await fetch(url,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});return r.json()}
function fmtF(f,v){v=+v;return f==='night_cooling_index'?v.toFixed(2):f==='air_temp_c'?v.toFixed(1):Math.round(v)}
function gauge(s){const c=BCOL[bandOf(s)],L=251.3,d='M20 100A80 80 0 0 1 180 100';
 return `<svg class="gauge" viewBox="0 0 200 125" width="100%"><path d="${d}" fill="none" stroke="#ffffff18" stroke-width="16" stroke-linecap="round"/><path d="${d}" fill="none" stroke="${c}" stroke-width="16" stroke-linecap="round" stroke-dasharray="${L*s/100} ${L}"/><text x="100" y="94" text-anchor="middle" font-size="38" font-weight="700" fill="#fff">${s.toFixed(1)}</text><text x="100" y="117" text-anchor="middle" font-size="11" fill="#92a9bd">of 100</text></svg>`}
function driversHTML(list){const L=[...list].sort((a,b)=>Math.abs(b.delta)-Math.abs(a.delta)),m=Math.max(1,...L.map(x=>Math.abs(x.delta)));
 return L.map(x=>{const w=Math.abs(x.delta)/m*50,pos=x.delta>=0;return `<div><span>${x.label}</span><div class="dv"><i class="${pos?'pos':'neg'}" style="${pos?'left':'right'}:50%;width:${w}%"></i></div><span class="v ${pos?'up':'dn'}">${pos?'+':'−'}${Math.abs(x.delta).toFixed(1)}</span></div>`}).join('')}
function intervHTML(list){return list.map(x=>`<button class="iv" data-f="${x.feature}" data-v="${x.new_value}"><span>${x.text}</span><b>${x.gain>0.05?'−'+x.gain.toFixed(1)+' pts':'≈ 0'}</b></button>`).join('')}
function buildSliders(el,vals,onInput,compact){
 el.innerHTML=FEATURES.map(f=>{const m=META[f];return `<div class="sl ${compact?'c':''}"><div class="top"><span>${m.label}</span><b id="v_${f}">${fmtF(f,vals[f])}${m.unit}</b></div><input type="range" id="s_${f}" min="${m.min}" max="${m.max}" step="${m.step}" value="${vals[f]}"><small>${m.hint}</small></div>`}).join('');
 FEATURES.forEach(f=>$('#s_'+f,el).addEventListener('input',()=>{$('#v_'+f,el).textContent=fmtF(f,$('#s_'+f,el).value)+META[f].unit;onInput&&onInput()}))}
function getVals(el){const o={};FEATURES.forEach(f=>o[f]=parseFloat($('#s_'+f,el).value));return o}
function setVal(el,f,v){const i=$('#s_'+f,el);i.value=v;i.dispatchEvent(new Event('input'))}
function debounce(fn,ms){let t;return(...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms)}}
function download(name,text){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/csv'}));a.download=name;a.click()}
