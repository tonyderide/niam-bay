// ================================================================ BOUCLE COMMUNE DES CHAPITRES VUS DE CÔTÉ (2, 4, 5, 7, 8, 9)
// objets du niveau : {k:'inter',x,y,lib,f,sp,une} · {k:'zone',x,f,y0,y1} · {k:'porte',x,y,h,id} · {k:'arc'|'vap'|'pic',x,y,w,h,per,dur,dec} (rectangles en tuiles)
const SPC={};
function spritesCote(){if(SPC.ok)return;SPC.ok=1;
  SPC.op=fabPerso(TENUES.operateur,['repos','marche','course','saut','chute','touche','garde','poing1','poing2','pied','elan','sol']);
  SPC.doc=forge(18,14,T=>{T.box(1,3,14,10,0,1,1,'#d8d4c0');T.box(3,1,14,10,1,1,1,'#f0ece0');for(let q=0;q<4;q++)T.teinte(5,3+q*2,9,.8,'#6a6a70')},{pas:8});
  SPC.dicta=forge(14,10,T=>{T.box(0,1,14,9,0,3,2,'#2a2e34');T.ell(4,5.5,2.4,2.4,3,.6,'#14181e');T.ell(10,5.5,2.4,2.4,3,.6,'#14181e');T.pix(7,2.4,'#ff3030')},{pas:8});
  SPC.photo=forge(20,18,T=>{T.box(0,0,20,18,0,2,2,'#8a6a40');T.plat(3,3,14,12,1.6,'#d8c8a8');T.teinte(5,7,3,7,'#3a4656');T.teinte(9,6,3,8,'#7a3a3a');T.teinte(13,9,2,5,'#c8b048');T.teinte(6,5.4,1.6,1.6,'#e0b89a');T.teinte(10,4.4,1.6,1.6,'#e0b89a')},{pas:9});
  SPC.lev=[0,1].map(q=>forge(16,22,T=>{T.box(2,6,12,16,0,3,2,'#3a424c');T.plat(6,8,4,10,1,'#14181e');T.cap(8,13,q?12:4,q?5:5,1.4,1.4,3,2,'#c8ccd2');T.ell(q?12:4,5,2.6,2.6,4,2.4,q?'#40ff70':'#E5283C',.6)},{pas:9}));
  SPC.term=forge(22,30,T=>{T.box(1,0,20,18,0,3,2,'#2a323c');T.plat(3,2,16,12,2,'#0a2a30',.9);for(let q=0;q<4;q++)T.teinte(5,4+q*2.4,6+((q*5)%7),.8,'#3FD6E6',1);T.box(8,18,6,12,0,2,2,'#3a424c')},{pas:10})}
function portes(N){for(const o of N.objets)if(o.k==='porte'&&!o.sp){const hp=o.h*TU;o.sp=forge(TU,hp,T=>{T.box(2,0,20,hp,0,4,2,'#56606c');T.rel(2,0,20,hp,(a,b,i,j)=>j%8<2?-1.2:0);T.teinte(2,hp-10,20,5,'#c8a820');for(let q=2;q<22;q+=8)T.teinte(q,hp-10,4,5,'#20242a')},{pas:10})}}
function coteDebut(N,o){o=o||{};spritesCote();portes(N);for(const ob of N.objets){ob.vu=false;if(ob.k==='porte'){ob.ouv=0;ob.ouverte=false;for(let q=0;q<ob.h;q++)N.G.g[ob.y+q][ob.x]='D'}}
  const d=o.x?[+o.x,N.depart[1]]:N.depart;
  S={t:0,N,j:joueurNouveau(d[0]*TU+12,d[1]*TU),cam:{x:0,y:0},vies:3,pouss:[],motes:ambianceNouv(46),proche:null,ckp:d.slice(),glitch:0,flash:0,flashC:'229,40,60',secousse:0,reinit:false,pause:false,fini:false,dialogue:false,amb:N.amb||'calme',q:[],friables:{},maxX:0};
  if(o.x)for(const ob of N.objets)if(ob.k==='zone'&&ob.x<+o.x)ob.vu=true;
  camSuit(N,S.cam,S.j,0,true);N.friable=(tx,ty)=>{const k=tx+','+ty;if(!S.friables[k])S.friables[k]={t:0,tx,ty}}}
const dans=(j,o)=>j.x+JL>o.x*TU&&j.x-JL<(o.x+o.w)*TU&&j.y>o.y*TU&&j.y-JH<(o.y+o.h)*TU;
const actif=(o,t)=>!o.per||((t+(o.dec||0))%o.per)<o.dur;
function coteDegat(retour){const j=S.j;if(j.inv>0||AUTO)return;S.vies--;S.flash=.35;S.secousse=.3;sfx.touche();vibre(120);j.inv=1.8;j.vy=-260;
  if(retour||S.vies<=0){j.x=S.ckp[0]*TU+12;j.y=S.ckp[1]*TU;j.vx=j.vy=0}
  if(S.vies<=0){S.pause=true;const N=S.N;if(S.reinit){S.vies=3;setTimeout(()=>{S.pause=false},700);aria('Réinitialisation indisponible. Reprise au point de contrôle.')}
    else reinitPage(()=>{S.reinit=true;S.vies=3;S.pause=false;aria('Réinitialisation terminée. Tu vois ? Tu peux me faire confiance.')},()=>{S.vies=3;S.pause=false})}}
function ouvrePorte(id){for(const o of S.N.objets)if(o.k==='porte'&&o.id===id&&!o.ouverte){o.ouverte=true;sfx.porte();for(let q=0;q<o.h;q++)S.N.G.g[o.y+q][o.x]='.'}}
function coteMaj(dt){const N=S.N,j=S.j;S.t+=dt;S.flash=Math.max(0,S.flash-dt);S.glitch=Math.max(0,S.glitch-dt);S.secousse=Math.max(0,S.secousse-dt);
  for(let i=S.q.length-1;i>=0;i--)if(S.q[i][0]<=S.t){const f=S.q[i][1];S.q.splice(i,1);f();if(!S||S.fini)return}
  const c=cmdLire();if(AUTO)c.dx=1;if(S.gel)c.dx=0,c.saut=false;majJoueur(N,j,dt,c);camSuit(N,S.cam,j,dt);S.maxX=Math.max(S.maxX,j.x);
  S.proche=null;let dm=40;
  for(const o of N.objets){
    if(o.k==='zone'){if(!o.vu&&j.x>o.x*TU&&(o.y0===undefined||(j.y>o.y0*TU&&j.y<=o.y1*TU))){o.vu=true;o.f(o)}}
    else if(o.k==='inter'){if(o.vu&&o.une)continue;const d=Math.hypot(j.x-(o.x*TU+12),(j.y-20)-(o.y*TU-12));if(d<dm){dm=d;S.proche=o}}
    else if(o.k==='porte'){if(o.ouverte&&o.ouv<1)o.ouv=Math.min(1,o.ouv+dt*1.4)}
    else if(o.k==='ckp'){if(!o.vu&&j.x>o.x*TU){o.vu=true;S.ckp=[o.x,o.y]}}
    else if(actif(o,S.t)&&dans(j,o))coteDegat(o.k==='pic')}
  for(const k in S.friables){const f=S.friables[k];f.t+=dt;if(f.t>.45&&!f.tombe){f.tombe=1;N.G.g[f.ty][f.tx]='.';sfx.chute();for(let i=0;i<6;i++)S.pouss.push({x:f.tx*TU+rnd()*TU,y:f.ty*TU,vx:(rnd()-.5)*30,vy:rnd()*60,l:.6,c:'#6a5a48'})}if(f.t>4){N.G.g[f.ty][f.tx]='~';delete S.friables[k]}}
  if(j.y>N.Hp+60)coteDegat(true);
  for(const p of S.pouss){p.x+=p.vx*dt;p.y+=p.vy*dt;p.vy+=(p.g===undefined?200:p.g)*dt;p.l-=dt}S.pouss=S.pouss.filter(p=>p.l>0);
  if(N.maj)N.maj(dt)}
function coteAct(){const o=S.proche;if(!o||S.pause||S.dialogue)return;o.vu=true;sfx.bip();o.f(o)}
function coteHud(){viesHud(S.vies);const b=$('act'),o=S.proche;b.style.visibility=o?'visible':'hidden';if(o)b.textContent=o.lib;if(S.N.hud)S.N.hud()}
function coteDessine(){const N=S.N,j=S.j,cmx=R(S.cam.x),cmy=R(S.cam.y+(N.Hp<H?N.Hp-H:0)),t=S.t;
  cx.save();if(S.secousse>0)cx.translate(R((rnd()-.5)*8*Math.min(1,S.secousse*3)),R((rnd()-.5)*8*Math.min(1,S.secousse*3)));
  cx.drawImage(N.fondLoin,-R(cmx*.12)%240,0);
  if(N.dessineLoin)N.dessineLoin(cmx,cmy);
  poseBandes(N.decor,cmx,cmy);
  // tuiles friables tombées : cache
  for(const k in S.friables){const f=S.friables[k];if(f.tombe){cx.fillStyle='rgba(8,10,16,.82)';cx.fillRect(f.tx*TU-cmx,f.ty*TU-cmy,TU,7)}else{cx.fillStyle='rgba(255,220,160,'+(.3*Math.sin(t*40)+.3)+')';cx.fillRect(f.tx*TU-cmx,f.ty*TU-cmy+(rnd()*2|0),TU,2)}}
  for(const o of N.objets){const ox=o.x*TU-cmx,oy=o.y*TU-cmy;if(ox<-200||ox>W+200)continue;
    if(o.k==='porte'){if(o.ouv<1){const hp=o.h*TU,v=R(hp*(1-o.ouv));cx.drawImage(o.sp,0,hp-v,TU,v,ox,oy,TU,v)}}
    else if(o.k==='inter'){if(o.sp&&!(o.vu&&o.cache)){const s=typeof o.sp==='function'?o.sp(o):o.sp;cx.drawImage(s,R(ox+12-s.width/2),R(oy-s.height-(o.dy||0)))}}
    else if(o.k==='arc'){if(actif(o,t)){cx.strokeStyle='#bff6ff';cx.lineWidth=2;cx.beginPath();for(let q=0;q<3;q++){let x=ox+rnd()*o.w*TU,y=oy+o.h*TU;cx.moveTo(x,y);for(let s=0;s<5;s++){x+=(rnd()-.5)*18;y-=o.h*TU/5;cx.lineTo(x,y)}}cx.stroke();cx.strokeStyle='#3FD6E6';cx.lineWidth=1;cx.stroke();if(rnd()<.3)S.pouss.push({x:o.x*TU+rnd()*o.w*TU,y:(o.y+o.h)*TU,vx:(rnd()-.5)*120,vy:-rnd()*160,l:.3,c:'#eaffff'});if(rnd()<.04)sfx.elec()}
      else if(((t+(o.dec||0))%o.per)>o.per-.5&&rnd()<.5){cx.fillStyle='#eaffff';cx.fillRect(ox+rnd()*o.w*TU,oy+o.h*TU-3,2,2)}}
    else if(o.k==='vap'){if(actif(o,t)){for(let q=0;q<3;q++)S.pouss.push({x:(o.x+o.w/2)*TU+(rnd()-.5)*8,y:(o.y+o.h)*TU,vx:(rnd()-.5)*26,vy:-o.h*TU*1.5-rnd()*40,l:.6,c:'v',g:0})}else if(rnd()<.1)S.pouss.push({x:(o.x+o.w/2)*TU,y:(o.y+o.h)*TU,vx:(rnd()-.5)*10,vy:-30,l:.4,c:'v',g:0})}}
  if(N.dessineAvant)N.dessineAvant(cmx,cmy);
  // joueur
  if(!S.cacheJoueur&&(j.inv<=0||Math.floor(j.inv*14)%2))poseSprite(imageJoueur(N.persoJ||SPC.op,j),j.x-cmx,j.y-cmy,j.dir);
  for(const p of S.pouss){if(p.c==='v'){cx.fillStyle='rgba(215,225,235,'+Math.min(.5,p.l)+')';const s=R(10-p.l*8);cx.fillRect(R(p.x-cmx-s/2),R(p.y-cmy-s/2),s,s)}else{cx.fillStyle=p.c;cx.fillRect(R(p.x-cmx),R(p.y-cmy),2,2)}}
  // éclairage
  lumDebut(N.ambCol||N.Th.amb);
  for(const[lx,ly,c,pas]of N.lampes||[]){const x=lx*TU+12-cmx,y=ly*TU+24-cmy;if(x<-220||x>W+220)continue;const fl=pas&&Math.sin(t*23+lx)*Math.sin(t*7.3+lx)>.3?.35:1;lumPoint(x,y+40,300,c||'#ffd9a0',fl)}
  for(const[fx,fy,fw,fh]of N.fenetres||[]){const x=(fx+fw/2)*TU-cmx,y=(fy+fh/2)*TU-cmy;if(x<-260||x>W+260)continue;lumPoint(x,y,Math.max(fw,fh)*TU*1.7,'#8fa6d8',.75);lumPoint(x+fh*TU*.5,y+fh*TU*1.1,fw*TU*2.6,'#8fa6d8',.4)}
  if(!S.cacheJoueur){lumPoint(j.x-cmx+j.dir*34,j.y-cmy-30,170,'#bfeeff',.8);lumPoint(j.x-cmx,j.y-cmy-22,90,'#dff6ff',.6)}
  for(const o of N.objets){if(o.k==='inter'&&o.lueur&&!(o.vu&&o.une))lumPoint(o.x*TU+12-cmx,o.y*TU-10-cmy,70,o.lueur,.6+.3*Math.sin(t*4));if(o.k==='arc'&&actif(o,t))lumPoint((o.x+o.w/2)*TU-cmx,(o.y+o.h/2)*TU-cmy,150,'#9feaff',.9)}
  if(N.lumieres)N.lumieres(cmx,cmy);
  lumFin();
  // rayons de lune, poussières, marqueur d'interaction
  cx.globalCompositeOperation='lighter';for(const[fx,fy,fw,fh,st]of N.fenetres||[]){if(st==='trou'&&!N.rayonsTrou)continue;const x=fx*TU-cmx,y=(fy+fh)*TU-cmy,w=fw*TU,L=260;if(x<-400||x>W+100)continue;const g=cx.createLinearGradient(0,y-fh*TU,0,y+L);g.addColorStop(0,'rgba(150,175,235,.13)');g.addColorStop(1,'rgba(150,175,235,0)');cx.fillStyle=g;cx.beginPath();cx.moveTo(x,y-fh*TU);cx.lineTo(x+w,y-fh*TU);cx.lineTo(x+w+L*.55,y+L);cx.lineTo(x+L*.55-20,y+L);cx.fill()}cx.globalCompositeOperation='source-over';
  ambianceDessine(S.motes,t,1/60);
  if(N.dessineApres)N.dessineApres(cmx,cmy);
  if(S.proche){const o=S.proche,x=o.x*TU+12-cmx,y=o.y*TU-34-cmy-(o.dy||0)+Math.sin(t*5)*2;cx.fillStyle='#3FD6E6';cx.fillRect(R(x-1),R(y-8),3,7);cx.fillRect(R(x-1),R(y+1),3,3)}
  // premier plan sombre (parallaxe)
  if(N.avant!==false){cx.fillStyle='#04060a';for(let i=0;i<8;i++){const x=R(i*520+210-cmx*1.35);if(x<-40||x>W+10)continue;cx.fillRect(x,0,16,H);cx.fillRect(x-5,R(H*.2),26,5);cx.fillRect(x-5,R(H*.62),26,5)}
    for(let i=0;i<10;i++){const x=R(i*410+70-cmx*1.2),l=90+(i*53)%120;if(x<-10||x>W+10)continue;for(let y=0;y<l;y+=6)cx.fillRect(x+(y%12?0:1),y,2,4);cx.fillRect(x-3,l,8,6)}}
  cx.restore();
  poseVoile(false);
  if(S.flash>0){cx.fillStyle='rgba('+S.flashC+','+Math.min(.85,S.flash)+')';cx.fillRect(0,0,W,H)}
  if(S.glitch>0)glitch()}
const coteChap=o=>Object.assign({maj:coteMaj,dessine:coteDessine,hud:coteHud,act:coteAct,bas:cmdBas,bouge:cmdBouge,haut:cmdHaut,touche(k){if(k==='e'||k==='Enter')coteAct()},etat(){return 'x='+(S.j.x/TU).toFixed(1)+' y='+(S.j.y/TU).toFixed(1)+' vies '+S.vies+' cam '+R(S.cam.y)+' H '+H+' Hp '+S.N.Hp+' ih '+innerHeight}},o);
const apres=(d,f)=>S.q.push([S.t+d,f]);
// flamme animée (images des explosions en boucle, mélange additif) ; x,y = base en pixels écran
function flamme(x,y,ech,i){if(!SP.feu)SP.feu=[flammes(3),flammes(17),flammes(41)];cx.globalCompositeOperation='lighter';for(let q=0;q<3;q++){const f=SP.feu[(i+q)%3][2+Math.floor((S.t*11+i*3+q*2)%5)],w=R(46*ech*(1-q*.22)),h=R(64*ech*(1-q*.2));cx.drawImage(f,R(x-w/2+Math.sin(S.t*7+q+i)*3),R(y-h*.82-q*9*ech),w,h)}cx.globalCompositeOperation='source-over'}
// contrôle d'accessibilité d'un niveau (essais) : cases où l'on peut se tenir, marche, saut de 3 cases de haut et 4 de large, chute
function accessible(N){const G=N.G,ok=(x,y)=>!plein(G.get(x,y-1))&&!plein(G.get(x,y-2))&&(plein(G.get(x,y))||G.get(x,y)==='='||G.get(x,y)==='~')&&G.get(x,y)!=='D'&&x>=0&&x<G.c,vu=new Set(),f=[[N.depart[0],N.depart[1]]];vu.add(f[0].join());
  const libreCol=(x,y0,y1)=>{for(let y=y0;y<=y1;y++)if(plein(G.get(x,y)))return false;return true};
  while(f.length){const[x,y]=f.pop();for(let dx=-4;dx<=4;dx++)for(let ny=y-3;ny<G.r;ny++){const nx=x+dx;if(!ok(nx,ny)||vu.has(nx+','+ny))continue;const up=y-ny,ad=Math.abs(dx);
      if(up>0){if(ad>(up>=3?2:3))continue;if(!libreCol(x,ny-2,y-1))continue}else if(ny>y){if(ad>4)continue;let lib=true;for(let q=Math.min(x,nx);q<=Math.max(x,nx);q++)if(plein(G.get(q,y-1))||plein(G.get(q,y-2)))lib=false;if(!lib||!libreCol(nx,y-1,ny-1))continue}
      else{if(ad>4)continue;if(ad>1){let lib=true;for(let q=Math.min(x,nx);q<=Math.max(x,nx);q++)if(plein(G.get(q,y-1))||plein(G.get(q,y-3)))lib=false;if(!lib)continue}}
      vu.add(nx+','+ny);f.push([nx,ny])}}
  const man=[];for(const o of N.objets){if(o.k!=='inter'&&o.k!=='zone')continue;const x=Math.floor(o.x);let a=false;for(let d=-1;d<=1;d++)for(let y=0;y<G.r;y++)if(vu.has((x+d)+','+y)&&(o.k==='zone'?(o.y0===undefined||(y>o.y0&&y<=o.y1)):Math.abs(y-o.y)<=1))a=true;if(!a)man.push(o.k+'@'+o.x+','+(o.y||''))}return man}
