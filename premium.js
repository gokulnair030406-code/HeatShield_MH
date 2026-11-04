
(()=>{'use strict';
 const clock=document.getElementById('liveClock');
 const tick=()=>{if(clock)clock.textContent=new Intl.DateTimeFormat('en-IN',{weekday:'short',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date())+' IST'};
 tick();setInterval(tick,1000);
 const canvas=document.getElementById('ambientCanvas');
 if(canvas){const ctx=canvas.getContext('2d');let w=0,h=0,pts=[];
  const resize=()=>{w=canvas.width=innerWidth*devicePixelRatio;h=canvas.height=innerHeight*devicePixelRatio;canvas.style.width=innerWidth+'px';canvas.style.height=innerHeight+'px';pts=Array.from({length:Math.min(65,Math.floor(innerWidth/19))},()=>({x:Math.random()*w,y:Math.random()*h,vx:(Math.random()-.5)*.18,vy:(Math.random()-.5)*.18,r:Math.random()*1.5+.4}))};
  resize();addEventListener('resize',resize);
  const draw=()=>{ctx.clearRect(0,0,w,h);for(let i=0;i<pts.length;i++){let p=pts[i];p.x+=p.vx*devicePixelRatio;p.y+=p.vy*devicePixelRatio;if(p.x<0||p.x>w)p.vx*=-1;if(p.y<0||p.y>h)p.vy*=-1;ctx.beginPath();ctx.arc(p.x,p.y,p.r*devicePixelRatio,0,Math.PI*2);ctx.fillStyle='#75e8d0';ctx.globalAlpha=.42;ctx.fill();for(let j=i+1;j<pts.length;j++){let q=pts[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.hypot(dx,dy);if(d<125*devicePixelRatio){ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.strokeStyle='#69dcca';ctx.globalAlpha=(1-d/(125*devicePixelRatio))*.09;ctx.stroke()}}}ctx.globalAlpha=1;requestAnimationFrame(draw)};draw();
 }
 const modal=document.getElementById('commandModal'),input=document.getElementById('commandInput'),results=document.getElementById('commandResults');
 const open=()=>{if(!modal)return;modal.classList.add('open');modal.setAttribute('aria-hidden','false');input.value='';filter('');setTimeout(()=>input.focus(),30)};
 const close=()=>{if(!modal)return;modal.classList.remove('open');modal.setAttribute('aria-hidden','true')};
 const filter=q=>{if(!results)return;[...results.querySelectorAll('a')].forEach(a=>a.style.display=a.textContent.toLowerCase().includes(q.toLowerCase())?'grid':'none')};
 document.getElementById('commandHint')?.addEventListener('click',open);
 input?.addEventListener('input',e=>filter(e.target.value));
 input?.addEventListener('keydown',e=>{if(e.key==='Enter'){const a=[...results.querySelectorAll('a')].find(x=>x.style.display!=='none');if(a)location.href=a.href}});
 modal?.addEventListener('click',e=>{if(e.target===modal)close()});
 document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();open()}if(e.key==='Escape')close()});
})();
