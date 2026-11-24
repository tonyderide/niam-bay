// ================================================================ MOTEUR BEAT'EM ALL : rue parisienne de nuit (décor en relief de 760 px de haut), combat au corps à corps
const RH=760,RF=520,RY0=600,RY1=712; // hauteur du décor, bas des façades, profondeur jouable
function peintRue(T,Wp,r,o){o=o||{};const ch=a=>a[(r()*a.length)|0];
  const fen=(x,y,w,h,allume)=>{T.box(x-3,y-3,w+6,h+6,3,1.6,1.6,'#c8bca8');T.plat(x,y,w,h,.5,allume?(r()<.5?'#ffd98a':'#ffe8b8'):'#141c2c',allume?.85:0);
    if(allume){if(r()<.6){T.teinte(x,y,w*.3,h,'#c8a868',.6);T.teinte(x+w*.7,y,w*.3,h,'#c8a868',.6)}if(r()<.3)T.teinte(x+w*.4,y+h*.45,w*.25,h*.55,'#2a2420',.2)}else T.ton(x,y,w,h,(a,b)=>1+((a+b)%9<3?.5:0));
    T.box(x+w/2-.8,y,1.6,h,3,.8,.6,'#d8d0c0');T.box(x,y+h*.42,w,1.4,3,.8,.6,'#d8d0c0')};
  const garde=(x,y,w)=>{T.box(x,y,w,2,6,1,.8,'#14181e');T.box(x,y+13,w,2,6,1,.8,'#14181e');for(let q=1;q<w;q+=3)T.box(x+q,y+2,1,11,5.4,.6,.4,'#1a2028')};
  let x=0,ib=o.dec||0;
  while(x<Wp){const w=264+((r()*4)|0)*24,C=ch(['#a89c88','#9c968a','#b0a28e','#928c86']),C2='#c0b4a0';
    T.box(x,0,w,RF,2,0,.01,C);T.ton(x,100,w,RF-100,(a,b,i,j)=>(.84+.16*Math.sin(a*.021+Math.sin(b*.013)*2))*(i%7===0?.94:1)*(b>400?(j%12<2?.8:1):1));
    // toit en zinc, lucarnes, souches
    T.box(x,0,w,96,2,5,40,'#4c586c');T.rel(x,0,w,96,(a,b,i,j)=>i%8===0?-.6:0);T.box(x,92,w,8,5,2.4,2,C2);
    for(let q=x+26;q<x+w-30;q+=52){T.box(q,44,24,48,5,4,3,'#566278');fen(q+5,54,14,28,r()<.35)}
    for(let q=0;q<3;q++){const cx0=x+20+r()*(w-50);T.box(cx0,2,16,26,6,3,2,'#8a5a46');for(let p=0;p<3;p++)cyl(T,cx0+1+p*5,-4,4,8,6,2,'#a86a50')}
    // étages
    const nf=Math.floor((w-24)/52),e=(w-nf*52)/2;
    for(let f=0;f<3;f++){const fy=112+f*96;for(let q=0;q<nf;q++){const fx=x+e+q*52+13;fen(fx,fy,26,62,r()<(f===2?.4:.3));
        if(f!==1||true){if(r()<.5||f===0||f===2)garde(fx-6,fy+48,38)}if(r()<.22){T.box(fx-9,fy-2,7,66,3.4,1.2,1,'#5a6a5a');T.box(fx+28,fy-2,7,66,3.4,1.2,1,'#5a6a5a')}}
      T.box(x,fy+78,w,5,4,2.4,1.6,C2);if(f!==1){T.box(x+4,fy+62,w-8,3,7,1.6,1.2,'#8a8478');garde(x+6,fy+48,w-12)}}
    T.trait(x,96,x,RF,1.6);cyl(T,x+3,96,5,RF-96,3,2.4,'#5a626c');
    // rez-de-chaussée
    const gy=404,k=ib%6;T.box(x,gy-6,w,8,5,2.6,2,C2);if(o.ens)o.ens.push([x,w,k]);
    const vitrine=(vx,vw,cb,aw,items)=>{T.box(vx-6,gy+4,vw+12,RF-gy-4,3,2,2,cb);T.plat(vx,gy+30,vw,RF-gy-52,.4,'#ffe6b0',.8);T.box(vx-6,gy+4,vw+12,20,5,1.4,1.4,cb);
      for(let q=0;q<items;q++){const ix=vx+6+q*(vw-12)/items,ih=10+r()*26;T.teinte(ix,RF-22-ih,(vw-12)/items-4,ih,ch(['#c8843a','#8a3a2a','#3a5a7a','#d8c8a0','#5a7a4a','#7a3a5a']),.45)}
      T.box(vx+vw/2-1,gy+30,2,RF-gy-52,3,1,.8,cb);T.box(vx-6,RF-22,vw+12,22,4,1.4,1.4,cb);
      if(aw){T.poly([[vx-12,gy+22],[vx+vw+12,gy+22],[vx+vw+16,gy+46],[vx-16,gy+46]],6,5,3,aw);T.ton(vx-16,gy+22,vw+32,24,(a,b,i)=>((i/9)|0)%2?1:.72)}
      T.lueur(vx+vw/2,RF+18,vw*.8,'#ffe0a0',.5)};
    const porte=(px,c)=>{T.box(px-6,gy+10,60,RF-gy-10,3,2.4,2.4,C2);T.plat(px,gy+16,48,RF-gy-16,.6,c);T.rel(px,gy+16,48,RF-gy-16,(a,b,i,j)=>(Math.abs(a-px-24)<1)?-1:((a-px)%24<3||(a-px)%24>21||(b-gy-16)%44<3)?-.7:0);T.ell(px+21,gy+70,1.6,1.6,2,1.4,'#c8a84a');T.ell(px+27,gy+70,1.6,1.6,2,1.4,'#c8a84a');T.box(px+8,gy+2,32,10,4,1,1,'#2a4a8a');T.pix(px+52,gy+60,'#40ff70')};
    const rideau=(vx,vw)=>{T.box(vx-6,gy+4,vw+12,RF-gy-4,3,2,2,'#56606c');T.box(vx,gy+22,vw,RF-gy-24,2,1,1,'#7a828c');T.rel(vx,gy+22,vw,RF-gy-24,(a,b,i,j)=>j%6<2?-1:0)};
    if(k===0){vitrine(x+24,w-120,'#7a2a2a','#a83a3a',6);porte(x+w-78,'#2a3a5a')}
    else if(k===1){porte(x+22,'#3a5a48');rideau(x+100,w-126)}
    else if(k===2){vitrine(x+20,w-40,'#2a4a3a','#3a6a52',7);for(let q=0;q<4;q++){const tx=x+30+q*((w-60)/4);T.box(tx,RF-4,18,3,6,1,1,'#3a3e46');T.box(tx+8,RF-4,2,22,5,1,1,'#3a3e46');T.box(tx-10,RF+4,8,2,6,1,1,'#6a5a48');T.box(tx-10,RF+4,2,14,5,1,1,'#3a3e46');T.box(tx+20,RF+4,8,2,6,1,1,'#6a5a48');T.box(tx+26,RF+4,2,14,5,1,1,'#3a3e46')}}
    else if(k===3){vitrine(x+20,w-116,'#d8dce0',null,5);porte(x+w-80,'#5a3a2a');T.box(x+w-104,gy-40,22,22,7,2,2,'#1a3a2a');T.teinte(x+w-96,gy-38,6,18,'#40ff80',1);T.teinte(x+w-102,gy-32,18,6,'#40ff80',1);T.lueur(x+w-93,gy-29,40,'#40ff80',.5)}
    else if(k===4){rideau(x+18,w/2-30);vitrine(x+w/2+8,w/2-30,'#2a3a6a','#3a4a8a',5);T.poly([[x+w/2-6,gy-30],[x+w/2+2,gy-34],[x+w/2+10,gy-30],[x+w/2+2,gy+2]],7,3,3,'#c02828',0,.5);T.lueur(x+w/2+2,gy-14,26,'#ff5040',.4)}
    else{porte(x+w/2-24,'#4a2a2a');for(const sx of[x+18,x+w-70]){fen(sx+4,gy+30,40,56,r()<.5);garde(sx,gy+72,48)}}
    x+=w;ib++}
  // trottoir, bordure, caniveau, chaussée mouillée
  T.box(0,RF,Wp,62,3,0,.01,'#6c6e76');T.rel(0,RF,Wp,62,(a,b,i,j)=>(i%34===0||j===RF+30)?-.8:0);T.ton(0,RF,Wp,62,(a,b,i,j)=>.86+((((i/34)|0)*7+((j>RF+30)?3:0))%5)*.035+Math.sin(a*.05)*.04);
  T.box(0,RF+62,Wp,7,1,2,2,'#8a8c94');T.rel(0,RF+62,Wp,7,(a,b,i)=>i%40===0?-1:0);
  T.plat(0,RF+69,Wp,RH-RF-69,0,'#2a2e3a');T.ton(0,RF+69,Wp,RH-RF-69,(a,b,i,j)=>(.8+.2*Math.sin(a*.017+Math.sin(b*.05)*1.6)*Math.sin(b*.041))*((((i*13)^(j*7))%11===0)?1.3:1));
  T.plat(0,RF+69,Wp,5,-.6,'#1c2028');
  for(let q=20;q<Wp;q+=96)T.teinte(q,RF+128,44,3,'#8d94a0');
  for(let q=180;q<Wp;q+=430){T.ell(q,RF+100+((q*7)%60),13,6,.2,.4,'#3e424c');T.trait(q-9,RF+100+((q*7)%60),q+9,RF+100+((q*7)%60),.6)}
  for(const zx of o.pietons||[])for(let q=0;q<7;q++)T.teinte(zx,RF+76+q*24,60,13,'#a8aeb8');
  for(let q=0;q<Wp/200;q++){const px=r()*Wp,py=RF+80+r()*150;T.ell(px,py,18+r()*30,5+r()*6,-.3,.1,'#3a4460')}
  // mobilier urbain
  for(let q=110;q<Wp;q+=310){// réverbère parisien
    cyl(T,q-2,RF-150,4,186,5,2.4,'#20262e');T.box(q-5,RF+26,10,10,5,3,2,'#20262e');T.box(q-7,RF-170,14,22,6,3,3,'#ffe2a0',0,.9);T.poly([[q-9,RF-170],[q,RF-182],[q+9,RF-170]],6,2,2,'#20262e');T.box(q-9,RF-150,18,3,6,1,1,'#20262e');T.lueur(q,RF-150,110,'#ffcf80',.5);T.lueur(q,RF+40,80,'#ffcf80',.4)}
  for(let q=262;q<Wp;q+=620){// platane et grille
    cyl(T,q-5,RF-120,10,160,5,3,'#5a5248');T.ton(q-5,RF-120,10,160,(a,b,i,j)=>((i*3+j*5)%11<3)?1.25:.95);T.ell(q,RF+42,18,5,3.2,.4,'#3a3e46');for(let p=0;p<16;p++){const a=r()*TAU,d=r()*42;T.ell(q+Math.cos(a)*d*1.3,RF-170+Math.sin(a)*d,18+r()*14,15+r()*10,6,5,ch(['#2c4a30','#34583a','#263f2a','#3c6240']))}}
  for(const[bx,k]of o.mobilier||[]){
    if(k==='auto'){const c=ch(['#7a2a2a','#2a3a5a','#8a8f98','#d8dce0','#2a2e34']);T.poly([[bx,RF+46],[bx+4,RF+30],[bx+28,RF+26],[bx+40,RF+10],[bx+86,RF+10],[bx+104,RF+28],[bx+126,RF+32],[bx+130,RF+46],[bx+128,RF+54],[bx+2,RF+54]],8,5,5,c,1);T.poly([[bx+33,RF+27],[bx+43,RF+14],[bx+62,RF+14],[bx+62,RF+27]],9,.5,1,'#141c2c');T.poly([[bx+66,RF+14],[bx+84,RF+14],[bx+98,RF+27],[bx+66,RF+27]],9,.5,1,'#141c2c');
      for(const wx of[bx+26,bx+102]){T.ell(wx,RF+54,11,11,9,2,'#14161a');T.ell(wx,RF+54,5.5,5.5,10,2,'#8a9098')}T.pix(bx+129,RF+38,'#ff3030');T.pix(bx+1,RF+38,'#fff6c0');T.trait(bx+64,RF+14,bx+64,RF+50,.8)}
    else if(k==='morris'){cyl(T,bx,RF-70,30,110,6,7,'#2a4a3a');T.ell(bx+15,RF-74,19,8,7,4,'#2a4a3a');T.ell(bx+15,RF-84,9,9,8,6,'#2a4a3a');T.box(bx+13,RF-98,4,10,8,2,2,'#2a4a3a');for(let p=0;p<2;p++){T.plat(bx+4,RF-58+p*44,22,38,9,ch(['#c8a040','#a03030','#d8d0c0','#3a5a8a']));T.teinte(bx+7,RF-52+p*44,16,5,'#f0ece0');T.teinte(bx+7,RF-34+p*44,12,2,'#20242a')}}
    else if(k==='metro'){for(const px of[bx,bx+96])cyl(T,px,RF-110,5,150,6,2.4,'#2a4a3a');T.box(bx-4,RF-112,110,26,7,2,2,'#2a4a3a');T.plat(bx+2,RF-108,98,18,8,'#e8dc9a',.7);T.box(bx,RF+8,100,3,6,1,1,'#2a4a3a');for(let p=4;p<100;p+=6)T.box(bx+p,RF+10,1.6,30,5,.8,.6,'#2a4a3a');T.box(bx,RF+38,100,4,6,1,1,'#2a4a3a');T.plat(bx+6,RF+12,88,24,-2,'#0c0e12');T.ell(bx+50,RF-124,10,10,8,2,'#e8c040',.9);T.lueur(bx+50,RF-110,50,'#ffe8a0',.5)}
    else if(k==='poubelle'){cyl(T,bx,RF+8,14,26,5,4,'#3a5a48');T.box(bx-1,RF+6,16,4,6,2,1.5,'#2a4a3a')}
    else if(k==='banc'){T.box(bx,RF+22,54,4,6,1.6,1.2,'#3a5a48');T.box(bx,RF+8,54,3,6,1.4,1,'#3a5a48');T.box(bx,RF+14,54,3,6,1.4,1,'#3a5a48');for(const px of[bx+4,bx+46])T.box(px,RF+8,4,30,5,1.4,1,'#20262e')}
    else if(k==='barricade'){PROPS.palette(T,bx,RF+50,r);PROPS.pneus(T,bx+50,RF+50,r);PROPS.baril(T,bx+82,RF+50,r);T.box(bx+10,RF+2,5,48,6,2,1.5,'#6a5a48');T.box(bx+92,RF-8,5,40,6,2,1.5,'#6a5a48');T.box(bx+8,RF-34,94,36,7,.6,.6,'#d8d4c4');T.rel(bx+8,RF-34,94,36,(a,b)=>Math.sin(a*.2)*.5)}
    else if(k==='velos'){for(let p=0;p<3;p++){const vx=bx+p*26;T.ell(vx,RF+40,11,11,5,1,'#14161a');T.trou(vx,RF+40,8.6,8.6,3.2,'#62646c');T.ell(vx+26,RF+40,11,11,5,1,'#14161a');T.trou(vx+26,RF+40,8.6,8.6,3.2,'#62646c');T.cap(vx,RF+40,vx+10,RF+22,1.2,1.2,6,1.4,'#8ab0a8');T.cap(vx+10,RF+22,vx+26,RF+40,1.2,1.2,6,1.4,'#8ab0a8');T.cap(vx+10,RF+22,vx+20,RF+22,1.2,1.2,6,1.4,'#8ab0a8');T.box(vx+6,RF+17,8,3,7,1,1,'#20242a')}}}
  if(o.plus)o.plus(T,r)}
// ---------------------------------------------------------------- combat
const SPR={};
function spritesRue(){if(SPR.ok)return;SPR.ok=1;spritesCote();const L=['repos','marche','garde','poing1','touche','sol','mains','elan','course'];
  for(const k of['civil1','civil2','civil3','civil4','civil5','meneur'])SPR[k]=fabPerso(TENUES[k],L);
  SPR.b1=fabPerso(TENUES.civil2,L,{arme:1});SPR.b2=fabPerso(TENUES.civil4,L,{arme:1});SPR.garde=fabPerso(TENUES.garde,L)}
const ETYPES={civil1:{pv:3,v:62,deg:1},civil2:{pv:3,v:70,deg:1},civil3:{pv:4,v:56,deg:1},civil4:{pv:3,v:78,deg:1},civil5:{pv:3,v:52,deg:1},b1:{pv:4,v:60,deg:1,port:44},b2:{pv:4,v:66,deg:1,port:44},meneur:{pv:16,v:70,deg:1,port:36},garde:{pv:6,v:74,deg:1}};
function rueDebut(N,o){spritesRue();S={t:0,N,j:{x:N.depart||70,y:660,dir:1,an:'garde',af:0,pv:6,inv:0,att:0,combo:0,comboT:0,dash:0,dvx:0,dvy:0,stun:0},cam:{x:0},en:[],corps:[],pouss:[],q:[],vague:-1,verrou:null,glitch:0,flash:0,flashC:'229,40,60',secousse:0,gel:0,pause:false,fini:false,dialogue:false,reinit:false,tues:0,amb:N.amb||'rue',mv:{x:0,y:0},go:0};
  if(o&&o.t){S.vague=(+o.t)-1;S.j.x=N.vagues[+o.t]?N.vagues[+o.t].x+60:S.j.x;S.cam.x=Math.max(0,S.j.x-W/2)}}
function rueEnnemi(k,x,y,o){const d=ETYPES[k];const e=Object.assign({k,x,y,dir:-1,pv:d.pv,et:'approche',t:0,af:rnd()*4,stun:0,cool:.6+rnd()*1.5,dy:(rnd()-.5)*60,vx:0},o);S.en.push(e);return e}
function rueFrappeJoueur(port,deg,recul){const j=S.j;let touche=false;for(const e of S.en){if(e.et==='sol'||e.et==='ko'||e.et==='rendu'||e.intouchable)continue;const dx=(e.x-j.x)*j.dir;if(dx>-8&&dx<port&&Math.abs(e.y-j.y)<16){touche=true;e.pv-=deg;e.stun=.32;e.et='touche';e.t=0;e.vx=j.dir*recul;e.dir=-j.dir;S.gel=.05;
      for(let i=0;i<6;i++)S.pouss.push({x:e.x-j.dir*6,y:e.y-34,vx:(rnd()-.3)*j.dir*160,vy:-rnd()*120,l:.3,c:i%2?'#fff':'#ffd27a'});
      if(e.pv<=0){if(S.N.avantKo&&S.N.avantKo(e)){e.pv=1;continue}e.et='sol';e.t=0;e.vx=j.dir*recul*1.7;e.ko=true;S.tues++;if(S.N.surKo)S.N.surKo(e)}}}
  sfx.coup(touche?1:0);if(!touche)sfx.vent();return touche}
function rueDegat(d,dir){const j=S.j;if(j.inv>0||AUTO)return;j.pv-=d;j.inv=.9;j.stun=.3;j.dvx=dir*150;S.flash=.25;S.secousse=.25;sfx.touche();vibre(100);
  if(j.pv<=0){S.pause=true;if(S.reinit){j.pv=6;setTimeout(()=>{S.pause=false},600);aria('Réinitialisation indisponible. Tiens bon.')}else reinitPage(()=>{S.reinit=true;j.pv=6;j.inv=2;S.pause=false;aria('Réinitialisation terminée. Je suis là.')},()=>{j.pv=6;j.inv=2;S.pause=false;for(const e of S.en)e.x+=e.x>j.x?120:-120})}}
function rueMaj(dt){const N=S.N,j=S.j;if(S.gel>0){S.gel-=dt;return}S.t+=dt;S.flash=Math.max(0,S.flash-dt);S.glitch=Math.max(0,S.glitch-dt);S.secousse=Math.max(0,S.secousse-dt);
  for(let i=S.q.length-1;i>=0;i--)if(S.q[i][0]<=S.t){const f=S.q[i][1];S.q.splice(i,1);f();if(!S||S.fini)return}
  // vagues : verrouillage de l'écran
  const nv=N.vagues[S.vague+1];if(!S.verrou&&nv&&j.x>nv.x){S.vague++;S.verrou=nv;nv.f&&nv.f();for(const[k,cote,dy,o]of nv.en)rueEnnemi(k,S.cam.x+(cote>0?W+30+rnd()*60:-30-rnd()*60),lim(660+(dy||0),RY0,RY1),o)}
  if(S.verrou&&!S.en.some(e=>!e.ko&&e.et!=='rendu')&&!S.attente){const v=S.verrou;S.verrou=null;S.go=2.5;v.fin&&v.fin()}
  // joueur
  j.inv=Math.max(0,j.inv-dt);j.comboT=Math.max(0,j.comboT-dt);if(j.comboT<=0)j.combo=0;
  let mx=S.mv.x,my=S.mv.y;if(!P.bas){mx=(KB.ArrowRight?1:0)-(KB.ArrowLeft?1:0);my=(KB.ArrowDown?1:0)-(KB.ArrowUp?1:0)}if(AUTO){mx=S.en.length?0:1;if(S.t%0.4<dt)rueAttaque()}
  if(S.bloque){mx=my=0}
  if(j.stun>0){j.stun-=dt;j.x+=j.dvx*dt;j.dvx*=.9;j.an='touche'}
  else if(j.dash>0){j.dash-=dt;j.x+=j.dvx*dt;j.y+=j.dvy*dt;j.an='elan';if(!j.dashT&&j.dash<.12){j.dashT=1;rueFrappeJoueur(46,2,260)}}
  else if(j.att>0){j.att-=dt;if(!j.attT&&j.att<.16){j.attT=1;const fin=j.combo===3;if(rueFrappeJoueur(fin?44:38,fin?2:1,fin?240:70)&&fin)S.secousse=.15}}
  else{const m=Math.hypot(mx,my);if(m>.2){j.x+=mx/m*118*dt;j.y+=my/m*76*dt;if(mx)j.dir=mx>0?1:-1;j.an='marche';j.af+=dt*11}else{j.an='garde';j.af+=dt*3}}
  const g0=S.verrou?S.cam.x+12:Math.max(12,S.cam.x-40),g1=S.verrou?S.cam.x+W-12:N.Wp-12;j.x=lim(j.x,g0,g1);j.y=lim(j.y,RY0,RY1);
  if(!S.verrou){const tx=lim(j.x-W*.42,0,(nv?nv.x-W*.3:N.Wp-W));S.cam.x+=(Math.max(S.cam.x,Math.min(tx,N.Wp-W))-S.cam.x)*Math.min(1,dt*4)}
  S.go=Math.max(0,S.go-dt);
  // ennemis
  let actifs=0;for(const e of S.en)if(e.et==='prep'||e.et==='frappe')actifs++;
  for(const e of S.en){const d=ETYPES[e.k];e.t+=dt;e.af+=dt*9;
    if(e.et==='rendu'){continue}
    if(e.et==='sol'){e.x+=e.vx*dt;e.vx*=.88;if(e.t>.9){if(e.ko){e.et='ko';S.corps.push(e)}else{e.et='approche';e.t=0}}continue}
    if(e.et==='ko')continue;
    if(e.et==='touche'){e.x+=e.vx*dt;e.vx*=.85;e.stun-=dt;if(e.stun<=0){e.et='approche';e.cool=.5+rnd()}continue}
    const dx=j.x-e.x,dyy=j.y-e.y,port=d.port||32;e.dir=dx>0?1:-1;
    if(e.et==='prep'){if(e.t>.42){e.et='frappe';e.t=0;if(Math.abs(dx)<port+8&&Math.abs(dyy)<15)rueDegat(d.deg,e.dir);else sfx.vent()}continue}
    if(e.et==='frappe'){if(e.t>.3){e.et='approche';e.cool=1+rnd()*1.6}continue}
    e.cool-=dt;const cx0=j.x-e.dir*(port-4),cy0=j.y+(e.cool>0?e.dy*.5:0),ddx=cx0-e.x,ddy=cy0-e.y,m=Math.hypot(ddx,ddy);
    if(e.cool>0&&m<70){e.x-=e.dir*d.v*.35*dt;e.y+=Math.sign(e.dy||1)*d.v*.3*dt}else if(m>5){e.x+=ddx/m*d.v*dt;e.y+=ddy/m*d.v*.7*dt}
    e.y=lim(e.y,RY0,RY1);e.x=lim(e.x,S.cam.x-70,S.cam.x+W+70);
    if(e.cool<=0&&Math.abs(dx)<port+4&&Math.abs(dyy)<11&&actifs<2&&j.inv<=0){e.et='prep';e.t=0;actifs++}}
  S.en=S.en.filter(e=>e.et!=='ko');
  for(const p of S.pouss){p.x+=p.vx*dt;p.y+=p.vy*dt;p.vy+=300*dt;p.l-=dt}S.pouss=S.pouss.filter(p=>p.l>0);
  if(N.maj)N.maj(dt)}
function rueAttaque(){const j=S.j;if(S.bloque||j.stun>0||j.dash>0||j.att>.08)return;j.combo=j.combo%3+1;j.comboT=.7;j.att=.28;j.attT=0;j.an=['poing1','poing2','pied'][j.combo-1]}
function rueElan(dx,dy){const j=S.j;if(S.bloque||j.stun>0||j.dash>0)return;const m=Math.hypot(dx,dy)||1;j.dash=.26;j.dashT=0;j.dvx=dx/m*330;j.dvy=dy/m*150;if(Math.abs(dx)>4)j.dir=dx>0?1:-1;j.inv=Math.max(j.inv,.2);sfx.vent()}
function rueDessine(){const N=S.N,j=S.j,cmx=R(S.cam.x),oy=H-RH,t=S.t;
  cx.save();if(S.secousse>0)cx.translate(R((rnd()-.5)*8),R((rnd()-.5)*8));
  if(oy>0)cx.drawImage(N.fondLoin,-R(cmx*.1)%240,oy-H+140);
  poseBandes(N.decor,cmx,-oy);
  // reflets mouillés des façades sur la chaussée
  cx.save();cx.globalAlpha=.16;cx.translate(0,oy+RF+69+150);cx.scale(1,-1);const i0=Math.max(0,Math.floor(cmx/N.decor.larg)),i1=Math.min(N.decor.bandes.length-1,Math.floor((cmx+W)/N.decor.larg));for(let i=i0;i<=i1;i++)cx.drawImage(N.decor.bandes[i],0,RF-150,N.decor.bandes[i].width,150,i*N.decor.larg-cmx,0,N.decor.bandes[i].width,150);cx.restore();
  if(N.dessineAvant)N.dessineAvant(cmx,oy);
  // personnages triés par profondeur
  const L=[];for(const e of S.corps)L.push([e.y-1000,e]);for(const e of S.en)L.push([e.y,e]);L.push([j.y,j]);L.sort((a,b)=>a[0]-b[0]);
  for(const[,e]of L){const sx=e.x-cmx,sy=e.y+oy;if(sx<-60||sx>W+60)continue;cx.fillStyle='rgba(0,0,0,.35)';cx.beginPath();cx.ellipse(sx,sy,15,4,0,0,7);cx.fill();
    if(e===j){if(j.inv<=0||Math.floor(j.inv*16)%2||j.stun>0){const f=SPC.op[j.an];poseSprite(f[Math.floor(j.af)%f.length],sx,sy,j.dir)}}
    else{const A=SPR[e.k],an=e.et==='rendu'?'mains':e.et==='ko'||e.et==='sol'?'sol':e.et==='touche'?'touche':e.et==='prep'?'garde':e.et==='frappe'?'poing1':'marche',f=A[an];
      if(e.et==='ko')cx.globalAlpha=.8;poseSprite(f[Math.floor(e.af)%f.length],sx+(e.et==='prep'?Math.sin(t*50)*1.5:0),sy,e.dir,e.et==='touche'&&e.stun>.24);cx.globalAlpha=1;
      if(e.et==='prep'){cx.fillStyle='#E5283C';cx.fillRect(R(sx-1),R(sy-64),3,7);cx.fillRect(R(sx-1),R(sy-55),3,3)}}}
  for(const p of S.pouss){cx.fillStyle=p.c;cx.fillRect(R(p.x-cmx),R(p.y+oy),2,2)}
  lumDebut(N.ambCol||'#5a6690');for(let q=110;q<N.Wp;q+=310){const x=q-cmx;if(x>-200&&x<W+200){lumPoint(x,oy+RF-150,360,'#ffd9a0',1);lumPoint(x,oy+RF+60,300,'#ffd9a0',.8)}}
  for(const[lx,ly,ray,c]of N.lumieres||[]){const x=lx-cmx;if(x>-300&&x<W+300)lumPoint(x,oy+ly,ray,c,.9)}lumPoint(j.x-cmx,j.y+oy-26,110,'#cfeeff',.7);lumFin();
  pluie(t,N.pluie===undefined?80:N.pluie);
  if(N.dessineApres)N.dessineApres(cmx,oy);
  if(S.go>0&&Math.floor(t*4)%2){cx.fillStyle='#3FD6E6';cx.font='bold 26px monospace';cx.fillText('AVANCE ▶',W-150,oy+RY0-40)}
  cx.restore();poseVoile(false);
  if(S.flash>0){cx.fillStyle='rgba('+S.flashC+','+Math.min(.85,S.flash)+')';cx.fillRect(0,0,W,H)}
  if(S.glitch>0)glitch()}
// commandes : glisser = se déplacer, toucher bref = frapper, balayage rapide = charge
const rueChap=o=>Object.assign({maj:rueMaj,dessine:rueDessine,hud(){viesHud(Math.ceil(S.j.pv/2));$('score').textContent=String(S.tues).padStart(3,'0');if(S.N.hud)S.N.hud()},
  bas(x,y){S.mv.x=S.mv.y=0;S.tx=x;S.ty=y;S.tmax=0},
  bouge(x,y){const dx=x-S.tx,dy=y-S.ty,m=Math.hypot(dx,dy);S.tmax=Math.max(S.tmax,m);if(m>9){S.mv.x=dx/m;S.mv.y=dy/m;if(m>36){S.tx=x-dx/m*36;S.ty=y-dy/m*36}}else S.mv.x=S.mv.y=0},
  haut(x,y,dur){const dx=x-P.x0,dy=y-P.y0,m=Math.hypot(dx,dy);S.mv.x=S.mv.y=0;if(dur<.22&&m>26)rueElan(dx,dy);else if(dur<.25&&S.tmax<12)rueAttaque()},
  act(){rueAttaque()},touche(k){if(k===' '||k==='x')rueAttaque();if(k==='c'||k==='Shift')rueElan(S.j.dir,0)},
  etat(){return 'vague '+S.vague+' x='+R(S.j.x)+' pv '+S.j.pv+' ennemis '+S.en.length+' tues '+S.tues}},o);
