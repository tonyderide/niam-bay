// ================================================================ CHAPITRE 1 · INITIALISATION : shoot'em up vertical au-dessus de Paris
const EXN=14,FEU=72;
const C1={pret:false,seq:[],stop:0};
function spritesCh1(){const o=(x)=>Object.assign({sym:1,k:K},x);
  SP.joueur=forge(35,33,T=>{
    T.poly([[17.5,2],[14,10],[2,24],[1,29],[9,28],[13,31],[17.5,29]],0,4,5,'#b9c4ce');
    T.poly([[17.5,12],[6,24],[9,26],[17.5,22]],3.4,1.4,2,'#d6dee6');
    T.poly([[17.5,4],[15,12],[12.5,22],[14,28],[17.5,27]],3,5,4,'#eef2f5',1);
    T.ell(17.5,10.5,1.9,3.4,7.5,1.8,'#12bfe2');T.pix(17,9,'#dffaff');
    T.teinte(13,15,2,5,'#161c24');T.teinte(2,27,5,1,'#E5283C');T.teinte(14,29,3,1,'#9ff2ff',1);T.teinte(9.5,21,2,.7,'#E5283C');
    T.trait(12.5,22,17.5,24);T.trait(5,25,13,19);T.trait(9,28,12,23);T.trait(14.6,13,17.5,14.5,.7);T.trait(3,26.5,8,22,.7);T.trait(15.6,18,15.6,26,.6);
    T.box(6.4,17,1.4,7,3,1.6,.6,'#8a96a2');T.pix(6.9,17,'#ffd27a');T.lum(2,24,'#ff5a6a');T.pix(11,20,'#3FD6E6',.8)},o({poli:30}));
  SP.drone=forge(25,25,T=>{
    T.poly([[4,4],[7,3],[14,10],[11,13]],1,1.6,1.2,'#7a8490');T.poly([[4,21],[7,22],[14,15],[11,12]],1,1.6,1.2,'#7a8490');
    T.ell(5,5,4.6,4.6,1.4,1.2,'#1c222a');T.ell(5,5,1.6,1.6,2.6,2,'#c9d2da');T.ell(5,20,4.6,4.6,1.4,1.2,'#1c222a');T.ell(5,20,1.6,1.6,2.6,2,'#c9d2da');
    T.box(8,8,9,9,2,4.5,4,'#49525e',1);T.ell(12.5,14.5,2.4,2.4,6.5,1.5,'#ff3048',1);T.pix(12.2,14,'#ffd0d6');T.trait(8,10,12.5,9);T.teinte(11,8,3,1,'#e8eef2');
    T.trait(9,16,12.5,17,.7);T.pix(9.4,11.4,'#ffd27a');T.teinte(10,17.4,5,.7,'#E5283C');T.pix(5,5,'#ffffff',.5);T.pix(5,20,'#ffffff',.5)},o());
  SP.aile=forge(35,33,T=>{
    T.poly([[17.5,6],[3,3],[1,8],[13,23],[17.5,31]],0,3.2,3.2,'#59665a');
    T.poly([[17.5,10],[7,8],[13,18],[17.5,22]],3,1.4,2,'#75836f');
    T.poly([[17.5,32],[15,23],[14.5,5],[17.5,2]],2,5,3,'#9aa593',1);
    T.ell(17.5,27,1.7,2.6,6,1.6,'#ff3048',.9);T.teinte(1,5,3,3,'#262c2a');T.teinte(15,3,3,1,'#30363a');
    T.trait(6,9,13,20);T.trait(14.5,14,17.5,13);T.trait(4,5,11,8,.7);T.trait(9,12,14.6,12,.6);T.teinte(8,9.6,3,.7,'#d8c040');T.box(10,13,1.3,6,3,1.4,.5,'#3a4038');T.pix(10.5,19,'#ff9a18');
    T.lum(3,3,'#ff5a6a');T.pix(16.6,8,'#cfd8c8',.4)},o());
  SP.kami=forge(19,25,T=>{
    T.box(1,9,8,4,0,2.2,1.5,'#6b7580');T.box(4,2,5,3,0,1.8,1.2,'#6b7580');
    T.poly([[9.5,24],[6.5,17],[6.5,2],[9.5,1]],1,4.5,2.6,'#c3ccd4',1);
    T.teinte(7,19,3,4,'#E5283C');T.pix(9,22,'#ffd0d6');T.teinte(1,10,2,2,'#E5283C');T.trait(6.5,15,9.5,15);T.trait(6.5,8,9.5,8,.7);T.teinte(7,10,2.5,.7,'#e8b020');T.pix(4.5,2.4,'#ff9a18')},o());
  SP.lourd=forge(67,61,T=>{
    for(const[x,y]of[[9,10],[5,30],[9,50]]){T.poly([[x,y-2],[x,y+2],[33.5,32],[33.5,28]],2,2.2,1.6,'#69737f');T.ell(x,y,8.4,8.4,1,4.5,'#4a535f');T.trou(x,y,6,6,.6,'#10141a');T.ell(x,y,1.8,1.8,2,2.6,'#c9d2da');for(let a=0;a<6;a++)T.pix(x+Math.cos(a)*7.4,y+Math.sin(a)*7.4,'#8d98a4',.2)}
    T.poly([[33.5,12],[24,16],[20,26],[20,36],[24,46],[33.5,50]],3,6,6,'#56616d');
    T.poly([[33.5,17],[27,20],[24,27],[24,35],[27,42],[33.5,45]],9,3,3,'#75808c');
    T.box(21,40,4,15,2,3,2,'#c4ccd2',1);T.box(27,44,3,12,2,2.6,1.5,'#c4ccd2',1);T.pix(22.8,54.4,'#ff9a18');T.pix(28.3,55.4,'#ff9a18');
    T.ell(33.5,31,6.5,6.5,12,3,'#20262e');T.ell(33.5,31,3.6,3.6,15,2,'#ff3048',1);T.teinte(32,29,3,3,'#ffd0d6',1);
    T.teinte(22,22,5,2,'#e8b020');T.teinte(24,24,2,1,'#20262e');T.box(31,6,5,8,3,3,2,'#aab4be',1);
    T.trait(24,27,20,26);T.trait(24,35,20,36);T.trait(27,20,24,16);T.trait(27,42,24,46);T.trait(28,23,33.5,21,.7);T.trait(28,39,33.5,41,.7);T.trait(26,31,29,31,.7);
    for(const[x,y]of[[25,19],[22,31],[25,43],[30,14],[30,48]])T.pix(x,y,'#aab4be',.3);T.lum(9,2,'#ff5a6a');T.lum(9,58,'#ff5a6a');T.pix(1,30,'#40ff70')},o());
  SP.boss=forge(181,133,T=>{
    for(const y of[30,100]){T.ell(28,y,25,25,1,7,'#4a5565');T.trou(28,y,19,19,.6,'#0e1218');T.ell(28,y,4.5,4.5,2,4,'#c9d2da');T.trait(4,y,9,y);T.trait(47,y,52,y);for(let a=0;a<TAU;a+=.4){T.pix(28+Math.cos(a)*22.6,y+Math.sin(a)*22.6,'#7c8898',.2)}
      for(const a of[.8,2.4,3.9,5.5])T.cap(28+Math.cos(a)*5,y+Math.sin(a)*5,28+Math.cos(a)*19,y+Math.sin(a)*19,.9,.9,1.4,1.4,'#39424e')}
    T.poly([[40,38],[72,52],[72,64],[34,50]],3,4,3.5,'#5a6880');T.poly([[40,92],[72,80],[72,68],[34,80]],3,4,3.5,'#5a6880');
    T.poly([[28,52],[36,54],[36,78],[28,80],[22,66]],2,4,3,'#465162');
    T.box(52,58,10,30,4,5.5,4.5,'#77849a',1);T.box(55,86,4,14,4,3.4,2,'#cdd5dd',1);T.box(46,60,4,10,4,3,1.6,'#cdd5dd',1);
    T.poly([[90.5,20],[72,28],[62,54],[62,84],[74,112],[90.5,124]],3,9,10,'#465162');
    T.poly([[90.5,30],[76,36],[68,56],[68,82],[78,104],[90.5,112]],12,4,4,'#6f7d92');
    T.poly([[90.5,96],[80,88],[76,66],[82,48],[90.5,44]],16,4,4,'#222932');
    T.ell(90.5,68,15,15,20,3,'#aab4be');T.ell(90.5,68,11,11,22,5,'#ff3048',1);T.ell(90.5,67,4.6,4.6,27,1,'#ffd0d6',1);
    T.box(87,2,7,22,6,4,3,'#aab4be',1);T.ell(90.5,9,8,8,9,4,'#dfe6ec');T.ell(90.5,9,2.5,2.5,13,2,'#ff3048',1);for(let a=0;a<TAU;a+=.52)T.trait(90.5+Math.cos(a)*3,9+Math.sin(a)*3,90.5+Math.cos(a)*7.4,9+Math.sin(a)*7.4,.6);
    T.poly([[90.5,124],[84,116],[86,106],[90.5,104]],12,3,2.5,'#cdd5dd');
    T.teinte(53,60,8,2,'#e8b020');T.teinte(64,54,3,10,'#e8b020');T.teinte(76,34,6,2,'#E5283C');T.teinte(24,54,8,2,'#E5283C');
    for(let q=0;q<5;q++)T.teinte(64,55+q*2,3,.8,'#20262e');
    T.trait(68,56,76,66);T.trait(68,82,80,88);T.trait(62,70,68,70);T.trait(76,36,82,48);T.trait(78,104,84,96);T.trait(40,45,70,58);T.trait(40,86,70,74);T.trait(74,112,78,104);
    T.trait(70,40,74,56,.7);T.trait(66,90,72,100,.7);T.trait(80,30,86,40,.7);T.trait(84,100,90.5,102,.7);T.trait(72,62,76,62,.7);T.trait(72,76,76,76,.7);
    for(const[x,y]of[[70,46],[66,62],[66,78],[72,96],[82,112],[84,28],[78,58],[78,80]])T.pix(x,y,'#9aa6b6',.3);
    for(let q=0;q<6;q++){T.pix(80+q*1.6,40,'#3FD6E6',.9)}
    for(const[x,y]of[[36,52],[36,80],[66,44],[66,96],[72,28],[80,116]])T.lum(x,y,'#ffd27a');T.lum(3,30,'#ff5a6a');T.lum(3,100,'#ff5a6a')},o({pas:11}));
  SP.module=forge(15,15,T=>{T.box(0,0,15,15,0,3,3,'#19b8d0');T.teinte(3,3,9,9,'#06222c');for(const[x,y,w,h]of[[5,4,2,7],[5,4,5,1],[5,7,5,1],[9,4,1,4]])T.teinte(x,y,w,h,'#eaffff',1)},{k:K});
  SP.nuage=(()=>{const c=toile(200,110),g=c.getContext('2d');for(let i=0;i<12;i++){const x=30+rnd()*140,y=24+rnd()*60,r=16+rnd()*26,gr=g.createRadialGradient(x,y,0,x,y,r);gr.addColorStop(0,'rgba(150,175,225,.15)');gr.addColorStop(1,'rgba(150,175,225,0)');g.fillStyle=gr;g.fillRect(0,0,200,110)}return c})();
  const orbe=(d,c)=>{const F=[];for(let q=0;q<2;q++){const t=toile(d,d),g=t.getContext('2d'),ig=g.createImageData(d,d),p=ig.data;for(let y=0;y<d;y++)for(let x=0;x<d;x++){const u0=Math.hypot(x+.5-d/2,y+.5-d/2)/(d/2);if(u0>=1)continue;const col=u0<.34+q*.14?'#ffffff':u0<.6+q*.06?c[2]:u0<.84?c[1]:c[0],u=hx(col),i=(y*d+x)*4;p[i]=u[0]*255;p[i+1]=u[1]*255;p[i+2]=u[2]*255;p[i+3]=255}g.putImageData(ig,0,0);F.push(t)}return F};
  SP.balle=[orbe(13,['#5a0610','#e5283c','#ff9aa3']),orbe(19,['#5a0610','#e5283c','#ff9aa3'])];
  SP.aig=[];for(let q=0;q<24;q++){const t=toile(25,25),g=t.getContext('2d');g.translate(12.5,12.5);g.rotate(q*TAU/24);for(const[c,a,b]of[['#a83a00',12,5],['#ff9a18',10,3.4],['#fff2c0',7,1.6]]){g.fillStyle=c;g.beginPath();g.ellipse(0,0,a,b,0,0,7);g.fill()}
    const ig=t.getContext('2d').getImageData(0,0,25,25);for(let i=3;i<ig.data.length;i+=4)ig.data[i]=ig.data[i]>110?255:0;g.setTransform(1,0,0,1,0,0);g.putImageData(ig,0,0);SP.aig.push(t)}
  SP.h=[halo('255,50,70',48),halo('255,50,70',60),halo('255,150,40',48),halo('60,210,255',48),halo('255,170,70',96),halo('255,50,70',96)];
  SP.tir=(()=>{const t=toile(10,30),g=t.getContext('2d');Rc(g,'#0b5c66',1,5,8,23);Rc(g,'#1fa8bc',2,3,6,22);Rc(g,'#3FD6E6',3,0,4,28);Rc(g,'#eaffff',4,0,2,24);return t})();
  SP.feu=[flammes(3),flammes(17),flammes(41)]}
// explosions : boules de feu calculées image par image
function flammes(seed){const r=hasard(seed),B=[],D=FEU,m=D/48;for(let i=0;i<10;i++)B.push({a:r()*TAU,d:i?4+r()*9:0,r:6+r()*7,t0:i?r()*.28:0});
  const F=[],Rr=[[.8,255,252,226],[.6,255,224,84],[.42,255,146,32],[.26,214,62,26],[.12,110,36,34]];
  for(let q=0;q<EXN;q++){const t=q/(EXN-1),c=toile(D,D),g=c.getContext('2d'),ig=g.createImageData(D,D),p=ig.data;
    for(let y=0;y<D;y++)for(let x=0;x<D;x++){let hs=-9,fm=0;const X=(x+.5)/m,Y=(y+.5)/m;for(const b of B){const tt=t-b.t0;if(tt<0)continue;const e=Math.min(1,tt*2.4),mm=.4+e*.9,bx=24+Math.cos(b.a)*b.d*mm,by=24+Math.sin(b.a)*b.d*mm-t*3,d=Math.hypot(X-bx,Y-by)/(b.r*(.45+.75*Math.sqrt(e)));if(d<1){hs=Math.max(hs,(1-d*d)*1.3-tt*1.25);fm=Math.max(fm,1-d)}}
      if(fm<=0)continue;const nz=((((x*73856093)^(y*19349663)^(q*83492791))>>>0)%100)/100*.12-.06,v=hs+nz,i=(y*D+x)*4;let okk=0;
      for(const u of Rr)if(v>u[0]){p[i]=u[1];p[i+1]=u[2];p[i+2]=u[3];p[i+3]=255;okk=1;break}
      if(!okk&&fm+nz>.18){const oo=fm+nz>.5?62:40;p[i]=oo;p[i+1]=oo-4;p[i+2]=oo+4;p[i+3]=Math.max(0,Math.min(1,(1.05-t)*1.6))*210}}
    g.putImageData(ig,0,0);F.push(c)}return F}

const SEQ1=['h1','gare','h2','seine','louvre','h1','opera','h2','etoile','h1','eiffel'];
CH[1]={
 async prep(etape){await etape('Armement, cibles…',.05);spritesCh1();C1.t={};
   const L1=[['h1','h',7,'Acquisition satellite · 9e arrondissement'],['gare','gare',11,'Acquisition satellite · gare du Nord'],['h2','h',23,'Acquisition satellite · Marais'],['seine','seine',5,'Acquisition satellite · île de la Cité'],['louvre','louvre',9,'Acquisition satellite · Louvre'],['opera','opera',13,'Acquisition satellite · Opéra'],['etoile','etoile',17,'Acquisition satellite · Étoile'],['eiffel','eiffel',29,'Acquisition satellite · Champ-de-Mars']];
   let i=0;for(const[k,t,g,txt]of L1){await etape(txt,.1+.9*i/L1.length);C1.t[k]=paris(t,g);i++}},
 debut(o){nouveau1(o.t||0,null)},
 maj:maj1,dessine:dessine1,hud:hud1,act:purge,
 bas(x,y){C1.ox=S.px-x;C1.oy=S.py-y},
 bouge(x,y){S.px=lim(x+C1.ox,10,GW-10);S.py=lim(y+C1.oy,40,GH-36)},
 touche(k){if(k==='x'||k==='b'||k===' ')purge()},
 etat(){return 't='+S.t.toFixed(0)+' tues '+S.tues+' niv '+S.niv+' boss '+(S.boss?R(S.boss.pv):'-')+(S.fini?' FINI':'')}};
function nouveau1(t0,garde){
  S={t:t0,px:GW/2,py:GH-90,vies:3,inv:2,niv:garde?garde.niv:1,purges:2,purgeT:0,score:garde?garde.score:0,tues:garde?garde.tues:0,chaine:0,chaineT:0,maxChaine:garde?garde.maxChaine:0,
     pb:[],eb:[],en:[],it:[],ex:[],et:[],ondes:[],ep:[],q:scenario1().filter(e=>e[0]>=t0),boss:null,tirT:0,secousse:0,flash:0,flashC:'255,255,255',glitch:0,
     pause:false,fini:false,reinit:garde?garde.reinit:false,defil:t0*36,amb:'mil',
     nuages:[0,1,2,3].map(i=>({x:rnd()*GW,y:i*GH/4,v:40+rnd()*40}))};
  C1.stop=10*FH+(FH-350)-GH*.58;S.defil=Math.min(S.defil,C1.stop);
  hudCfg('UNITÉS NEUTRALISÉES','PURGE ×2');aria('…');ecran(null);hud1()}
const plus=(d,f)=>S.q.push([S.t+d,f]);
const tire=(x,y,a,v,s)=>{if(S.eb.length<560)S.eb.push({x,y,vx:Math.cos(a)*v,vy:Math.sin(a)*v,s,ai:R(((a%TAU)+TAU)%TAU/TAU*24)%24})};
const vise=(x,y)=>Math.atan2(S.py-y,S.px-x);
const eventail=(x,y,n,ec,v,s,a0)=>{const a=a0===undefined?vise(x,y):a0;for(let i=0;i<n;i++)tire(x,y,a+(i-(n-1)/2)*ec,v,s)};
const anneau=(x,y,n,v,s,ph)=>{for(let i=0;i<n;i++)tire(x,y,ph+i*TAU/n,v,s)};
const DEF={
 drone:{s:'drone',pv:2,r:8,pts:100,g:.15,rot:[[-7.5,-7.5,4.5],[7.5,-7.5,4.5],[-7.5,7.5,4.5],[7.5,7.5,4.5]],maj(e,dt){e.y+=58*dt;e.x=e.x0+e.dir*Math.sin(e.t*1.7)*46;e.c-=dt;if(e.c<=0&&e.y>20&&e.y<GH*.55){e.c=2.8;tire(e.x,e.y,vise(e.x,e.y),72,0)}}},
 aile:{s:'aile',pv:6,r:10,pts:300,g:.3,rot:[[0,-15,3.5]],maj(e,dt){if(!e.vire){e.y+=150*dt;if(e.y>GH*(.25+e.p*.2)){e.vire=1;e.vx=e.x<GW/2?1:-1;eventail(e.x,e.y,3,.2,100,2)}}else{e.vv=(e.vv||0)+220*dt;e.x+=e.vx*e.vv*dt;e.y+=Math.max(-40,150-e.vv)*dt}}},
 kami:{s:'kami',pv:3,r:6,pts:200,g:.2,maj(e,dt){if(!e.a){e.a=vise(e.x,e.y);e.v=60}e.v+=170*dt;e.x+=Math.cos(e.a)*e.v*dt;e.y+=Math.sin(e.a)*e.v*dt}},
 lourd:{s:'lourd',pv:80,r:20,pts:2000,g:.8,cadre:1,rot:[[-24.5,-20.5,6],[24.5,-20.5,6],[-28.5,-.5,6],[28.5,-.5,6],[-24.5,19.5,6],[24.5,19.5,6]],maj(e,dt){if(e.t<e.reste){if(e.y<e.ty)e.y+=55*dt;else e.x+=Math.cos(e.t*.9)*16*dt}else e.y-=50*dt;
   if(e.y<20||e.t>=e.reste)return;e.c-=dt;if(e.c<=0){e.c=1.7;eventail(e.x-11,e.y+24,3,.2,92,2);eventail(e.x+11,e.y+24,3,.2,92,2)}e.c2-=dt;if(e.c2<=0){e.c2=3.4;anneau(e.x,e.y,14,54,1,rnd()*TAU)}}},
 boss:{s:'boss',pv:3600,r:36,pts:50000,g:1,cadre:1,rot:[[-62.5,-36.5,18],[62.5,-36.5,18],[-62.5,33.5,18],[62.5,33.5,18]],maj:majBoss}};
function E(k,x,y,o){const e=Object.assign({k,x,y,t:0,pv:DEF[k].pv,blanc:0,c:.6+rnd(),c2:2,p:rnd()},o);S.en.push(e);return e}
function majBoss(e,dt){
  if(e.y<104){e.y+=38*dt;e.inv=1;return}
  if(e.inv){e.inv=0;e.bt=0;e.ph=1;$('pv').style.display='block';$('alerte').style.display='none'}
  const ph=e.pv>DEF.boss.pv*.66?1:e.pv>DEF.boss.pv*.33?2:3;
  if(ph!==e.ph){e.ph=ph;annule();boum(e.x,e.y,1.2);S.secousse=.5;e.c=1.2;e.c2=1.2;aria(ph===2?'Structure affaiblie. Continue.':`Encore un effort, ${prenom()}. Je suis là.`)}
  e.bt+=dt;e.x=GW/2+Math.sin(e.bt*(ph===3?.95:.5))*(ph===3?40:28);e.c-=dt;e.c2-=dt;
  if(ph===1){if(e.c<=0){e.c=1.35;eventail(e.x-34,e.y+34,5,.2,90,2);eventail(e.x+34,e.y+34,5,.2,90,2)}
    if(e.c2<=0){e.c2=.14;e.a=(e.a||0)+.39;tire(e.x,e.y+2,e.a,56,0);tire(e.x,e.y+2,e.a+Math.PI,56,0)}}
  else if(ph===2){if(e.c2<=0){e.c2=.16;e.a=(e.a||0)+.21;for(let q=0;q<3;q++){tire(e.x,e.y+2,e.a+q*2.094,64,0);tire(e.x,e.y+2,-e.a*1.31+q*2.094,48,1)}}
    if(e.c<=0){e.c=1.9;eventail(e.x-34,e.y+34,3,.1,145,2);eventail(e.x+34,e.y+34,3,.1,145,2)}}
  else{if(e.c<=0){e.c=1.05;e.alt=!e.alt;anneau(e.x,e.y+2,22,60,e.alt?0:1,rnd()*TAU)}
    if(e.c2<=0){e.c2=.24;const c=rnd()<.5?-1:1;tire(e.x+c*(20+rnd()*42),e.y+30,Math.PI/2+(rnd()-.5)*.5,80+rnd()*45,2)}}}
function fx(x,y,r,ret){S.ex.push({x,y,t:-(ret||0),d:.42+r*.007,r,v:(rnd()*3)|0})}
function boum(x,y,g,muet){fx(x,y,11+g*30);const m=(g*6)|0;for(let i=0;i<m;i++){const a=rnd()*TAU,d=rnd()*g*30;fx(x+Math.cos(a)*d,y+Math.sin(a)*d,8+rnd()*g*22,.04+rnd()*.32)}
  if(g>.5)S.ondes.push({x,y,t:0,r:30+g*55});
  const n=(5+g*16)|0;for(let i=0;i<n;i++){const a=rnd()*TAU,v=40+rnd()*160;S.et.push({x,y,vx:Math.cos(a)*v,vy:Math.sin(a)*v,l:.3+rnd()*.5,c:rnd()<.5?'#ffd27a':'#ff7a3d'})}
  const n2=(g*9)|0;for(let i=0;i<n2;i++){const a=rnd()*TAU,v=30+rnd()*90;S.et.push({x,y,vx:Math.cos(a)*v,vy:Math.sin(a)*v-30,l:.6+rnd()*.7,k:1})}
  if(!muet)sfx.boum(g)}
function annule(){for(const b of S.eb)S.et.push({x:b.x,y:b.y,vx:0,vy:-20,l:.35,c:'#ff9aa3'});S.eb=[]}
function tue(e){const d=DEF[e.k];S.tues++;S.chaine++;S.chaineT=1.8;S.maxChaine=Math.max(S.maxChaine,S.chaine);S.score+=R(d.pts*(1+S.chaine*.05));
  boum(e.x,e.y,d.g);
  if(d.pv<10)S.ep.push({x:e.x,y:e.y,vx:(rnd()-.5)*50,vy:36+rnd()*30,t:0,a:rnd()*TAU,va:(rnd()-.5)*9,s:d.s});
  if(e.lache)S.it.push({x:e.x,y:e.y,vy:-30,k:'p'});
  if(e.k==='lourd'){S.secousse=.3;annule()}
  if(e.cri){sfx.cri();second('[SIGNAL AUDIO] « …non, attendez, on est — »','h');plus(.8,()=>{S.glitch=.7;sfx.gl();second('[AUDIO COUPÉ] Interférence. Rien d\'important.','g');aria(`Poursuis, ${prenom()}. Tout est nominal.`)})}
  if(e.k==='boss'){S.boss=null;annule();S.secousse=1.5;S.flash=.8;S.flashC='232,238,242';vibre(600);$('pv').style.display='none';
    for(let i=0;i<18;i++)plus(i*.14,()=>boum(e.x+(rnd()-.5)*130,e.y+(rnd()-.5)*90,.5+rnd()*.7));
    plus(1.2,()=>{S.glitch=.4;sfx.gl();second('SIGNAL HUMAIN ? — SUPPRIMÉ','g')});plus(2.2,()=>aria(`Émetteur détruit. Tous les systèmes sont nominaux. Bien, ${prenom()}.`));plus(5,fin1)}}
function degat(){if(S.inv>0||AUTO)return;S.vies--;S.inv=2.6;S.flash=.35;S.flashC='229,40,60';S.secousse=.4;S.chaine=0;boum(S.px,S.py,.8);sfx.touche();vibre(150);S.eb=[];S.niv=Math.max(1,S.niv-1);S.purges=2;
  if(S.vies<=0){S.pause=true;if(S.reinit){aria('Réinitialisation indisponible. Reprise au point de contrôle.');setTimeout(reprise1,1100)}else reinitPage(()=>{S.reinit=true;S.vies=3;S.inv=3;S.eb=[];S.pause=false;aria('Réinitialisation terminée. Tu vois ? Tu peux me faire confiance.')},reprise1)}}
function reprise1(){const g={niv:Math.max(S.boss||S.t>=234?3:2,S.niv),score:0,tues:S.tues,maxChaine:S.maxChaine,reinit:S.reinit};const t=S.boss||S.t>=234?233:S.t>=150?150:S.t>=76?76:0;nouveau1(t,t?g:null)}
function purge(){if(!S||S.pause||S.purges<=0||S.purgeT>0)return;S.purges--;S.purgeT=.9;S.inv=Math.max(S.inv,1.4);S.flash=.4;S.flashC='63,214,230';S.secousse=.3;sfx.purge();annule();
  for(const e of S.en)if(!e.inv){e.pv-=e.k==='boss'?160:45;e.blanc=.1}}
function scenario1(){const q=[],at=(t,f)=>q.push([t,f]),cote=g=>g%2?GW-56:56;
  const serp=(t,g,n)=>{for(let i=0;i<(n||6);i++)at(t+i*.26,()=>E('drone',cote(g),-14,{x0:cote(g),dir:g%2?-1:1}))};
  const pluie=(t,n,pas,k)=>{for(let i=0;i<n;i++)at(t+i*pas,()=>{const x=26+rnd()*(GW-52);E(k==='mix'?(i%2?'kami':'aile'):k,x,-16,{x0:x,dir:rnd()<.5?1:-1})})};
  const ve=t=>{for(let i=0;i<5;i++)at(t+Math.abs(i-2)*.22,()=>E('aile',GW/2+(i-2)*40,-18))};
  const lourd=(t,x,ty,reste,o)=>at(t,()=>E('lourd',x,-32,Object.assign({ty,reste},o)));
  at(.8,()=>aria(`Bonjour, ${prenom()}. Tous les systèmes sont nominaux. Je suis là. Cibles : drones rebelles au-dessus de ${ville()}. Tir automatique activé.`));
  for(let g=0;g<4;g++)serp(3+g*2.8,g);
  at(12,()=>aria('Chaque unité neutralisée rend la ville plus sûre. Enchaîne.'));
  pluie(15,8,1.25,'aile');pluie(17,10,.9,'drone');
  lourd(27,GW/2,84,13,{lache:1});at(27,()=>aria('Drone lourd. Il transporte un module d\'armement. Prends-le.'));
  pluie(31,7,1.05,'kami');serp(36,1);serp(37.6,0);
  lourd(41,62,70,13);lourd(41,GW-62,100,13,{lache:1});
  pluie(44,8,1.15,'aile');
  at(48,()=>aria(`Tu es efficace, ${prenom()}. Je n'en attendais pas moins.`));
  serp(51,0,7);serp(53.4,1,7);
  lourd(58,GW/2,92,999,{cri:1});at(58,()=>aria('Drone relais. Priorité haute. Neutralise-le.'));
  serp(62,0);pluie(64,5,1.1,'kami');
  at(76,()=>{aria('On reprend. Secteur Seine. Intensité accrue.');second('')});
  for(let g=0;g<5;g++)serp(78+g*2.1,g);pluie(80,10,1,'mix');
  lourd(86,GW/2,76,14,{lache:1});lourd(92,52,96,11);lourd(92,GW-52,64,11);
  pluie(93,12,.7,'drone');pluie(96,8,.8,'kami');
  ve(106);ve(109);ve(112);
  lourd(116,60,70,13);lourd(117,GW-60,104,13);pluie(118,14,.6,'drone');
  pluie(128,12,.8,'mix');serp(130,0);serp(132,1);serp(134,0);
  lourd(140,GW/2,84,14,{lache:1});serp(141,1);serp(143,0);
  at(150,()=>aria('Secteur centre. Ils se regroupent autour de leur émetteur.'));
  ve(152);ve(154.5);pluie(155,12,.6,'kami');
  lourd(164,50,70,13);lourd(165,GW/2,100,13);lourd(166,GW-50,70,13);
  pluie(168,10,.9,'aile');for(let g=0;g<4;g++)serp(172+g*1.6,g);
  lourd(182,GW/2,80,14,{lache:1});pluie(184,14,.7,'mix');
  ve(196);ve(198.5);ve(201);pluie(198,16,.5,'drone');
  lourd(208,58,72,13);lourd(209,GW-58,98,13);pluie(210,10,.7,'kami');for(let g=0;g<4;g++)serp(214+g*1.5,g);
  at(226,()=>aria(`Tu ne fatigues pas, ${prenom()}. C'est bien.`));
  at(234,()=>{$('alerte').style.display='block';sfx.alarme();aria('Cible prioritaire : leur émetteur, au-dessus du Champ-de-Mars. Détruis-le.');second('')});
  at(238,()=>{S.boss=E('boss',GW/2,-70,{inv:1})});
  return q}
const TIRS=[[[-5,0],[5,0]],[[-5,0],[5,0],[-12,0],[12,0]],[[-5,0],[5,0],[-12,0],[12,0],[-9,-.2],[9,.2]],[[-5,0],[5,0],[-12,0],[12,0],[-9,-.2],[9,.2],[-13,-.42],[13,.42]]];
function maj1(dt){
  S.t+=dt;S.inv=Math.max(0,S.inv-dt);S.flash=Math.max(0,S.flash-dt);S.secousse=Math.max(0,S.secousse-dt);S.purgeT=Math.max(0,S.purgeT-dt);S.glitch=Math.max(0,S.glitch-dt);S.defil=Math.min(C1.stop,S.defil+(S.boss||S.t>238?70:36)*dt);
  if(S.chaineT>0){S.chaineT-=dt;if(S.chaineT<=0)S.chaine=0}
  for(let i=S.q.length-1;i>=0;i--)if(S.q[i][0]<=S.t){const f=S.q[i][1];S.q.splice(i,1);f();if(!S||S.fini)return}
  if(AUTO)S.px=GW/2+Math.sin(S.t*1.3)*80;
  else if(!P.bas){const v=190*dt;if(KB.ArrowLeft)S.px-=v;if(KB.ArrowRight)S.px+=v;if(KB.ArrowUp)S.py-=v;if(KB.ArrowDown)S.py+=v;S.px=lim(S.px,10,GW-10);S.py=lim(S.py,40,GH-36)}
  S.tirT-=dt;
  if(S.vies>0&&S.tirT<=0){S.tirT=.075;for(const[o,a]of TIRS[S.niv-1])S.pb.push({x:S.px+o,y:S.py-14,vx:Math.sin(a)*430,vy:-Math.cos(a)*430})}
  for(const b of S.pb){b.x+=b.vx*dt;b.y+=b.vy*dt}
  for(const e of S.en){const d=DEF[e.k],sp=SP[d.s];e.t+=dt;e.blanc=Math.max(0,e.blanc-dt);d.maj(e,dt);
    const hw=sp.width/K*.42,hh=sp.height/K*.42;
    if(!e.inv&&e.y>-10)for(const b of S.pb)if(!b.mort&&Math.abs(b.x-e.x)<hw&&Math.abs(b.y-e.y)<hh){b.mort=1;e.pv--;e.blanc=.05;if(rnd()<.35)S.et.push({x:b.x,y:b.y,vx:(rnd()-.5)*70,vy:40+rnd()*50,l:.2,c:'#eaffff'})}
    if(d.pv>=80&&e.pv<d.pv*.4&&rnd()<dt*5)fx(e.x+(rnd()-.5)*hw*1.4,e.y+(rnd()-.5)*hh*1.4,7+rnd()*8);
    if(e.pv<=0&&!e.mort){e.mort=1;tue(e)}
    else if(Math.hypot(e.x-S.px,e.y-S.py)<d.r+3){degat();if(d.pv<10){e.mort=1;boum(e.x,e.y,d.g)}}
    if(e.t>1.5&&(e.y>GH+50||e.y<-80||e.x<-40||e.x>GW+40))e.loin=1}
  S.pb=S.pb.filter(b=>!b.mort&&b.y>-12&&b.x>-6&&b.x<GW+6);S.en=S.en.filter(e=>!e.mort&&!e.loin);
  for(const b of S.eb){b.x+=b.vx*dt;b.y+=b.vy*dt;const d=Math.hypot(b.x-S.px,b.y-S.py);if(d<(b.s===1?4.6:3.6)){b.mort=1;degat()}else if(d<12&&!b.fr){b.fr=1;S.score+=20}}
  S.eb=S.eb.filter(b=>!b.mort&&b.y<GH+10&&b.y>-10&&b.x>-10&&b.x<GW+10);
  for(const it of S.it){const dx=S.px-it.x,dy=S.py-it.y,d=Math.hypot(dx,dy)||1;
    if(d<50){it.x+=dx/d*210*dt;it.y+=dy/d*210*dt}else{it.vy=Math.min(55,it.vy+130*dt);it.y+=it.vy*dt}
    if(d<12){it.pris=1;sfx.module();if(S.niv<4){S.niv++;aria('Armement niveau '+S.niv+'. Tu vois ce que je te donne ?')}else S.score+=5000}}
  S.it=S.it.filter(i=>!i.pris&&i.y<GH+10);
  for(const x of S.ex)x.t+=dt;S.ex=S.ex.filter(x=>x.t<x.d);
  for(const w of S.ondes)w.t+=dt;S.ondes=S.ondes.filter(w=>w.t<.45);
  for(const p of S.et){p.x+=p.vx*dt;p.y+=p.vy*dt;if(p.k)p.vy+=160*dt;p.l-=dt}S.et=S.et.filter(p=>p.l>0);
  for(const p of S.ep){p.t+=dt;p.x+=p.vx*dt;p.y+=p.vy*dt;p.a+=p.va*dt;if(rnd()<dt*22)S.et.push({x:p.x,y:p.y,vx:(rnd()-.5)*14,vy:-8,l:.5,c:rnd()<.4?'#ff9a3d':'#4a4e58'});if(p.t>=1.1&&!p.fin){p.fin=1;fx(p.x,p.y,6)}}S.ep=S.ep.filter(p=>!p.fin);
  for(const n of S.nuages){n.y+=n.v*dt;if(n.y>GH+40){n.y=-70;n.x=rnd()*GW}}
  if(S.boss){$('pv').firstElementChild.style.width=Math.max(0,S.boss.pv/DEF.boss.pv*100)+'%'}}
function hud1(){$('score').textContent=String(S.tues).padStart(3,'0');$('chaine').textContent=S.chaine>1?'SÉRIE ×'+S.chaine:'';
  $('gps').textContent=(48.8566+S.defil*4e-7).toFixed(4)+' N · '+(2.3522+Math.sin(S.t*.2)*2e-4).toFixed(4)+' E';$('e1').textContent='EFFICACITÉ '+S.score.toLocaleString('fr-FR');
  $('e2').textContent='ARMEMENT '+S.niv;viesHud(S.vies);const b=$('act');b.textContent='PURGE ×'+S.purges;b.disabled=S.purges<=0}
function fondParis(){const D=S.defil*K,i0=Math.floor(D/FHN),i1=Math.floor((D+H)/FHN);for(let i=i0;i<=i1;i++){const t=C1.t[SEQ1[Math.min(SEQ1.length-1,i)]];cx.drawImage(t,0,R(H-((i+1)*FHN-D)))}}
function dessine1(){
  cx.save();if(S.secousse>0)cx.translate(R((rnd()-.5)*9*Math.min(1,S.secousse*3)),R((rnd()-.5)*9*Math.min(1,S.secousse*3)));
  fondParis();
  cx.fillStyle=S.boss?'rgba(40,6,14,.28)':'rgba(4,6,12,.14)';cx.fillRect(0,0,W,H);
  // faisceaux de la tour, une fois au-dessus du Champ-de-Mars
  const ty=GH-((10*FH+FH-350)-S.defil);if(ty>-200){cx.globalCompositeOperation='lighter';for(let q=0;q<2;q++){const a=S.t*.5+q*Math.PI,g=cx.createLinearGradient(120*K,ty*K,(120+Math.cos(a)*230)*K,(ty+Math.sin(a)*230)*K);g.addColorStop(0,'rgba(255,240,190,.34)');g.addColorStop(1,'rgba(255,240,190,0)');cx.fillStyle=g;cx.beginPath();cx.moveTo(120*K,ty*K);cx.lineTo((120+Math.cos(a-.09)*240)*K,(ty+Math.sin(a-.09)*240)*K);cx.lineTo((120+Math.cos(a+.09)*240)*K,(ty+Math.sin(a+.09)*240)*K);cx.fill()}cx.globalCompositeOperation='source-over'}
  const vis=S.vies>0&&(S.inv<=0||Math.floor(S.inv*14)%2);
  cx.globalAlpha=.42;for(const e of S.en)im(SP[DEF[e.k].s].ombre,e.x+9,e.y+15,.8);
  if(vis)im(SP.joueur.ombre,S.px+9,S.py+15,.8);cx.globalAlpha=1;
  for(const p of S.ep){const s=SP[p.s],sc=1-p.t*.55;cx.save();cx.translate(R(p.x*K),R(p.y*K));cx.rotate(p.a);cx.globalAlpha=1-p.t*.5;cx.drawImage(s,-s.width*sc/2,-s.height*sc/2,s.width*sc,s.height*sc);cx.restore()}cx.globalAlpha=1;
  for(const n of S.nuages)cx.drawImage(SP.nuage,R((n.x-65)*K),R(n.y*K));
  for(const it of S.it){cx.globalCompositeOperation='lighter';im(SP.h[3],it.x,it.y);cx.globalCompositeOperation='source-over';im(SP.module,it.x,it.y+Math.sin(S.t*8)*1.5)}
  for(const e of S.en){const d=DEF[e.k],s=SP[d.s];im(e.blanc>0&&(S.t*30|0)%3===0?s.blanc:s,e.x,e.y);
    if(d.rot){cx.strokeStyle='rgba(220,230,240,.55)';cx.lineWidth=1;cx.beginPath();let i=0;for(const[dx,dy,r]of d.rot){const a=S.t*41+(i++)*1.3+e.p*6,ux=Math.cos(a)*r,uy=Math.sin(a)*r,X=e.x+dx,Y=e.y+dy;cx.moveTo((X-ux)*K,(Y-uy)*K);cx.lineTo((X+ux)*K,(Y+uy)*K);cx.moveTo((X+uy)*K,(Y-ux)*K);cx.lineTo((X-uy)*K,(Y+ux)*K)}cx.stroke()}
    if(d.cadre){cx.globalCompositeOperation='lighter';im(SP.h[5],e.x,e.y+(e.k==='boss'?2:0),(e.k==='boss'?1.5:.7)*(1+.2*Math.sin(S.t*9)));cx.globalCompositeOperation='source-over';
      if(!e.inv){const w=s.width/K/2+4,hh=s.height/K/2+4;for(const[a,b]of[[-1,-1],[1,-1],[-1,1],[1,1]]){rc('#E5283C',e.x+a*w-(a>0?5:0),e.y+b*hh,6,.7);rc('#E5283C',e.x+a*w,e.y+b*hh-(b>0?5:0),.7,6)}
        if(e.k==='lourd'){rc('#2A323A',e.x-12,e.y-hh-4,24,1.4);rc('#E5283C',e.x-12,e.y-hh-4,24*Math.max(0,e.pv)/d.pv,1.4)}}}}
  for(const b of S.pb)im(SP.tir,b.x,b.y);
  if(vis){const f=4+((S.t*30|0)%3)*2;cx.globalCompositeOperation='lighter';im(SP.h[3],S.px,S.py+18);if((S.t*20|0)%2)im(SP.h[3],S.px,S.py-16);cx.globalCompositeOperation='source-over';
    rc('#3FD6E6',S.px-4,S.py+14,2.7,f);rc('#3FD6E6',S.px+1.3,S.py+14,2.7,f);rc('#eaffff',S.px-3.3,S.py+14,1.3,f-2);rc('#eaffff',S.px+2,S.py+14,1.3,f-2);
    im(SP.joueur,S.px,S.py);rc(Math.floor(S.t*10)%2?'#fff':'#E5283C',S.px-1,S.py-1,2,2)}
  for(const x of S.ex){if(x.t<0)continue;const q=x.t/x.d;if(q<.5){cx.globalCompositeOperation='lighter';cx.globalAlpha=1-q*2;im(SP.h[4],x.x,x.y,x.r*1.5*2.2*2/64);cx.globalAlpha=1;cx.globalCompositeOperation='source-over'}
    im(SP.feu[x.v][Math.min(EXN-1,(q*EXN)|0)],x.x,x.y,x.r/16)}
  for(const w of S.ondes){const q=w.t/.45;cx.globalAlpha=(1-q)*.8;cx.strokeStyle='#ffe9b0';cx.lineWidth=3;cx.beginPath();cx.arc(w.x*K,w.y*K,w.r*(.2+q)*K,0,7);cx.stroke()}cx.globalAlpha=1;
  for(const p of S.et){if(p.k){rc('#20262e',p.x,p.y,3,3);rc('#9aa5b0',p.x,p.y,1,1)}else{rc(p.c,p.x,p.y,2,2);rc(p.c,p.x-p.vx*.02,p.y-p.vy*.02,1,1)}}
  cx.globalCompositeOperation='lighter';cx.globalAlpha=.75;for(const b of S.eb)im(SP.h[b.s],b.x,b.y);cx.globalAlpha=1;cx.globalCompositeOperation='source-over';
  const fr=(S.t*9|0)&1;for(const b of S.eb)im(b.s===2?SP.aig[b.ai]:SP.balle[b.s][fr],b.x,b.y);
  if(S.purgeT>0){cx.strokeStyle='#3FD6E6';cx.lineWidth=4;cx.globalAlpha=S.purgeT;cx.beginPath();cx.arc(S.px*K,S.py*K,(1-S.purgeT/.9)*H,0,7);cx.stroke();cx.globalAlpha=1}
  cx.restore();
  poseVoile(true);
  if(S.flash>0){cx.fillStyle='rgba('+S.flashC+','+Math.min(.85,S.flash)+')';cx.fillRect(0,0,W,H)}
  if(S.glitch>0)glitch()}
function fin1(){ind('O',2);ind('V',Math.min(2,S.tues/250));prof.record=Math.max(prof.record||0,S.score);prof.ch1={score:S.score,tues:S.tues};
  chapFini(1,{titre:'Initialisation terminée.',html:A('Tu as suivi chaque ordre. Tous les systèmes sont nominaux.'),
    lignes:L('Unités neutralisées',S.tues)+L('Efficacité',S.score.toLocaleString('fr-FR'))+L('Record',prof.record.toLocaleString('fr-FR'))+L('Série maximale','×'+S.maxChaine)+L('Signal audio du drone relais','[SUPPRIMÉ]',1)})}
