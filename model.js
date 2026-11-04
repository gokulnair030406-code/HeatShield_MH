(async()=>{
const d=await api('/api/model'),m=d.metrics;
$('#mk').innerHTML=[['Parameters',d.params,'weights + biases'],['Train / test rows',m.train_rows+' / '+m.test_rows,'80/20 split'],['MAE',m.MAE,'score points'],['RMSE',m.RMSE,'score points'],['R²',m.R2,'on synthetic labels']].map(k=>`<div class="kpi"><span>${k[0]}</span><b>${k[1]}</b><small>${k[2]}</small></div>`).join('');
/* architecture drawing */
const sizes=d.sizes,show=[7,10,8,1],names=['Input','Dense 32 · ReLU','Dense 16 · ReLU','Output · Sigmoid'],X=[90,290,490,680],svg=$('#net');let h='';
const pos=show.map((n,i)=>Array.from({length:n},(_,j)=>[X[i],165+(j-(n-1)/2)*(i==0?30:i==3?0:24)]));
for(let i=0;i<3;i++)pos[i].forEach(a=>pos[i+1].forEach(b=>h+=`<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="#56e0d0" stroke-opacity=".10"/>`));
pos.forEach((L,i)=>{L.forEach((p,j)=>{const t=i==0?window.META[FEATURES[j]].label:i==3?'Risk score 0–100':`neuron ${j+1}`;h+=`<circle cx="${p[0]}" cy="${p[1]}" r="${i==3?16:9}" fill="${i==3?'#f43f5e':i==0?'#63a8ff':'#56e0d0'}" stroke="#07111f" stroke-width="2"><title>${t}</title></circle>`});
 h+=`<text x="${X[i]}" y="${i==0?305:i==3?220:292}" fill="#92a9bd" font-size="12" text-anchor="middle">${names[i]}</text>`;
 if(i==1||i==2)h+=`<text x="${X[i]}" y="40" fill="#92a9bd" font-size="11" text-anchor="middle">showing ${show[i]} of ${sizes[i]}</text>`});
h+=`<text x="390" y="318" fill="#ffffff55" font-size="10" text-anchor="middle">Dropout 0.10 after the first hidden layer (training only)</text>`;svg.innerHTML=h;
/* charts */
Chart.defaults.color='#92a9bd';const grid={color:'#ffffff14'};
new Chart($('#loss'),{type:'line',data:{labels:d.history.map(x=>x[0]),datasets:[{label:'Train MSE',data:d.history.map(x=>x[1]),borderColor:'#56e0d0',pointRadius:0,tension:.2},{label:'Test MSE',data:d.history.map(x=>x[2]),borderColor:'#ff9b62',pointRadius:0,tension:.2}]},
 options:{scales:{y:{type:'logarithmic',grid},x:{grid:{display:false},title:{display:true,text:'epoch'}}}}});
new Chart($('#sc'),{type:'scatter',data:{datasets:[{label:'Test rows',data:d.scatter.map(p=>({x:p[0],y:p[1]})),backgroundColor:'#56e0d0'},{label:'Perfect',type:'line',data:[{x:0,y:0},{x:100,y:100}],borderColor:'#ffffff55',borderDash:[5,5],pointRadius:0}]},
 options:{scales:{x:{min:0,max:100,grid,title:{display:true,text:'simulated label'}},y:{min:0,max:100,grid,title:{display:true,text:'network prediction'}}}}});
const im=[...d.importance].sort((a,b)=>b.value-a.value);
new Chart($('#imp'),{type:'bar',data:{labels:im.map(x=>x.label),datasets:[{data:im.map(x=>x.value),backgroundColor:'#ff9b62'}]},options:{indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{grid,title:{display:true,text:'mean |Δ score| when shuffled'}},y:{grid:{display:false}}}}});
})();
