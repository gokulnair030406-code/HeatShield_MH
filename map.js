let month=5,layer='risk',surf={},overlay=null,probeMk=null,cur=null,curLL=null,pins=[],playT=null,names=[],stLayer=L.layerGroup();
const map=L.map('map',{zoomControl:false,minZoom:5,maxZoom:11,zoomSnap:.25,maxBounds:[[12,69],[25,84]]}).setView([19.2,76.6],6.6);
L.control.zoom({position:'bottomright'}).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© OpenStreetMap · © CARTO',subdomains:'abcd',maxZoom:19}).addTo(map);
stLayer.addTo(map);
api('/api/outline').then(o=>L.polygon(o,{color:'#56e0d0',weight:1.6,dashArray:'6 6',fill:false,interactive:false}).addTo(map));

/* ---------- risk surface ---------- */
async function surfaceURL(m,l){const k=m+l;if(!surf[k]){const d=await api(`/api/surface?month=${m}&layer=${l}`);const c=document.createElement('canvas');c.width=d.nx;c.height=d.ny;const g=c.getContext('2d'),im=g.createImageData(d.nx,d.ny);
 d.values.forEach((v,i)=>{if(v<0){im.data[i*4+3]=0;return}const[r,gg,b]=rampColor(v);im.data.set([r,gg,b,225],i*4)});g.putImageData(im,0,0);surf[k]={url:c.toDataURL(),b:d.bounds,lo:d.lo,hi:d.hi}}return surf[k]}
async function showSurface(){const s=await surfaceURL(month,layer);
 if(overlay)overlay.setUrl(s.url);else{overlay=L.imageOverlay(s.url,s.b,{opacity:.85,interactive:false}).addTo(map)}
 const T={risk:['AI heat-risk score','0','100'],temp:['Air temperature','24 °C','46 °C'],water:['Water-access gap','small gap','large gap']}[layer];
 $('#legTitle').textContent=T[0];$('#legLo').textContent=T[1];$('#legHi').textContent=T[2]}
async function showStations(){const [st,sm]=await Promise.all([api('/api/stations?month='+month),api('/api/summary?month='+month)]);
 stLayer.clearLayers();names=st.map(s=>s.place);$('#places').innerHTML=names.map(n=>`<option value="${n}">`).join('');
 st.forEach(s=>L.circleMarker([s.latitude,s.longitude],{radius:6,color:'#fff',weight:1.5,fillColor:BCOL[s.risk_band],fillOpacity:1,bubblingMouseEvents:false})
  .bindTooltip(`${s.place} · ${s.ai_risk_score}`).on('click',()=>probe(L.latLng(s.latitude,s.longitude))).addTo(stLayer));
 $('#hotList').innerHTML=sm.top.slice(0,5).map((r,i)=>`<div class="item" data-ll="${r.latitude},${r.longitude}"><b>${i+1}</b><div class="n">${r.place}<small>${r.zone}</small></div><b>${r.ai_risk_score}</b></div>`).join('')}
$('#hotList').onclick=e=>{const it=e.target.closest('.item');if(!it)return;const [a,b]=it.dataset.ll.split(',').map(Number);map.flyTo([a,b],8,{duration:1});probe(L.latLng(a,b))};

/* ---------- controls ---------- */
function setMonth(m,quiet){month=m;$$('#monthSeg button').forEach(b=>b.classList.toggle('on',b.dataset.m==m));showSurface();showStations();if(curLL)probe(curLL,true)}
$('#monthSeg').onclick=e=>{if(e.target.dataset.m){stopPlay();setMonth(+e.target.dataset.m)}};
$('#layerSeg').onclick=e=>{if(e.target.dataset.l){layer=e.target.dataset.l;$$('#layerSeg button').forEach(b=>b.classList.toggle('on',b.dataset.l==layer));showSurface()}};
function stopPlay(){clearInterval(playT);playT=null;$('#play').textContent='▶ Time-lapse'}
$('#play').onclick=()=>{if(playT)return stopPlay();$('#play').textContent='⏸ Pause';const tick=()=>setMonth(month>=6?3:month+1);tick();playT=setInterval(tick,1800)};
$('#search').addEventListener('change',e=>{const q=e.target.value.trim().toLowerCase(),n=names.find(x=>x.toLowerCase()===q);if(!n)return toast('Pick a city from the list');
 api('/api/stations?month='+month).then(st=>{const s=st.find(x=>x.place===n);map.flyTo([s.latitude,s.longitude],8,{duration:1});probe(L.latLng(s.latitude,s.longitude))});e.target.value=''});
$('#closeD').onclick=()=>$('#drawer').classList.add('hide');
map.on('click',e=>{stopPlay();probe(e.latlng)});

/* ---------- probe drawer ---------- */
async function probe(ll,quiet){
 const d=await api('/api/probe',{lat:ll.lat,lon:ll.lng,month});
 if(!d.inside){if(!quiet)toast(d.error||'Outside the demo region');return}
 curLL=ll;cur=d;
 if(probeMk)map.removeLayer(probeMk);
 probeMk=L.marker(ll,{icon:L.divIcon({className:'',html:'<div class="mk"></div>',iconSize:[16,16],iconAnchor:[8,8]}),interactive:false}).addTo(map);
 const dr=$('#drawer');dr.classList.remove('hide');
 $('#drawerBody').innerHTML=`<div class="dh">📍 Near ${d.nearest[0].place}</div>
  <div class="dsub">${d.zone} · ${d.month_name} · ${d.lat.toFixed(3)}°N, ${d.lon.toFixed(3)}°E</div>
  <div class="gwrap"><div style="width:180px;flex:none" id="dG"></div><div><div class="bandname" id="dB"></div><div class="delta" id="dD"></div></div></div>
  <p class="muted sm" id="dT"></p>
  <h5>Try a what-if</h5><div id="dS"></div>
  <h5>What drives this score</h5><div class="bars" id="dR"></div>
  <h5>Cool it down</h5><div id="dI"></div>
  <h5>Closest stations</h5>${d.nearest.map(n=>`<div class="nb"><span>${n.place} · ${n.km} km</span><b>${n.score}</b></div>`).join('')}
  <div class="row"><button class="btn sm" id="dPin">📌 Pin to compare</button><button class="btn sm" id="dSim">🧪 Open in simulator</button><button class="btn sm" id="dRst">↺ Reset</button></div><div id="dC"></div>`;
 let res=d;
 const upd=r=>{res=r;$('#dG').innerHTML=gauge(r.score);const b=$('#dB');b.textContent=r.band+' proxy';b.style.color=BCOL[r.band];
  const df=r.score-d.score,el=$('#dD');el.textContent=Math.abs(df)<.05?'baseline for this point':`${df>0?'▲ +':'▼ −'}${Math.abs(df).toFixed(1)} vs. baseline`;el.className='delta '+(df>0.05?'up':df<-0.05?'dn':'');
  $('#dT').textContent=r.guidance;$('#dR').innerHTML=driversHTML(r.drivers);$('#dI').innerHTML=intervHTML(r.interventions)};
 upd(d);
 const S=$('#dS'),vals={};FEATURES.forEach(f=>vals[f]=d.features[f]);
 buildSliders(S,vals,debounce(async()=>upd(await api('/api/predict',getVals(S))),90),true);
 $('#dI').onclick=e=>{const b=e.target.closest('.iv');if(b)setVal(S,b.dataset.f,b.dataset.v)};
 $('#dRst').onclick=()=>{FEATURES.forEach(f=>{$('#s_'+f,S).value=d.features[f];$('#v_'+f,S).textContent=fmtF(f,d.features[f])+META[f].unit});upd(d)};
 $('#dSim').onclick=()=>{localStorage.setItem('hs_prefill',JSON.stringify({place:'Near '+d.nearest[0].place,...getVals(S)}));location.href='/simulator'};
 $('#dPin').onclick=()=>{pins.push({n:`Near ${d.nearest[0].place}`,m:d.month_name,s:res.score,b:res.band,t:getVals(S).air_temp_c});pins=pins.slice(-2);cmp()};
 cmp()}
function cmp(){const el=$('#dC');if(!el)return;if(pins.length<2){el.innerHTML=pins.length?'<p class="muted sm">Pinned 1 of 2. Click another point and pin it to compare.</p>':'';return}
 const[a,b]=pins,df=b.s-a.s;el.innerHTML=`<h5>Comparison</h5><table class="cmpt"><tr><th></th><th>A</th><th>B</th></tr><tr><td>Place</td><td>${a.n}</td><td>${b.n}</td></tr><tr><td>Month</td><td>${a.m}</td><td>${b.m}</td></tr><tr><td>Temp</td><td>${(+a.t).toFixed(1)}°C</td><td>${(+b.t).toFixed(1)}°C</td></tr><tr><td>Risk</td><td><b>${a.s.toFixed(1)}</b></td><td><b>${b.s.toFixed(1)}</b></td></tr></table><p class="sm">${Math.abs(df)<.5?'Both spots score about the same.':`B is ${Math.abs(df).toFixed(1)} pts ${df>0?'riskier':'safer'} than A.`}</p>`}

/* ---------- boot ---------- */
(async()=>{await Promise.all([showSurface(),showStations()]);
 const h=location.hash.slice(1).split(',').map(Number);
 if(h.length==3&&h.every(x=>!isNaN(x))){month=h[2];setMonth(month);map.setView([h[0],h[1]],8);probe(L.latLng(h[0],h[1]))}
 else $('#drawer').classList.remove('hide');
 [3,4,5,6].forEach(m=>surfaceURL(m,'risk'))})();
