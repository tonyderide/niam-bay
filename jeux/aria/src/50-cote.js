// ================================================================ MOTEUR VUE DE CÔTÉ : niveaux en tuiles de 24 px, décor en relief, éclairage, personnage
const TU=24;
function grille(c,r){const g=[];for(let y=0;y<r;y++)g.push(new Array(c).fill('.'));return{c,r,g,
  r_(x,y,w,h,ch){for(let j=y;j<y+h;j++)for(let i=x;i<x+w;i++)if(j>=0&&j<r&&i>=0&&i<c)g[j][i]=ch;return this},
  get(x,y){return y<0?'.':y>=r||x<0||x>=c?'#':g[y][x]}}}
const plein=ch=>ch==='#'||ch==='c'||ch==='D';
// ---------------------------------------------------------------- accessoires de décor (peints dans le relief) : x = gauche, y = sol
const cyl=(T,x,y,w,h,z,dz,col,e)=>{T.box(x,y,w,h,z,0,.01,col,0,e);T.rel(x,y,w,h,a=>dz*Math.sqrt(Math.max(0,1-Math.pow((a-x-w/2)/(w/2),2))))};
const PROPS={
  caisse(T,x,y,r){const s=20+((r()*3)|0)*2,c=['#8a6a40','#7a5c38','#96744a'][(r()*3)|0];T.box(x,y-s,s,s,13,2,2,c);for(let q=5;q<s-2;q+=5)T.trait(x+2,y-s+q,x+s-2,y-s+q,.6);T.trait(x+2,y-s+2,x+s-2,y-2,.9);T.box(x,y-s,s,2.5,15,1,1,'#6a4c2c');T.box(x,y-3,s,3,15,1,1,'#6a4c2c');if(r()<.5)T.teinte(x+s/2-3,y-s/2-2,6,4,'#2a2420')},
  baril(T,x,y,r){const c=['#3a5a7a','#7a3a2a','#4a5a3a','#6a6a70'][(r()*4)|0];cyl(T,x,y-30,20,30,8,6,c);for(const q of[4,14,25])T.trait(x,y-30+q,x+20,y-30+q,.8);T.teinte(x+1,y-30,18,2,'#9aa0a8');T.ton(x,y-12,20,12,(a,b)=>.7+((a*7+b*3)%5)*.06);if(r()<.4){T.teinte(x+5,y-22,10,7,'#e8c020');T.teinte(x+8,y-20,4,3,'#20242a')}},
  etagere(T,x,y,r){for(const px of[x,x+52])T.box(px,y-78,3,78,5,1.4,1,'#4a525c');for(const q of[0,26,52,76]){T.box(x,y-q-3,55,3,6,1.4,1,'#5a626c');if(q<76)for(let px=x+4;px<x+48;){const w=7+r()*9,h=8+r()*13;if(r()<.75)T.box(px,y-q-3-h,w,h,4,3,1.5,['#8a6a40','#a0522d','#5a6a7a','#7a7a5a','#6a3a3a','#b8b0a0'][(r()*6)|0]);px+=w+1.5}}},
  machine(T,x,y,r){T.box(x,y-58,74,58,7,3,3,'#4a5a54');T.box(x+4,y-54,30,22,10,1,2,'#3a4844');T.box(x+38,y-54,32,36,9,2,2,'#56665e');for(let q=0;q<5;q++)T.trait(x+40,y-50+q*6,x+68,y-50+q*6,.8);
    for(const[gx,gy]of[[10,-44],[22,-44]]){T.ell(x+gx,y+gy,4.5,4.5,11,1,'#d8d4c0');T.trait(x+gx,y+gy,x+gx+2.5,y+gy-3,.6);T.pix(x+gx,y+gy,'#a02020',0)}
    for(let q=0;q<4;q++){T.box(x+6+q*7,y-26,4,6,10,1.5,1,q===1?'#a02828':'#2a2e34')}T.teinte(x,y-10,74,5,'#c8a820');for(let q=0;q<74;q+=10)T.teinte(x+q,y-10,5,5,'#20242a');
    cyl(T,x+56,y-110,9,54,6,4,'#6a7078');T.box(x+53,y-62,15,5,8,2,1.5,'#7a8088');T.box(x+53,y-92,15,4,8,2,1.5,'#7a8088');T.ton(x,y-58,74,58,(a,b)=>.82+Math.sin(a*.3)*Math.sin(b*.23)*.16);T.pix(x+8,y-34,'#40ff70',.9)},
  casiers(T,x,y,r){for(let q=0;q<4;q++){const px=x+q*15,ouv=r()<.2;T.box(px,y-52,14,52,5,2,1.5,['#4a6070','#566a78','#3e5462'][(r()*3)|0]);if(ouv){T.plat(px+2,y-49,10,45,2,'#14181e')}else{for(let j=0;j<3;j++)T.trait(px+3,y-46+j*3,px+11,y-46+j*3,.6);T.pix(px+11,y-26,'#c8ccd2',.2)}if(r()<.3)T.teinte(px+4,y-36,5,6,'#c8c0a8')}},
  etabli(T,x,y,r){T.box(x,y-27,62,5,9,2,1.5,'#6a5238');for(const px of[x+3,x+55])T.box(px,y-22,4,22,6,1.5,1,'#3e444c');T.box(x+6,y-12,50,3,6,1,1,'#3e444c');T.box(x+42,y-37,10,10,10,2,2,'#5a6068');T.box(x+45,y-41,4,5,11,1,1,'#8a9098');
    for(let q=0;q<4;q++)T.box(x+6+q*8,y-30-r()*2,5,3,10,1,1,['#a03030','#c8a020','#9aa0a8','#3a5a8a'][q]);T.box(x+10,y-10-8,12,8,5,2,1.5,'#7a3a2a')},
  palette(T,x,y,r){for(const q of[0,6])T.box(x,y-3-q,44,2.5,7,1,.8,'#8a6a40');for(const px of[x+1,x+20,x+40])T.box(px,y-6,3,4,6,1,.8,'#6a4c2c');for(let q=0;q<3;q++)for(let p=0;p<3-q;p++)T.box(x+3+p*13+q*6.5,y-17-q*8,13,9,7,3,4,['#c8c0a8','#b8b098'][q&1],1)},
  pneus(T,x,y,r){for(let q=0;q<3;q++){T.box(x+(q&1),y-9-q*9,26,9,6,3,4,'#20242a',1);T.trait(x+3,y-5-q*9,x+24,y-5-q*9,.6)}},
  bureau(T,x,y,r){T.box(x,y-25,54,4,9,1.6,1.2,'#6a5a48');T.box(x+2,y-21,16,21,6,1.6,1.2,'#5a4c3c');T.trait(x+3,y-14,x+17,y-14,.7);T.trait(x+3,y-7,x+17,y-7,.7);T.box(x+49,y-21,3,21,6,1,1,'#4a3e30');
    T.box(x+28,y-43,20,15,9,1.5,1.5,'#2a2e34');T.plat(x+30,y-41,16,11,9,'#0c1014');T.box(x+36,y-28,4,3,9,1,1,'#2a2e34');T.box(x+6,y-27.5,12,2,10,.6,.5,'#d8d4c0');
    T.box(x+62,y-22,14,4,7,1.5,1,'#3a3e46');T.box(x+73,y-40,3,22,7,1,1,'#3a3e46');T.box(x+67,y-18,3,18,5,1,1,'#2a2e34')},
  lit(T,x,y,r){T.box(x,y-9,50,3,6,1,1,'#4a525c');for(const px of[x+1,x+46])T.box(px,y-12,3,12,6,1,1,'#3e444c');T.box(x+1,y-14,48,6,7,2.5,3,['#3a5a48','#7a3a3a','#3a4a6a'][(r()*3)|0],1);T.box(x+2,y-17,11,5,8,2,2.5,'#c8c0b0',1)},
  camp(T,x,y,r){T.box(x,y-9,12,9,7,2,2,'#6a7078');T.box(x+2,y-12,8,3,8,1,1,'#3a3e46');T.pix(x+5,y-13,'#40a0ff',.9);T.pix(x+6,y-14,'#80c8ff',.7);cyl(T,x+16,y-7,5,7,6,2,'#c03030');cyl(T,x+23,y-7,5,7,6,2,'#d8d4c0');T.box(x+31,y-4,10,4,6,1.5,1.5,'#8a6a40');T.box(x+44,y-11,9,11,6,2.5,3,'#3a5a8a',1);T.lueur(x+6,y-14,12,'#60b0ff',.35)},
  jouet(T,x,y,r){T.ell(x+5,y-5,5,5,6,3,'#d8a060');T.ell(x+5,y-12,3.6,3.6,6,3,'#d8a060');T.ell(x+2,y-15,1.5,1.5,6,2,'#b88040');T.ell(x+8,y-15,1.5,1.5,6,2,'#b88040');T.pix(x+4,y-12.5,'#101010',0);T.pix(x+6.4,y-12.5,'#101010',0);T.box(x+14,y-6,6,6,6,1.5,1,'#c03030');T.box(x+21,y-6,6,6,6,1.5,1,'#3a6ac0');T.box(x+17,y-12,6,6,6,1.5,1,'#e0b030')},
  convoyeur(T,x,y,r){T.box(x,y-18,120,5,8,1.4,1.2,'#2a2e34');for(let q=4;q<120;q+=9)cyl(T,x+q-3,y-13,6,6,6,2,'#6a7078');for(const px of[x+6,x+58,x+110])T.box(px,y-9,4,9,5,1.4,1,'#3e444c');T.rel(x,y-18,120,5,(a)=>((a|0)%6===0?-.5:0));T.box(x+30,y-34,18,16,7,3,2,'#8a6a40');T.box(x+70,y-30,14,12,7,3,2,'#7a5c38')},
  armoire(T,x,y,r){T.box(x,y-64,34,64,6,2,2,'#56606a');T.trait(x+17,y-62,x+17,y-2,.9);T.teinte(x+5,y-56,8,10,'#c8a820');T.pix(x+8,y-52,'#20242a',0);T.pix(x+9,y-50,'#20242a',0);T.pix(x+15,y-34,'#c8ccd2',.2);T.pix(x+19,y-34,'#c8ccd2',.2);for(let q=0;q<4;q++)T.trait(x+21,y-58+q*3,x+31,y-58+q*3,.5)},
  frigo(T,x,y,r){T.box(x,y-50,24,50,6,2,2.5,'#c8ccd0');T.trait(x+1,y-34,x+23,y-34,.8);T.box(x+20,y-46,1.6,8,8,.8,.5,'#8a9098');T.box(x+20,y-30,1.6,12,8,.8,.5,'#8a9098');T.teinte(x+5,y-44,6,5,'#e06a8a');T.teinte(x+12,y-42,5,6,'#6ac0e0');T.teinte(x+6,y-28,9,7,'#f0f0e0')},
  canape(T,x,y,r){T.box(x,y-14,64,11,6,3,4,'#6a4a5a',1);T.box(x+2,y-30,60,18,5,3,5,'#7a566a',1);T.box(x-2,y-22,8,19,7,3,3,'#5e4050',1);T.box(x+58,y-22,8,19,7,3,3,'#5e4050',1);T.box(x+3,y-3,4,3,5,1,1,'#2a2420');T.box(x+57,y-3,4,3,5,1,1,'#2a2420');T.box(x+12,y-22,13,10,8,2.5,4,'#c8a860',1)},
  table(T,x,y,r){T.box(x,y-24,48,4,8,1.6,1.2,'#7a5c40');for(const px of[x+3,x+42])T.box(px,y-20,3,20,6,1.2,1,'#5a4430');T.box(x+8,y-27,7,3,9,1,1.2,'#e8e4d8');T.box(x+22,y-31,5,7,9,1.5,1.5,'#3a6a8a');T.box(x+33,y-27,8,3,9,1,1.2,'#e8e4d8')},
  chaise(T,x,y,r){T.box(x,y-14,14,3,7,1.2,1,'#6a5038');T.box(x,y-34,3,34,6,1.2,1,'#5a4430');T.box(x+11,y-11,3,11,6,1.2,1,'#5a4430');T.box(x+1,y-32,2,6,7,.8,.6,'#7a5c40')},
  biblio(T,x,y,r){T.box(x,y-74,46,74,5,2,2,'#5a4430');for(let q=0;q<4;q++){const sy=y-70+q*18;T.plat(x+3,sy,40,15,3,'#2a2018');for(let px=x+4;px<x+40;){const w=2.4+r()*3,h=9+r()*5;if(r()<.85)T.box(px,sy+15-h,w,h,3,2.4,.8,['#8a2a2a','#2a4a7a','#3a6a4a','#c8a040','#6a3a6a','#d8d0c0','#4a4a4a'][(r()*7)|0]);px+=w+.4}}},
  tele(T,x,y,r){T.box(x,y-20,46,20,6,2,1.5,'#4a3e30');T.box(x+4,y-50,38,28,8,1.5,1.5,'#1a1c20');T.plat(x+6,y-48,34,24,8,'#0a0c10');T.trait(x+10,y-46,x+30,y-30,.2);T.pix(x+38,y-23,'#ff3030',.9)},
  serveur(T,x,y,r){T.box(x,y-88,30,88,6,2,2,'#1e242c');for(let q=0;q<10;q++){const sy=y-84+q*8.4;T.box(x+3,sy,24,6.6,8,.8,.8,'#2c343e');for(let p=0;p<4;p++)T.trait(x+12+p*3.4,sy+1.4,x+12+p*3.4,sy+5,.4)}T.teinte(x+3,y-88,24,1.4,'#3FD6E6',.8)},
  rack(T,x,y,r){T.box(x,y-70,42,70,5,1.5,1.5,'#3a424c');for(let q=0;q<5;q++){T.plat(x+3,y-66+q*13.4,36,11,3,'#12161c');for(let p=0;p<7;p++)if(r()<.8)T.box(x+4+p*5,y-65+q*13.4,4,9.4,3,2.2,.8,['#c8c0a8','#b8b098','#8a8f98','#a09880'][(r()*4)|0])}},
  cellule(T,x,y,r){T.box(x-4,y-80,80,80,4,1.5,2,'#4a525c');T.plat(x,y-76,72,76,-2,'#161a20');for(let px=x+5;px<x+72;px+=9)cyl(T,px,y-76,3,76,5,2,'#8a929c');T.box(x-4,y-44,80,4,7,1.5,1.2,'#6a727c');T.box(x+60,y-52,10,16,8,2,2,'#3a424c');T.pix(x+65,y-44,'#E5283C',.9)},
  camera(T,x,y,r){T.box(x,y,4,10,5,1.4,1,'#3a424c');T.box(x-8,y+8,16,7,7,2.5,2,'#c8ccd2');T.ell(x-8,y+11.5,2.6,2.6,8,1.6,'#14181e');T.pix(x+5,y+10,'#E5283C',1)},
  banc(T,x,y,r){T.box(x,y-12,40,3,7,1.2,1,'#5a626c');for(const px of[x+3,x+34])T.box(px,y-9,3,9,6,1.2,1,'#3e444c')}};
// ---------------------------------------------------------------- thèmes de murs
const THEMES={
  usine:{amb:'#4c5a82',mur(T,Wp,Hp){T.box(0,0,Wp,Hp,0,0,1,'#644438');
     T.rel(0,0,Wp,Hp,(a,b,i,j)=>(j%7===0||(i+(((j/7)|0)&1?7:0))%14===0)?-.9:0);
     T.ton(0,0,Wp,Hp,(a,b,i,j)=>{const row=(j/7)|0,col=((i+(row&1?7:0))/14)|0,u=(((row*73856093)^(col*19349663))>>>0)%100;return(.74+u*.0052)*(.82+.24*Math.sin(a*.013+Math.sin(b*.021)*2)*Math.sin(b*.017+a*.004))*(u>94?.55:1)})},
    sol:'#7a7c84',int:'#33353d',lip:'#9a9ca4',plate:'#5a6470'},
  prison:{amb:'#66789a',mur(T,Wp,Hp){T.box(0,0,Wp,Hp,0,0,1,'#59626e');T.rel(0,0,Wp,Hp,(a,b,i,j)=>(j%48===0||i%72===0)?-1:((i%72===8||i%72===64)&&(j%48===8||j%48===40))?-1.2:0);
     T.ton(0,0,Wp,Hp,(a,b)=>.86+.14*Math.sin(a*.02+b*.013)*Math.sin(b*.031));for(let y=120;y<Hp;y+=192)T.teinte(0,y,Wp,2,'#3FD6E6',.75)},
    sol:'#6a727e',int:'#2c323a',lip:'#aab2bc',plate:'#56606c'},
  ruine:{amb:'#3a4466',mur(T,Wp,Hp){T.box(0,0,Wp,Hp,0,0,1,'#7a6a5c');
     T.ton(0,0,Wp,Hp,(a,b,i,j)=>{const m=((i%16<2)?.86:1)*(((i>>4)+(j>>4))%2?1:.95),fl=(Math.pow(Math.sin(i*.39)*Math.sin(j*.39),2)>.55)?.86:1;return m*fl*(.72+.3*Math.sin(a*.011+Math.sin(b*.019)*2.4)*Math.sin(b*.014))});
     T.rel(0,0,Wp,Hp,(a,b,i,j)=>Math.sin(a*.05)*Math.sin(b*.06)>.55?-1.2:0)},
    sol:'#6a625c',int:'#2e2a28',lip:'#8a8078',plate:'#6a5440'},
  archives:{amb:'#30405e',mur(T,Wp,Hp){T.box(0,0,Wp,Hp,0,0,1,'#2a323e');T.rel(0,0,Wp,Hp,(a,b,i,j)=>(i%48===0||j%96===0)?-1:(j%96>84&&i%6<3)?-.7:0);T.ton(0,0,Wp,Hp,(a,b)=>.86+.14*Math.sin(a*.017)*Math.sin(b*.023))},
    sol:'#4a5562',int:'#1c2028',lip:'#7a8794',plate:'#3e4854'}};
// ---------------------------------------------------------------- fabrication d'un niveau : N = {G, theme, fenetres, lampes, props, tags, peint(T), fond}
async function fabNiveau(N,etape){const G=N.G,Wp=G.c*TU,Hp=G.r*TU,Th=THEMES[N.theme];N.Wp=Wp;N.Hp=Hp;N.Th=Th;const r=hasard(N.graine||3);
  N.decor=await forgeBandes(Wp,Hp,T=>{
    Th.mur(T,Wp,Hp);
    if(N.piliers)for(let x=N.piliers;x<G.c;x+=N.piliers){T.box(x*TU-6,0,12,Hp,2.5,1.2,2,N.theme==='usine'?'#6a6a72':'#4a5460');for(let y=30;y<Hp;y+=60){T.pix(x*TU-3,y,'#3a3a40',0);T.pix(x*TU+3,y,'#3a3a40',0)}}
    for(const[fx,fy,fw,fh,st]of N.fenetres||[]){const px=fx*TU,py=fy*TU,pw=fw*TU,ph=fh*TU;T.box(px-5,py-5,pw+10,ph+10,3,1.6,2,'#3a3e46');T.vide(px,py,pw,ph);
      if(st!=='trou'){const rr=hasard(fx*31+fy*7);for(let i=0;i<pw;i+=12)for(let j=0;j<ph;j+=16){const u=rr();if(u<.5)T.plat(px+i,py+j,12,16,1,u<.2?'#4a5a6a':'#3a4856')}
        for(let i=12;i<pw;i+=12)T.box(px+i-1,py,2,ph,3,1,1,'#2e3238');for(let j=16;j<ph;j+=16)T.box(px,py+j-1,pw,2,3,1,1,'#2e3238')}
      T.box(px-7,py+ph+4,pw+14,4,4,1.4,1.4,'#55585f');T.ton(px,py+ph+8,pw,40,(a,b,i,j)=>.78+.22*Math.min(1,(j-(py+ph+8))/40)+(i%9<2?-.08:0))}
    if(N.peintFond)N.peintFond(T,r);
    for(const p of N.props||[])PROPS[p[0]](T,p[1]*TU+(p[3]||0),p[2]*TU,r);
    // tuiles pleines
    for(let y=0;y<G.r;y++)for(let x=0;x<G.c;x++){const ch=G.g[y][x],px=x*TU,py=y*TU;
      if(ch==='#'){const up=!plein(G.get(x,y-1))||G.get(x,y-1)==='c'||G.get(x,y-1)==='D',dn=!plein(G.get(x,y+1)),lf=!plein(G.get(x-1,y)),rt=!plein(G.get(x+1,y)),ins=!up&&!dn&&!lf&&!rt&&plein(G.get(x-1,y-1))&&plein(G.get(x+1,y-1))&&plein(G.get(x-1,y+1))&&plein(G.get(x+1,y+1));
        T.box(px,py,TU,TU,12,0,.01,ins?Th.int:Th.sol);
        if(!ins){T.ton(px,py,TU,TU,(a,b,i,j)=>.86+((((i>>1)*7+(j>>1)*13)%9))*.022+Math.sin(a*.07+b*.05)*.06);if(x%2===0)T.trait(px,py+(up?5:0),px,py+TU,.7)}
        if(up){T.box(px,py,TU,5,12,1.2,1.2,Th.lip);T.trait(px,py+5.5,px+TU,py+5.5,.8);if(((x*7+y*3)%5)===0)T.trait(px+6,py+7,px+10+((x*5)%8),py+17,.6)}
        if(dn)T.ton(px,py+TU-5,TU,5,()=>.7)}
      else if(ch==='='||ch==='~'){T.box(px,py,TU,6,13,1,1,ch==='~'?'#6a5a48':Th.plate);T.rel(px,py+1,TU,4,(a,b,i)=>i%4<2?-.8:0);if(ch==='='&&x%3===1){let y2=y-1;while(y2>y-12&&y2>=0&&!plein(G.get(x,y2)))y2--;if(y-y2<12&&y2>=0)T.box(px+11,(y2+1)*TU,2,(y-y2-1)*TU,5,1,1,'#3e444c')}}
      else if(ch==='c'){PROPS.caisse(T,px+1,py+TU,()=>.4);}}
    for(const[lx,ly,c]of N.lampes||[]){const px=lx*TU+12,py=ly*TU;T.box(px-.8,py,1.6,14,4,.8,.6,'#20242a');T.poly([[px-8,py+20],[px-3,py+13],[px+3,py+13],[px+8,py+20]],5,2,2,'#3a4a44');T.teinte(px-5,py+19.4,10,1.6,c||'#ffe9b0',1);T.lueur(px,py+24,74,c||'#ffcf80',.55)}
    if(N.peint)N.peint(T,r);
  },{mur:1,pas:16,gain:.95,grain:.1,omb:12,ombre:.55},etape,'Relevé des lieux…');
  for(const t of N.tags||[])tag(N.decor,...t);
  N.fondLoin=fondLoin(N.fond||'nuit')}
// inscription à la bombe sur le décor déjà rendu
function tag(D,txt,x,y,px,col,rot,al){const w=txt.length*px*.75+20,h=px*1.8,t=toile(R(w),R(h)),g=t.getContext('2d');g.font='bold '+px+'px Impact,"Arial Narrow",sans-serif';g.textBaseline='middle';g.translate(8,h/2);g.rotate(rot||0);g.fillStyle=col;g.fillText(txt,0,0);g.setTransform(1,0,0,1,0,0);
  const d=g.getImageData(0,0,t.width,t.height),p=d.data,rr=hasard(txt.length*7+px);for(let i=3;i<p.length;i+=4)p[i]=p[i]>120&&rr()>.08?255:0;g.putImageData(d,0,0);
  for(let i=0;i<txt.length*.8;i++){g.fillStyle=col;const xx=10+rr()*(w-24);g.fillRect(xx|0,h/2,1,(px*.3+rr()*px*.5)|0)}
  for(let i=0;i<D.bandes.length;i++){const bx=i*D.larg;if(x+w<bx||x>bx+D.larg)continue;const q=D.bandes[i].getContext('2d');q.globalAlpha=al||.82;q.drawImage(t,R(x-bx),R(y));q.globalAlpha=1}}
// arrière-plans lointains (visibles par les fenêtres et les brèches)
function fondLoin(k){const w=W+240,c=toile(w,H),g=c.getContext('2d'),r=hasard(k.length*13+5);const gr=g.createLinearGradient(0,0,0,H);
  if(k==='feu'){gr.addColorStop(0,'#0c0e18');gr.addColorStop(.6,'#2a1820');gr.addColorStop(1,'#6a2a18')}else{gr.addColorStop(0,'#070b16');gr.addColorStop(.7,'#16223c');gr.addColorStop(1,'#243250')}
  g.fillStyle=gr;g.fillRect(0,0,w,H);for(let i=0;i<150;i++){g.fillStyle='rgba(220,230,255,'+(.2+r()*.7)+')';g.fillRect((r()*w)|0,(r()*H*.7)|0,1,1)}
  if(k!=='feu'){const mx=w*.72,my=H*.2,m=g.createRadialGradient(mx,my,0,mx,my,90);m.addColorStop(0,'rgba(200,215,255,.5)');m.addColorStop(.16,'rgba(200,215,255,.22)');m.addColorStop(1,'rgba(200,215,255,0)');g.fillStyle=m;g.fillRect(mx-90,my-90,180,180);g.fillStyle='#e8eef8';g.beginPath();g.arc(mx,my,13,0,7);g.fill();g.fillStyle='#c4cee0';g.beginPath();g.arc(mx-4,my-3,3,0,7);g.arc(mx+5,my+4,2,0,7);g.fill()}
  for(let l=0;l<3;l++){const base=H*(.5+l*.13),col=['#121a2e','#0e1424','#090d18'][l];let x=0;while(x<w){const bw=14+r()*38,bh=30+r()*(120-l*20)+(r()<.08?90:0);g.fillStyle=col;g.fillRect(x|0,(base-bh)|0,bw|0,H);
      if(r()<.3){g.fillRect((x+bw*.3)|0,(base-bh-8)|0,3,8)}for(let q=0;q<bw*bh/90;q++)if(r()<.35){g.fillStyle=k==='feu'?(r()<.3?'#ff9a40':'#3a2a2a'):(r()<.8?'#ffd98a':'#bfe6ff');g.globalAlpha=.25+r()*.5;g.fillRect((x+2+r()*(bw-4))|0,(base-bh+3+r()*(bh-6))|0,1,2);g.globalAlpha=1}x+=bw+r()*4}}
  if(k==='nuit'){const ex=w*.3,ey=H*.5;g.fillStyle='#1c2640';g.beginPath();g.moveTo(ex-16,ey+70);g.quadraticCurveTo(ex-3,ey+20,ex-1.5,ey-50);g.lineTo(ex+1.5,ey-50);g.quadraticCurveTo(ex+3,ey+20,ex+16,ey+70);g.fill();g.fillStyle='#ffd98a';for(let q=0;q<9;q++)g.fillRect(ex|0,(ey-46+q*13)|0,1,1);g.fillStyle='#fff';g.fillRect((ex-1)|0,(ey-52)|0,2,2)}
  if(k==='feu'){for(let i=0;i<7;i++){const fx=r()*w,fy=H*(.55+r()*.25),f=g.createRadialGradient(fx,fy,0,fx,fy,50+r()*50);f.addColorStop(0,'rgba(255,150,50,.55)');f.addColorStop(1,'rgba(255,90,20,0)');g.fillStyle=f;g.fillRect(fx-100,fy-100,200,200)}}
  return c}
// ---------------------------------------------------------------- éclairage : calque sombre troué par les lampes
const LUM={c:null,g:null,rond:{}};
function lumRond(col,ray){const k=col+ray;if(!LUM.rond[k]){const t=toile(ray*2,ray*2),g=t.getContext('2d'),gr=g.createRadialGradient(ray,ray,0,ray,ray,ray),u=hx(col).map(v=>R(v*255));gr.addColorStop(0,'rgba('+u+',1)');gr.addColorStop(.5,'rgba('+u+',.42)');gr.addColorStop(1,'rgba('+u+',0)');g.fillStyle=gr;g.fillRect(0,0,ray*2,ray*2);LUM.rond[k]=t}return LUM.rond[k]}
function lumDebut(amb){const w=W>>1,h=(H>>1)+1;if(!LUM.c||LUM.c.height!==h){LUM.c=toile(w,h);LUM.g=LUM.c.getContext('2d')}const g=LUM.g;g.globalCompositeOperation='source-over';g.fillStyle=amb;g.fillRect(0,0,w,h);g.globalCompositeOperation='lighter'}
function lumPoint(x,y,ray,col,a){const s=lumRond(col||'#ffdca0',ray>>1);LUM.g.globalAlpha=a===undefined?1:a;LUM.g.drawImage(s,R(x/2-s.width/2),R(y/2-s.height/2))}
function lumFin(){LUM.g.globalAlpha=1;cx.globalCompositeOperation='multiply';cx.imageSmoothingEnabled=false;cx.drawImage(LUM.c,0,0,W,LUM.c.height*2);cx.globalCompositeOperation='source-over'}
// ---------------------------------------------------------------- personnage joueur et physique
const JL=7,JH=42; // demi-largeur, hauteur de la boîte
function joueurNouveau(x,y){return{x,y,vx:0,vy:0,sol:false,dir:1,an:'repos',af:0,inv:0,coy:0,tamp:0,vit:150}}
function solide(N,px,py){return plein(N.G.get(Math.floor(px/TU),Math.floor(py/TU)))}
function majJoueur(N,j,dt,cmd){
  const cible=cmd.dx*j.vit;j.vx+=(cible-j.vx)*Math.min(1,dt*(j.sol?14:7));if(cmd.dx)j.dir=cmd.dx;
  j.coy=j.sol?.1:Math.max(0,j.coy-dt);j.tamp=cmd.saut?.14:Math.max(0,j.tamp-dt);
  if(j.tamp>0&&j.coy>0&&!N.sansSaut){j.vy=-520;j.sol=false;j.coy=0;j.tamp=0;sfx.saut()}
  j.vy=Math.min(760,j.vy+1500*dt);
  // horizontal
  let nx=j.x+j.vx*dt;const cote=j.vx>0?JL:-JL;if(j.vx!==0){let bloc=false;for(const oy of[-2,-JH/2,-JH+2])if(solide(N,nx+cote,j.y+oy))bloc=true;if(bloc){nx=j.vx>0?Math.floor((nx+cote)/TU)*TU-JL-.01:Math.floor((nx+cote)/TU)*TU+TU+JL+.01;j.vx=0}}j.x=lim(nx,JL,N.Wp-JL);
  // vertical
  let ny=j.y+j.vy*dt;const etait=j.sol;j.sol=false;
  if(j.vy>=0){for(const ox of[-JL+1,JL-1]){const tx=Math.floor((j.x+ox)/TU),ty=Math.floor(ny/TU),ch=N.G.get(tx,ty);
      if(plein(ch)||((ch==='='||ch==='~')&&j.y<=ty*TU+2&&!cmd.bas)){ny=ty*TU;j.sol=true;if(ch==='~'&&N.friable)N.friable(tx,ty)}}
    if(j.sol){if(!etait&&j.vy>300){sfx.chute();if(S.pouss)for(let i=0;i<5;i++)S.pouss.push({x:j.x+(rnd()-.5)*14,y:ny,vx:(rnd()-.5)*40,vy:-rnd()*30,l:.4,c:'#8a8a90'})}j.vy=0}}
  else{for(const ox of[-JL+1,JL-1])if(solide(N,j.x+ox,ny-JH)){ny=Math.floor((ny-JH)/TU)*TU+TU+JH+.01;j.vy=0}}
  j.y=ny;j.inv=Math.max(0,j.inv-dt);
  // animation
  const an=!j.sol?(j.vy<0?'saut':'chute'):Math.abs(j.vx)>90?'course':Math.abs(j.vx)>12?'marche':'repos';if(an!==j.an){j.an=an;j.af=0}
  const av=j.af;j.af+=dt*(an==='course'?Math.abs(j.vx)/11:an==='marche'?Math.abs(j.vx)/7:3);if(j.sol&&(an==='course'||an==='marche')&&(Math.floor(av/4)!==Math.floor(j.af/4)))sfx.pas()}
function imageJoueur(A,j){const f=A[j.an];return f[Math.floor(j.af)%f.length]}
// commande au pouce : manche flottant (gauche/droite), coup vers le haut = saut ; clavier : flèches, espace
const CMD={dx:0,saut:false,bas:false,ax:0,ay:0,arm:true,ymin:0};
function cmdBas(x,y){CMD.ax=x;CMD.ay=y;CMD.arm=true;CMD.ymin=y;CMD.dx=0}
function cmdBouge(x,y){const dx=x-CMD.ax;CMD.dx=dx>7?1:dx<-7?-1:0;if(Math.abs(dx)>34)CMD.ax=x-Math.sign(dx)*34;
  if(y>CMD.ymin)CMD.ymin=y;if(CMD.arm&&CMD.ymin-y>16){CMD.saut=true;CMD.arm=false;CMD.ymin=y}if(!CMD.arm){if(y<CMD.ymin-0)CMD.ymin=Math.min(CMD.ymin,y);if(y>CMD.ymin+9){CMD.arm=true;CMD.ymin=y}}CMD.bas=y-CMD.ay>30}
function cmdHaut(){CMD.dx=0;CMD.bas=false}
function cmdLire(){const c={dx:CMD.dx,saut:CMD.saut,bas:CMD.bas};CMD.saut=false;if(!P.bas){c.dx=(KB.ArrowRight||KB.d?1:0)-(KB.ArrowLeft||KB.q||KB.a?1:0);c.bas=!!KB.ArrowDown}if(KB[' ']||KB.ArrowUp||KB.z||KB.w){if(!CMD.kj){c.saut=true;CMD.kj=1}}else CMD.kj=0;return c}
// caméra
function camSuit(N,cam,j,dt,brut){const tx=lim(j.x-W/2+j.dir*36,0,Math.max(0,N.Wp-W)),ty=lim(j.y-H*.6,0,Math.max(0,N.Hp-H));if(brut){cam.x=tx;cam.y=ty}else{cam.x+=(tx-cam.x)*Math.min(1,dt*4);cam.y+=(ty-cam.y)*Math.min(1,dt*5)}}
// poussières en suspension, gouttes
function ambianceNouv(n){const a=[];for(let i=0;i<n;i++)a.push({x:rnd()*W,y:rnd()*H,vx:(rnd()-.5)*8,vy:2+rnd()*7,p:rnd()*TAU});return a}
function ambianceDessine(a,t,dt,col){cx.fillStyle=col||'rgba(220,225,240,.35)';for(const p of a){p.x+=p.vx*dt+Math.sin(t+p.p)*.1;p.y+=p.vy*dt;if(p.y>H){p.y=0;p.x=rnd()*W}if(Math.sin(t*1.7+p.p)>-.2)cx.fillRect(R(p.x),R(p.y),1,1)}}
function pluie(t,f){cx.strokeStyle='rgba(170,190,230,.3)';cx.lineWidth=1;cx.beginPath();for(let i=0;i<(f||70);i++){const x=((i*97+t*340)%(W+80))-40,y=((i*57+t*(820+(i%7)*40))%(H+40))-20;cx.moveTo(x,y);cx.lineTo(x-4,y+13)}cx.stroke()}
