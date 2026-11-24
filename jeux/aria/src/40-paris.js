// ================================================================ PARIS VU DU CIEL, LA NUIT : dalles de 240 × 960 (unités logiques) calculées en relief
const FH=960,FHN=FH*K;
const ZINC=['#6c7888','#5e6b7c','#77828f','#56627a','#808a96','#667284','#70798a','#5a6676','#7c8696'],ARDOISE=['#3e4658','#444c60','#39415a','#4a5268'],VERTS=['#2f7040','#3c8448','#28603a','#4a8a3e','#356a36'],AUTOS=['#c03a3a','#d8d8e0','#3a6ac0','#e0b030','#30343c','#8a8f98','#f0f0f0'];
const ASPH='#262d3b',TROT='#454e60',PAVE='#77746c',EAU='#12324c';
function paris(type,graine){const r=hasard(graine),ch=a=>a[(r()*a.length)|0];
  return forge(GW,FH,T=>{
  T.box(0,0,GW,FH,0,0,1,ASPH);
  // ---- un immeuble : toit à quatre pans ou mansarde en zinc, joints debout, souches de cheminée, lucarnes éclairées
  function bati(x,y,w,h,o){o=o||{};const z=o.z||9+r()*5,col=o.col||ch(ZINC),m=Math.min(w,h);if(w<3||h<3)return;
    if(o.pans||(m<=15&&r()<.75)){T.box(x,y,w,h,z,m*.3,m/2,col)}
    else{T.box(x,y,w,h,z,2.4,2.2,col);T.box(x+2.6,y+2.6,w-5.2,h-5.2,z+2.4,.6,1.2,o.col2||ch(ZINC));
      for(let i=0;i<3;i++)if(r()<.5)T.box(x+4+r()*(w-11),y+4+r()*(h-10),3+r()*2,2.4,z+3,1.4,.8,'#aab3bd');
      if(r()<.35&&w>12&&h>12){const sx=x+4+r()*(w-12),sy=y+4+r()*(h-11);T.box(sx,sy,4,3,z+3,1,.7,'#9fc0d8');if(r()<.5)T.teinte(sx+.7,sy+.7,2.6,1.6,'#ffd98a',.85)}}
    const vert=w<h;T.rel(x+1,y+1,w-2,h-2,(a,b,i,j)=>(vert?j:i)%4===0?-.28:0);
    const nc=1+((r()*3)|0);for(let i=0;i<nc;i++){const cx0=vert?x+1+r()*(w-4):x+2+r()*(w-5),cy0=vert?y+2+r()*(h-5):y+1+r()*(h-4);T.box(cx0,cy0,2.4,1.7,z+2.5,2.6,.5,'#8f5a46');T.pix(cx0+.8,cy0+.6,'#d89a70',.3)}
    for(let px=x+1.6;px<x+w-1.5;px+=2.8){if(r()<.2)T.pix(px,y+.9,r()<.8?'#ffd98a':'#bfe6ff');if(r()<.2)T.pix(px,y+h-1.2,r()<.8?'#ffd98a':'#ffe9b8')}
    for(let py=y+1.6;py<y+h-1.5;py+=2.8){if(r()<.2)T.pix(x+.9,py,'#ffd98a');if(r()<.2)T.pix(x+w-1.2,py,r()<.8?'#ffd98a':'#bfe6ff')}
    if(z>15.5)T.pix(x+1.5,y+1.5,'#ff4a4a')}
  function arbre(x,y,q){q=q||2.2+r()*1.4;T.ell(x,y,q,q,1,3+r()*3,ch(VERTS))}
  function lampe(x,y,f){T.lueur(x,y,f||10,'#ffc670',.62);T.pix(x,y,'#fff2c8')}
  function auto(x,y,vert,phare){const w=vert?3.4:6.4,h=vert?6.4:3.4,c=ch(AUTOS);T.box(x,y,w,h,.4,2,1.3,c);T.teinte(vert?x+.6:x+1.6,vert?y+1.6:y+.6,vert?2.2:3,vert?3:2.2,'#1a2030');
    if(phare){if(vert){T.pix(x+.5,y+(phare>0?6.2:0),'#fff6c0');T.pix(x+2.6,y+(phare>0?6.2:0),'#fff6c0');T.pix(x+.5,y+(phare>0?0:6.2),'#ff3030');T.pix(x+2.6,y+(phare>0?0:6.2),'#ff3030');T.lueur(x+1.7,y+(phare>0?11:-5),6,'#fff2c0',.5)}
      else{T.pix(x+(phare>0?6.2:0),y+.5,'#fff6c0');T.pix(x+(phare>0?6.2:0),y+2.6,'#fff6c0');T.pix(x+(phare>0?0:6.2),y+.5,'#ff3030');T.pix(x+(phare>0?0:6.2),y+2.6,'#ff3030');T.lueur(x+(phare>0?11:-5),y+1.7,6,'#fff2c0',.5)}}}
  // ---- îlot haussmannien : couronne d'immeubles autour d'une cour
  function ilot(bx,by,bw,bh){T.box(bx,by,bw,bh,0,.7,1,TROT);const k=r();
    if(k<.1&&bw>40){square(bx+2,by+2,bw-4,bh-4);return}
    const d=12+((r()*4)|0),x0=bx+2,y0=by+2,w=bw-4,h=bh-4;
    if(w<2*d+8||h<2*d+8){let y=y0;while(y<y0+h-1){let hg=13+((r()*14)|0);if(y0+h-(y+hg)<10)hg=y0+h-y;let x=x0;while(x<x0+w-1){let wd=12+((r()*14)|0);if(x0+w-(x+wd)<10)wd=x0+w-x;bati(x,y,wd-.6,hg-.6);x+=wd}y+=hg}return}
    T.plat(x0+d,y0+d,w-2*d,h-2*d,.25,'#202634');
    for(const yy of[y0,y0+h-d]){let x=x0;while(x<x0+w-1){let wd=12+((r()*15)|0);if(x0+w-(x+wd)<10)wd=x0+w-x;bati(x,yy,wd-.5,d);x+=wd}}
    for(const xx of[x0,x0+w-d]){let y=y0+d+.4;while(y<y0+h-d-1){let hg=12+((r()*15)|0);if(y0+h-d-(y+hg)<10)hg=y0+h-d-y;bati(xx,y,d,hg-.5);y+=hg}}
    const ix=x0+d+1,iy=y0+d+1,iw=w-2*d-2,ih=h-2*d-2;
    if(ih>44&&r()<.75){const my=iy+ih*(.35+r()*.3);bati(ix-1,my,iw+2,10+r()*3,{z:7+r()*4})}
    if(iw>30&&r()<.5)bati(ix+iw/2-5,iy+2,9,ih*.3,{z:6});
    for(let i=0;i<(iw*ih)/90;i++){const ax=ix+2+r()*(iw-4),ay=iy+2+r()*(ih-4);if(T.haut(ax,ay)<1){if(r()<.6)arbre(ax,ay,1.8+r());else T.pix(ax,ay,'#ffd98a')}}
    for(let i=0;i<5;i++){const ax=ix+r()*iw,ay=iy+r()*ih;if(T.haut(ax,ay)<1&&r()<.6)T.lueur(ax,ay,5,'#ffcf80',.4)}}
  function square(x,y,w,h){T.plat(x,y,w,h,.3,'#27482f');T.ton(x,y,w,h,(a,b,i,j)=>1+(((i*7+j*13)%5)-2)*.03);
    T.plat(x,y+h/2-1.5,w,3,.3,'#857c66');T.plat(x+w/2-1.5,y,3,h,.3,'#857c66');T.ell(x+w/2,y+h/2,6,6,.3,.5,'#8f866e');T.ell(x+w/2,y+h/2,3.4,3.4,.5,.6,'#1d4d6a');T.pix(x+w/2,y+h/2,'#cfefff');
    for(let i=0;i<w*h/38;i++){const ax=x+3+r()*(w-6),ay=y+3+r()*(h-6);if(Math.abs(ax-x-w/2)>4&&Math.abs(ay-y-h/2)>4)arbre(ax,ay,2.4+r()*2.4)}
    for(const[a,b]of[[.25,.25],[.75,.25],[.25,.75],[.75,.75]])lampe(x+w*a,y+h*b,8);T.lueur(x+w/2,y+h/2,9,'#9fe0ff',.4)}
  // ---- voirie : marquages, passages piétons, arbres d'alignement, réverbères, voitures
  function rueH(y0,x0,x1){x0=x0||0;x1=x1||GW;for(let x=x0+4;x<x1;x+=11)T.teinte(x,y0+8.7,5,.7,'#8d94a0');
    if(x1-x0>30)for(let i=0;i<5;i++){const x=x0+6+r()*(x1-x0-18),haut=r()<.5;if((x>66&&x<96)||(x>154&&x<184))continue;auto(x,haut?y0+2.6:y0+12,false,r()<.45?(haut?-1:1):0)}
    for(let x=x0+10;x<x1;x+=34){if((x>70&&x<96)||(x>158&&x<184))continue;lampe(x,y0+1.5);lampe(x+17,y0+16.5)}}
  function avenue(ax,y0,y1){for(let y=y0;y<y1;y+=11)T.teinte(ax+8.7,y,.7,5,'#8d94a0');
    for(let y=y0+5;y<y1;y+=9.5){const q=y%120;if(q<22)continue;arbre(ax+1.6,y,2.1);arbre(ax+16.4,y+3,2.1)}
    for(let y=y0+8;y<y1;y+=40){const q=y%120;if(q<20)continue;lampe(ax+3.5,y,9);lampe(ax+14.5,y+20,9)}
    for(let i=0;i<(y1-y0)/70;i++){const y=y0+r()*(y1-y0-8),g=r()<.5;if(y%120<20)continue;auto(ax+(g?4.6:10.2),y,true,g?1:-1)}}
  function carrefour(ax,y0){for(let i=0;i<5;i++){T.teinte(ax+1.5+i*3.3,y0-3.4,1.6,2.6,'#b9bec8');T.teinte(ax+1.5+i*3.3,y0+19,1.6,2.6,'#b9bec8');T.teinte(ax-3.4,y0+1.5+i*3.3,2.6,1.6,'#b9bec8');T.teinte(ax+19,y0+1.5+i*3.3,2.6,1.6,'#b9bec8')}
    T.pix(ax-1,y0-1,'#40ff70');T.pix(ax+18.6,y0+18.6,'#ff3a3a');T.pix(ax+18.6,y0-1,'#ffb020')}
  const COLS=[[2,70],[94,66],[182,56]],libre=new Array(8).fill(true);
  // ---- grands sites
  const SITES={
   seine(){const y0=360;libre[3]=libre[4]=false;T.plat(0,y0+8,GW,240,-.5,EAU);
     T.rel(0,y0+8,GW,240,(a,b)=>Math.sin(b*1.7+Math.sin(a*.19)*2.4)*.22+Math.sin(a*.9+b*.4)*.08);T.ton(0,y0+8,GW,240,(a,b)=>1+Math.sin(b*.31+a*.05)*.12);
     T.box(0,y0+2,GW,9,0,1.6,1.2,'#7a808a');T.box(0,y0+235,GW,9,0,1.6,1.2,'#7a808a');
     for(let x=5;x<GW;x+=9){arbre(x,y0+6,2);arbre(x+4,y0+240,2)}
     for(let x=12;x<GW;x+=26){lampe(x,y0+10,8);lampe(x+13,y0+236,8);T.teinte(x,y0+13,.7,5+r()*5,'#c9a060',.5);T.teinte(x+13,y0+226-r()*4,.7,6,'#c9a060',.5)}
     // île de la Cité
     T.poly([[4,485],[26,420],[214,414],[238,485],[214,556],[26,550]],0,1.6,1.4,'#6f7684');T.poly([[8,485],[28,424],[212,418],[234,485],[212,552],[28,546]],1.6,.3,1,'#4c5464');
     for(let i=0;i<9;i++)arbre(10+r()*12,478+r()*14,2.4);T.pix(15,485,'#ffd98a');
     // pont Neuf, place Dauphine, palais de Justice et Sainte-Chapelle
     pont(20,8,y0+10,y0+236,1);T.poly([[31,440],[44,432],[44,538],[31,530]],1.6,10,3,'#737e8e');T.plat(35,452,6,66,1.7,'#27482f');for(let y=456;y<516;y+=7)arbre(38,y,2);
     bati(47,428,25,34,{z:11,col:'#3e4658',col2:'#444c60'});bati(47,466,10,60,{z:11,col:'#444c60'});bati(61,470,11,22,{z:10,col:'#39415a'});T.plat(58,496,13,28,1.7,'#5a5f6a');bati(47,528,25,16,{z:11,col:'#3e4658'});
     T.box(60,498,5,22,8,9,2.5,'#2c3a66');T.rel(60,498,5,22,(a,b,i,j)=>j%3===0?-.3:0);T.ell(62.5,507,1.1,1.1,18,8,'#c9a25a',.6);T.pix(62.5,507,'#fff2c8');T.lueur(62,509,10,'#ffc670',.45);
     pont(74,18,y0+10,y0+236,0);
     // préfecture, Hôtel-Dieu, parvis, Notre-Dame
     ilotSimple(95,422,24,60);ilotSimple(95,490,22,56);pont(121,10,y0+10,y0+236,0);
     T.plat(132,440,12,92,1.7,PAVE);T.ton(132,440,12,92,(a,b,i,j)=>(i+j)%4<2?1:.88);
     bati(133,424,60,14,{z:10});bati(134,534,54,12,{z:10});
     const N='#bdb5a4';T.box(146,476,46,18,16,5,9,'#7d8894');T.rel(146,476,46,18,(a,b,i,j)=>i%3===0?-.3:0);T.box(165,464,10,42,16,5,5,'#7d8894');
     T.ell(193,485,8,9,10,7,'#7d8894');for(let a=-1.3;a<=1.31;a+=.43)T.cap(193+Math.cos(a)*8,485+Math.sin(a)*9,193+Math.cos(a)*13,485+Math.sin(a)*14,.6,.6,3,3,N);
     for(let x=149;x<190;x+=5){if(x>162&&x<176)continue;T.box(x,470,1.3,6,6,2,.6,N);T.box(x,494,1.3,6,6,2,.6,N)}
     T.box(136,473,10,10,24,1.5,1.2,N);T.box(136,487,10,10,24,1.5,1.2,N);T.box(144,482,3,6,14,2,1,N);for(const ty of[473,487]){T.trait(137.5,ty+1.5,144.5,ty+1.5,.8);T.trait(137.5,ty+8.5,144.5,ty+8.5,.8);T.trait(137.5,ty+1.5,137.5,ty+8.5,.8);T.trait(144.5,ty+1.5,144.5,ty+8.5,.8)}
     T.cap(170,485,170,485,1.6,1.6,22,16,'#8a94a0');T.pix(170,485,'#fff6d8');T.lueur(138,485,16,'#ffd9a0',.5);T.lueur(170,485,14,'#ffd9a0',.3);
     T.plat(202,462,24,46,1.7,'#27482f');for(let i=0;i<16;i++)arbre(204+r()*20,464+r()*42,2.3);lampe(214,485,9);
     // quais bas de l'île, bateaux
     for(let x=30;x<212;x+=17){lampe(x,421.5,6);lampe(x+8,548.5,6)}
     bateau(40,y0+22,1);bateau(150,y0+26,0);bateau(100,y0+214,0);bateau(196,y0+218,1);peniche(8,y0+214);peniche(206,y0+20);peniche(224,y0+24)},
   louvre(){libre[1]=libre[2]=libre[3]=false;const y0=120;T.plat(46,y0+18,148,342,.2,'#3a3f48');
     // rues latérales
     T.plat(44,y0+18,6,342,0,ASPH);T.plat(190,y0+18,6,342,0,ASPH);for(let y=y0+24;y<y0+356;y+=30){lampe(47,y,8);lampe(193,y+15,8)}
     for(const[bx,bw]of[[2,42],[196,42]])for(let b=1;b<4;b++)ilot(bx,b*120+18,bw,100);
     // jardin des Tuileries
     const G='#8a8370';T.plat(52,y0+20,136,112,.3,G);T.ton(52,y0+20,136,112,(a,b,i,j)=>.86+(((i*5+j*11)%7))*.012);
     for(const[gx0,gw]of[[56,58],[126,58]]){T.plat(gx0,y0+52,gw,34,.35,'#25472d');T.plat(gx0,y0+92,gw,34,.35,'#2b5234');for(let i=0;i<40;i++)arbre(gx0+3+(i%8)*7.4+r(),y0+25+((i/8)|0)*5.4+r(),2.5)}
     T.ell(120,y0+38,12,12,.3,.6,'#9a927c');T.ell(120,y0+38,9.5,9.5,.2,.4,'#1d4d6a');T.pix(120,y0+38,'#dff4ff');T.lueur(120,y0+38,13,'#9fe0ff',.45);
     T.ell(120,y0+110,9,9,.3,.6,'#9a927c');T.ell(120,y0+110,6.8,6.8,.2,.4,'#1d4d6a');T.pix(120,y0+110,'#dff4ff');T.lueur(120,y0+110,10,'#9fe0ff',.45);
     for(let y=y0+24;y<y0+130;y+=15){lampe(117,y,6);lampe(123,y+7,6)}
     // Carrousel
     T.plat(52,y0+134,136,44,.3,'#7c7a72');for(let a=0;a<6;a++){const an=Math.PI*(.15+a*.14);T.ruban(120,y0+176,120-Math.cos(an)*60,y0+176-Math.sin(an)*40,2.2,.5,'#2b5234')}
     T.box(113,y0+150,14,7,0,10,2,'#c9b8a8');T.teinte(116,y0+152,8,2.6,'#d8a860',.4);T.lueur(120,y0+158,12,'#ffd9a0',.5);
     // ailes, cour Napoléon, pyramide
     const A0='#3e4658',A1='#474f64';T.plat(66,y0+178,108,104,.3,'#8f8b80');T.ton(66,y0+178,108,104,(a,b,i,j)=>(((i>>2)+(j>>2))&1)?.9:1);
     for(const ax of[52,174]){T.box(ax,y0+134,14,150,0,13,3,A0);T.box(ax+2.5,y0+136.5,9,145,13,2.6,3,A1);T.rel(ax,y0+134,14,150,(a,b,i,j)=>j%4===0?-.25:0);
       for(const py of[134,196,268])T.box(ax-1.5,y0+py,17,15,0,17,5,'#4a5268',1);for(let y=y0+140;y<y0+280;y+=5){T.pix(ax+(ax<100?13.4:.3),y,'#ffd98a')}}
     T.box(107,y0+218,26,26,.4,14,13,'#7fd0dc',0,.5);T.trait(107,y0+218,133,y0+244,.3);T.trait(133,y0+218,107,y0+244,.3);T.lueur(120,y0+231,30,'#bff2ff',.55);
     for(const[px,py]of[[120,206],[100,231],[140,231]])T.box(px-2.5,y0+py-2.5,5,5,.4,3,2.5,'#9fe6f0',0,.6);
     for(const[px,py,pw,ph]of[[92,214,12,10],[136,214,12,10],[92,238,12,10],[136,238,12,10]]){T.plat(px,y0+py,pw,ph,.15,'#1d4d6a');T.pix(px+pw/2,y0+py+ph/2,'#dff4ff')}
     // cour Carrée
     T.box(66,y0+282,108,14,0,13,3,A0);T.box(80,y0+296,80,76,0,13,3,A0);T.plat(92,y0+308,56,52,.3,'#8f8b80');T.ton(92,y0+308,56,52,(a,b,i,j)=>(((i>>2)+(j>>2))&1)?.9:1);
     T.box(82.5,y0+298.5,75,71,13,2.6,3,A1);T.plat(92,y0+308,56,52,.3,'#8f8b80');
     for(const[px,py]of[[80,296],[146,296],[80,358],[146,358],[113,293],[113,361],[77,327],[149,327]])T.box(px,y0+py,14,14,0,17,5,'#4a5268',1);
     T.ell(120,y0+334,5,5,.3,.6,'#9a927c');T.ell(120,y0+334,3.4,3.4,.2,.4,'#1d4d6a');T.pix(120,y0+334,'#dff4ff');
     for(const[px,py]of[[96,312],[144,312],[96,356],[144,356]])lampe(px,y0+py,9);for(let x=96;x<146;x+=6){T.pix(x,y0+308.6,'#ffd98a');T.pix(x,y0+359.4,'#ffd98a')}},
   etoile(){const ex=120,ey=480;
     for(let i=0;i<12;i++){const a=i*TAU/12+.26;T.ruban(ex,ey,ex+Math.cos(a)*330,ey+Math.sin(a)*330,i%3===0?17:12,0,ASPH)}
     T.trou(ex,ey,62,62,0,ASPH);T.trou(ex,ey,40,40,.2,'#5d626c');
     T.ton(ex-40,ey-40,80,80,(a,b)=>{const d=Math.hypot(a-ex,b-ey);if(d>40)return 1;const an=Math.atan2(b-ey,a-ex);return (Math.sin(an*12)>0?1.16:.86)*(d<19?1.1:1)});
     for(let a=0;a<TAU;a+=.105){T.pix(ex+Math.cos(a)*41,ey+Math.sin(a)*41,'#8d94a0',.2)}
     for(let i=0;i<12;i++){const a=i*TAU/12+.26;for(let d=70;d<320;d+=9){for(const s of[-1,1]){const l=(i%3===0?10:7.6)*s,x=ex+Math.cos(a)*d-Math.sin(a)*l,y=ey+Math.sin(a)*d+Math.cos(a)*l;if(x>2&&x<GW-2&&y>244&&y<716&&T.haut(x,y)<1)arbre(x,y,2)}}
       for(let d=74;d<320;d+=34){const x=ex+Math.cos(a)*d,y=ey+Math.sin(a)*d;if(x>2&&x<GW-2&&y>244&&y<716)lampe(x,y,9)}
       const b=a+TAU/24;lampe(ex+Math.cos(b)*58,ey+Math.sin(b)*58,10)}
     for(let i=0;i<16;i++){const a=r()*TAU,d=46+r()*12,x=ex+Math.cos(a)*d,y=ey+Math.sin(a)*d,v=Math.abs(Math.cos(a))>.7;auto(x,y,v,r()<.5?1:-1)}
     // l'Arc de triomphe : quatre piles, attique, terrasse
     const P='#cfc4ac';for(const[px,py]of[[108,471],[125,471],[108,482],[125,482]])T.box(px,py,7,7,0,26,1.5,P);
     T.box(107,470,26,20,26,3,1.5,P,0,.25);T.box(109.5,472.5,21,15,29,.6,1,'#b8ae98',0,.2);T.trait(110,473,130,473,.6);T.trait(110,487,130,487,.6);T.trait(110,473,110,487,.6);T.trait(130,473,130,487,.6);
     for(const[px,py]of[[107,470],[132,470],[107,489],[132,489]])T.pix(px,py,'#fff6d8');T.lueur(ex,ey,34,'#ffd9a0',.6);T.pix(ex,ey,'#3a70ff')},
   eiffel(){for(let b=2;b<6;b++)libre[b]=false;const tx=120,ty=350;
     T.plat(58,240,124,480,.2,'#3a3f48');T.plat(58,240,6,480,0,ASPH);T.plat(176,240,6,480,0,ASPH);for(let y=250;y<716;y+=32){lampe(61,y,8);lampe(179,y+16,8)}
     for(const[bx,bw]of[[2,54],[184,54]])for(let b=2;b<6;b++)ilot(bx,b*120+18,bw,100);
     // la Seine et le pont d'Iéna
     T.plat(0,258,GW,44,-.5,EAU);T.rel(0,258,GW,44,(a,b)=>Math.sin(b*1.7+Math.sin(a*.19)*2.4)*.22);T.ton(0,258,GW,44,(a,b)=>1+Math.sin(b*.31+a*.05)*.12);
     T.box(0,254,GW,5,0,1.6,1.2,'#7a808a');T.box(0,301,GW,5,0,1.6,1.2,'#7a808a');pont(111,18,258,302,0);bateau(30,270,1);bateau(170,284,0);peniche(60,290);peniche(200,262);
     for(let x=6;x<GW;x+=22){if(x>104&&x<136)continue;lampe(x,256,7);lampe(x+11,304,7);T.teinte(x,260,.7,6,'#c9a060',.5)}
     // jardins du Trocadéro (bord haut)
     T.plat(64,240,112,14,.3,'#27482f');T.plat(104,240,32,14,.2,'#1d4d6a');for(let x=106;x<136;x+=4)T.pix(x,246,'#dff4ff');T.lueur(120,246,18,'#9fe0ff',.5);for(let i=0;i<22;i++){const x=66+r()*108;if(x<102||x>138)arbre(x,242+r()*10,2.4)}
     // Champ-de-Mars
     T.plat(64,306,112,414,.3,'#8a8370');T.ton(64,306,112,414,(a,b,i,j)=>.82+(((i*5+j*11)%7))*.012);
     for(let y=396;y<716;y+=64){T.plat(96,y,48,56,.35,'#2b5a34');T.ton(96,y,48,56,(a,b,i,j)=>(j>>2)&1?1.07:.95);T.plat(68,y,20,56,.35,'#25472d');T.plat(152,y,20,56,.35,'#25472d');
       for(let q=0;q<10;q++){arbre(70+r()*16,y+3+q*5.3,2.5);arbre(154+r()*16,y+3+q*5.3,2.5)}
       for(const lx of[92,148]){lampe(lx,y+10,7);lampe(lx,y+42,7)}}
     // la tour : quatre piliers, deux étages, la flèche ; illuminée
     const F='#b98440',E=.42;T.plat(84,314,72,72,.3,'#6d6a62');T.ton(84,314,72,72,(a,b,i,j)=>(((i>>2)+(j>>2))&1)?.92:1);
     const pieds=[[-27,-27],[27,-27],[-27,27],[27,27]];
     for(const[dx,dy]of pieds){T.box(tx+dx-7,ty+dy-7,14,14,0,6,3,'#8a6a40',0,.2);T.cap(tx+dx,ty+dy,tx+dx*.52,ty+dy*.52,5.5,4,6,12,F,E)}
     for(const[a,b]of[[0,1],[0,2],[1,3],[2,3]]){const p=pieds[a],q=pieds[b];T.cap(tx+p[0]*.8,ty+p[1]*.8,tx+q[0]*.8,ty+q[1]*.8,2.2,2.2,8,6,F,E)}
     T.box(tx-17,ty-17,34,34,19,2.4,2,F,0,E);T.plat(tx-9,ty-9,18,18,.3,'#6d6a62');for(const[dx,dy]of pieds)T.cap(tx+dx*.52,ty+dy*.52,tx+dx*.26,ty+dy*.26,4,3,22,10,F,E);
     T.box(tx-9.5,ty-9.5,19,19,34,2.2,1.6,F,0,E);T.box(tx-5,ty-5,10,10,37,26,5,'#c99548',0,.5);T.ell(tx,ty,2.2,2.2,63,3,'#e8c070',.7);T.pix(tx,ty,'#ffffff');
     for(let q=-15;q<=15;q+=5){T.trait(tx-17,ty+q,tx-10,ty+q,.7);T.trait(tx+10,ty+q,tx+17,ty+q,.7);T.trait(tx+q,ty-17,tx+q,ty-10,.7);T.trait(tx+q,ty+10,tx+q,ty+17,.7)}
     for(const[dx,dy]of pieds)for(let q=.56;q<1;q+=.1){const cx0=tx+dx*q,cy0=ty+dy*q;T.trait(cx0-3,cy0+3*Math.sign(dx*dy),cx0+3,cy0-3*Math.sign(dx*dy),.8)}
     T.lueur(tx,ty,52,'#ffc860',.6);for(const[dx,dy]of pieds){T.pix(tx+dx*1.2,ty+dy*1.2,'#fff2c8');T.pix(tx+dx*.52,ty+dy*.52,'#fff6d8')}},
   gare(){libre[2]=libre[3]=libre[4]=false;const y0=240;T.plat(26,y0+18,188,342,.1,'#33302e');T.ton(26,y0+18,188,342,(a,b,i,j)=>.85+(((i*7+j*3)%5))*.05+(j%3===0?.1:0));
     for(const[bx,bw]of[[2,22],[216,22]])for(let b=2;b<5;b++)ilot(bx,b*120+18,bw,100);
     // faisceau de voies, traverses, caténaires
     for(let x=34;x<208;x+=9.4){for(const d of[0,2.6]){T.box(x+d,y0+18,.9,342,.1,.7,.4,'#9aa2ac')}}
     for(let y=y0+30;y<y0+356;y+=26){T.box(30,y,180,1,5,.6,.5,'#5a626e');for(let x=34;x<208;x+=18.8)T.pix(x+1.3,y+.4,r()<.5?'#40ff70':'#ff3a3a')}
     // trains : rames à grande vitesse et trains de banlieue, fenêtres éclairées
     for(const[tx0,ty0,n,c1,c2]of[[33,y0+40,5,'#d8dce4','#c03a3a'],[52,y0+150,6,'#d8dce4','#3a6ac0'],[80,y0+30,4,'#c8ccd4','#3a6ac0'],[99,y0+120,6,'#e0e4ea','#c03a3a'],[146,y0+60,5,'#d8dce4','#e0b030'],[183,y0+100,6,'#d8dce4','#3a6ac0'],[127,y0+210,3,'#c8ccd4','#c03a3a']])
       for(let i=0;i<n;i++){const y=ty0+i*25;T.box(tx0,y,4.8,23.6,.6,3.4,1.8,c1,1);T.teinte(tx0+.4,y+2,.7,19.6,c2);T.teinte(tx0+3.7,y+2,.7,19.6,c2);for(let q=3;q<21;q+=2.6){T.pix(tx0+.3,y+q,'#ffe9b0');T.pix(tx0+4.4,y+q,'#ffe9b0')}if(i===0){T.pix(tx0+1,y,'#fff6c0');T.pix(tx0+3.4,y,'#fff6c0');T.lueur(tx0+2.4,y-6,7,'#fff2c0',.5)}}
     // halle : trois grandes verrières, quais éclairés, bâtiment des voyageurs avec horloge
     for(let i=0;i<3;i++){const vx=30+i*61;T.box(vx,y0+250,58,96,0,15,29,'#3f7480',1,.12);T.rel(vx,y0+250,58,96,(a,b,i2,j)=>j%6===0?-.8:i2%9===0?-.4:0);
       for(let q=0;q<26;q++)T.teinte(vx+4+r()*48,y0+254+r()*88,3,2,'#bfeee0',.45);T.lueur(vx+29,y0+298,34,'#bff2e0',.3)}
     for(let x=38;x<208;x+=18.8)for(let y=y0+200;y<y0+250;y+=12)lampe(x+6,y,5);
     T.box(26,y0+346,188,16,0,15,3,'#4a5268');T.box(28.5,y0+348.5,183,11,15,2.4,2,'#565e74');T.box(108,y0+343,24,20,0,20,5,'#5a6278',1);T.ell(120,y0+353,3,3,20,1,'#fff2c8',.9);T.lueur(120,y0+353,10,'#ffe9b0',.5);
     for(let x=32;x<210;x+=5)T.pix(x,y0+361.4,'#ffd98a')},
   opera(){libre[4]=false;const y0=480;T.plat(0,y0+18,GW,100,0,ASPH);ilot(2,y0+18,56,100);ilot(182,y0+18,56,100);
     T.plat(62,y0+18,116,100,.2,'#55585f');T.ton(62,y0+18,116,100,(a,b,i,j)=>(((i>>2)+(j>>2))&1)?.92:1);
     const P='#b9b09c';T.box(86,y0+26,68,84,0,12,3,P);T.box(90,y0+62,60,44,12,10,22,'#5a6672');T.rel(90,y0+62,60,44,(a,b,i,j)=>i%4===0?-.3:0);
     T.ell(120,y0+50,19,19,12,12,'#5f9c86');T.rel(101,y0+31,38,38,(a,b)=>Math.abs(Math.sin(Math.atan2(b-y0-50,a-120)*8))<.2?-.5:0);T.ell(120,y0+50,3,3,24,5,'#d8b050',.6);T.pix(120,y0+50,'#fff6d8');
     T.box(86,y0+26,68,9,12,3,2,'#c9c0aa');for(let x=90;x<152;x+=6)T.pix(x,y0+27,'#ffd98a');for(const px of[88,151]){T.ell(px,y0+28,2,2,15,4,'#e0b850',.7);T.pix(px,y0+28,'#fff6d8')}
     T.lueur(120,y0+20,30,'#ffd9a0',.55);T.lueur(120,y0+66,44,'#ffd9a0',.25);for(const[px,py]of[[70,30],[170,30],[70,104],[170,104],[70,66],[170,66]])lampe(px,y0+py,10);
     for(let i=0;i<6;i++)auto(64+r()*14,y0+24+r()*84,true,r()<.5?1:-1);for(let i=0;i<6;i++)auto(160+r()*12,y0+24+r()*84,true,r()<.5?1:-1)}};
  function ilotSimple(x,y,w,h){T.box(x,y,w,h,1.6,.3,1,TROT);const d=8;bati(x+1,y+1,w-2,d,{z:10});bati(x+1,y+h-d-1,w-2,d,{z:10});bati(x+1,y+d+1.4,d,h-2*d-2.8,{z:10});bati(x+w-d-1,y+d+1.4,d,h-2*d-2.8,{z:10});T.plat(x+d+1,y+d+1,w-2*d-2,h-2*d-2,1.8,'#27482f');arbre(x+w/2,y+h/2,2.5)}
  function pont(x,l,ya,yb,neuf){T.box(x-1,ya-6,l+2,yb-ya+12,2,1.4,1.4,'#6a7282');T.plat(x+.8,ya-6,l-1.6,yb-ya+12,3,'#2b3240');if(l>12)for(let y=ya-4;y<yb+6;y+=11)T.teinte(x+l/2-.4,y,.7,5,'#8d94a0');
    for(let y=ya+6;y<yb-2;y+=13){const sk=T.haut(x-3,y)>.5&&T.haut(x+l+3,y)>.5;if(sk)continue;T.ell(x-1,y,neuf?2.6:1.8,2.4,1,2.6,'#7a8292');T.ell(x+l+1,y,neuf?2.6:1.8,2.4,1,2.6,'#7a8292');T.pix(x,y,'#ffe2a0');T.pix(x+l-.4,y,'#ffe2a0');T.lueur(x+l/2,y,l*.7,'#ffc670',.35)}}
  function bateau(x,y,sens){T.box(x,y,30,7,0,2.6,3,'#e4e8ee',1);T.box(x+4,y+1.2,21,4.6,2,1.4,1,'#ffe2a0',0,.8);for(let q=5;q<24;q+=3)T.trait(x+q,y+1.2,x+q,y+5.6,.3);T.lueur(x+15,y+3.5,17,'#ffdc90',.5);T.pix(x+(sens?29:.4),y+3.4,'#40ff70');for(let q=2;q<9;q++)T.teinte(x+(sens?-q*2.4:30+q*2.4),y+3.2+Math.sin(q)*1.4,1.4,.7,'#3a6688')}
  function peniche(x,y){T.box(x,y,24,5.4,0,2,1.6,'#2e3440');T.box(x+2,y+1,13,3.4,1.6,.8,.6,'#4a3a30');T.box(x+17,y+.8,5,3.8,1.6,2,.8,'#c8ccd4');T.pix(x+18,y+2,'#ffd98a');T.pix(x+20,y+3.2,'#ffd98a')}
  if(SITES[type]&&type!=='etoile')SITES[type]();
  // ---- trame ordinaire : îlots, rues, avenues plantées
  const BANDE={seine:{3:null,4:null},louvre:{2:[44,196],3:[44,196]},eiffel:{2:[58,182],3:[58,182],4:[58,182],5:[58,182]},gare:{3:[26,214],4:[26,214]}}[type]||{};
  for(let b=0;b<8;b++)if(libre[b])for(const[bx,bw]of COLS)ilot(bx,b*120+18,bw,100);
  for(let b=0;b<8;b++){const y0=b*120,c=BANDE[b];if(c===null)continue;
    if(c){rueH(y0,0,c[0]);rueH(y0,c[1],GW)}else{rueH(y0);carrefour(74,y0);carrefour(162,y0)}
    if(libre[b]){avenue(74,y0+18,y0+120);avenue(162,y0+18,y0+120)}}
  if(type==='etoile')SITES.etoile();
  },{k:K,sol:1,contour:false,pas:22,gain:.8,grain:.07,omb:type==='eiffel'?80:type==='etoile'?44:22})}
