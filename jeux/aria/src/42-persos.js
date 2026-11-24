// ================================================================ PERSONNAGES : squelette articulé, rendu en relief image par image (vue de côté, regard à droite)
const PW=44,PH=58,PIED=55;
// pose : t torse, b1/b2 bras avant/arrière [épaule, coude], j1/j2 jambes [hanche, genou], dy, tete (inclinaison)
function poseP(P,p,opt){opt=opt||{};return forge(PW,PH,T=>{
  const hxp=22+(p.dx||0),hyp=PIED-19.5+(p.dy||0),t=p.t||0,ex=hxp+Math.sin(t)*14.5,ey=hyp-Math.cos(t)*14.5,tx=ex+Math.sin(t+(p.tete||0))*6.4,ty=ey-Math.cos(t+(p.tete||0))*6.4;
  const som=c=>{const u=hx(c);return '#'+u.map(v=>R(v*255*.66).toString(16).padStart(2,'0')).join('')};
  const jambe=(a,z,dos)=>{const kx=hxp+Math.sin(a[0])*9.5,ky=hyp+Math.cos(a[0])*9.5,ax=kx+Math.sin(a[0]-a[1])*9.5,ay=ky+Math.cos(a[0]-a[1])*9.5,cb=dos?som(P.bas):P.bas;
    T.cap(hxp,hyp,kx,ky,3.7,3.1,z,2.4,cb);T.cap(kx,ky,ax,ay,3,2.4,z,2.2,cb);const fa=a[0]-a[1]+1.35;T.cap(ax,ay,ax+Math.sin(fa)*4.2,ay+Math.cos(fa)*4.2+.2,2.3,1.9,z+.2,2,dos?som(P.pied):P.pied);if(P.genou&&!dos)T.ell(kx+.6,ky,2,2.2,z+1.6,1.4,P.genou)};
  const bras=(a,z,dos)=>{const cx0=ex+Math.sin(a[0])*7.6,cy0=ey+1+Math.cos(a[0])*7.6,mx=cx0+Math.sin(a[0]+a[1])*7.2,my=cy0+Math.cos(a[0]+a[1])*7.2,ch=dos?som(P.haut):P.haut;
    T.cap(ex,ey+1,cx0,cy0,2.9,2.5,z,2.2,ch);T.cap(cx0,cy0,mx,my,2.4,2.1,z,2,P.manche?ch:(dos?som(P.peau):P.peau));T.ell(mx,my,2.3,2.3,z+.3,2,P.gant||(dos?som(P.peau):P.peau));
    if(opt.arme&&!dos){T.cap(mx,my,mx+Math.sin(a[0]+a[1]-1.4)*9,my+Math.cos(a[0]+a[1]-1.4)*9,1.1,1.1,z+1,1.4,'#8a929c')}};
  jambe(p.j2,0,1);bras(p.b2,1,1);
  // torse
  T.cap(hxp,hyp,ex,ey,4.8,5.4,3,3.4,P.haut);if(P.gilet){T.cap(hxp+Math.sin(t)*3,hyp-Math.cos(t)*3,ex-Math.sin(t)*1,ey+Math.cos(t)*1,5,5.6,3.6,3.2,P.gilet)}
  if(P.ceinture)T.cap(hxp-1,hyp-.6,hxp+1,hyp-.6,4.9,4.9,3.4,3.3,P.ceinture);
  if(P.sac)T.cap(ex-5.5,ey+3,hxp-5.5,hyp-5,3.4,3.6,2.6,3,P.sac);
  if(P.bande)T.cap(hxp+2,hyp-5,ex+3,ey+3,1.2,1.2,6.2,.8,P.bande);
  // tête
  T.cap(ex,ey,tx,ty+2,2.4,2.4,3.4,2.4,P.cou||P.peau);
  if(P.tete==='casque'){T.ell(tx,ty,5.4,5.6,4,4.6,P.casque);T.teinte(tx+.5,ty-1.6,5.2,2.6,P.visiere||'#3FD6E6',.9);T.pix(tx+4.2,ty-1,'#eaffff');T.trait(tx-5,ty+2.6,tx+5,ty+2.6,.6);T.box(tx-6.2,ty-1,2,4,5,1.6,.8,som(P.casque))}
  else{T.ell(tx,ty,4.9,5.3,4,4.4,P.peau);
    if(P.tete==='capuche'){T.ell(tx-1.2,ty-.6,5.6,6,4.6,4.4,P.haut);T.teinte(tx+1.4,ty-2,3.6,5,P.peau);T.rel(tx+1,ty-3,5,7,()=>-.6)}
    else if(P.tete==='chauve'){}
    else{const c=P.cheveux||'#2a2420';T.teinte(tx-5,ty-5.6,10,P.tete==='long'?5.4:3.9,c);T.teinte(tx-5.2,ty-2,P.tete==='long'?4.2:3,P.tete==='long'?8.6:3.8,c);if(P.tete==='bonnet'){T.teinte(tx-5.2,ty-5.8,10.6,4.2,P.bonnet||'#8a2a2a')}}
    T.pix(tx+2.9,ty-.6,'#101418',0);if(P.barbe){T.teinte(tx-.4,ty+1.6,5,3.4,P.barbe)}if(P.lunettes){T.teinte(tx+1.2,ty-1.5,3.6,.8,'#101418');T.pix(tx+3,ty-1,'#bfe6ff',.6)}}
  jambe(p.j1,5,0);bras(p.b1,7,0);
  if(P.brassard)T.cap(ex+Math.sin(p.b1[0])*3,ey+1+Math.cos(p.b1[0])*3,ex+Math.sin(p.b1[0])*5,ey+1+Math.cos(p.b1[0])*5,3,3,8.4,1.4,P.brassard,.5);
  if(P.badge){T.pix(ex+2.2,ey+5,P.badge);T.pix(ex+3.2,ey+5,P.badge)}
},{pas:10,poli:14,gain:opt.gain||1})}
const POSES={
  repos:i=>({t:.03,dy:[0,.4,.9,.4][i%4],b1:[.12,.25],b2:[-.12,.2],j1:[.1,.06],j2:[-.14,.04]}),
  marche:i=>{const f=i/8*TAU,s=Math.sin(f),c=Math.cos(f);return{t:.06,dy:-Math.abs(s)*.8,b1:[-.45*s,.35],b2:[.45*s,.3],j1:[.42*s,.1+.5*Math.max(0,c)],j2:[-.42*s,.1+.5*Math.max(0,-c)]}},
  course:i=>{const f=i/8*TAU,s=Math.sin(f),c=Math.cos(f);return{t:.2,dy:-Math.abs(s)*1.8,b1:[-.95*s,1.2],b2:[.95*s,1.2],j1:[.85*s+.1,.25+1.1*Math.max(0,c)],j2:[-.85*s+.1,.25+1.1*Math.max(0,-c)]}},
  saut:()=>({t:.1,dy:-1,b1:[-2.2,.5],b2:[-1.6,.6],j1:[.9,1.3],j2:[-.2,.9]}),
  chute:()=>({t:.05,b1:[-2.5,.3],b2:[2.2,-.3],j1:[.35,.3],j2:[-.4,.5]}),
  garde:i=>({t:.14,dy:[0,.5][i%2],b1:[.9,1.9],b2:[.5,2.1],j1:[.4,.35],j2:[-.45,.3]}),
  poing1:()=>({t:.3,dx:2,b1:[1.55,.05],b2:[.2,2.2],j1:[.55,.3],j2:[-.6,.2]}),
  poing2:()=>({t:.36,dx:3,b1:[.3,2.2],b2:[1.6,.05],j1:[.6,.4],j2:[-.65,.15]}),
  pied:()=>({t:-.32,dx:-1,b1:[-.5,1.2],b2:[.9,1.4],j1:[1.5,.12],j2:[-.2,.25]}),
  elan:()=>({t:.5,dx:4,dy:1,b1:[1.5,.2],b2:[1.3,.3],j1:[.9,.9],j2:[-.9,.1]}),
  touche:()=>({t:-.34,dx:-2,tete:-.3,b1:[-.9,.6],b2:[-1.6,.4],j1:[.3,.4],j2:[-.2,.5]}),
  sol:()=>({t:-1.45,dx:-8,dy:14,tete:-.1,b1:[-1.9,.3],b2:[-1.2,.2],j1:[1.4,.3],j2:[1.15,.4]}),
  mains:()=>({t:-.04,b1:[-2.6,-.5],b2:[-2.8,-.4],j1:[.12,.05],j2:[-.12,.05]}),
  assis:()=>({t:.12,dy:9,tete:.25,b1:[.5,1.2],b2:[.4,1.3],j1:[1.5,1.6],j2:[1.35,1.5]}),
  lit:()=>({t:.35,dy:1,tete:.4,b1:[.9,.9],b2:[.8,1],j1:[.1,.05],j2:[-.1,.05]})};
const NFR={repos:4,marche:8,course:8,garde:2};
function fabPerso(P,liste,opt){const A={};for(const k of liste||Object.keys(POSES)){const n=NFR[k]||1;A[k]=[];for(let i=0;i<n;i++){const c=poseP(P,POSES[k](i),opt);c.g=miroir(c);c.g.blanc=miroir(c.blanc);A[k].push(c)}}return A}
// dessin : pieds posés en (x,y) pixels réels ; dir -1 = regard à gauche
function poseSprite(c,x,y,dir,blanc){let s=dir<0?c.g:c;if(blanc)s=s.blanc;cx.drawImage(s,R(x-PW/2),R(y-PIED))}
const TENUES={
  operateur:{peau:'#2c3440',haut:'#3a4656',bas:'#2a323e',pied:'#14181e',tete:'casque',casque:'#4a5666',visiere:'#3FD6E6',gilet:'#56657a',genou:'#56657a',gant:'#1a2028',manche:1,ceinture:'#1a2028',brassard:'#3FD6E6'},
  civil1:{peau:'#d8a888',haut:'#7a3a3a',bas:'#2e3a5a',pied:'#e8e8e8',tete:'capuche',manche:1},
  civil2:{peau:'#8a5a40',haut:'#c8b048',bas:'#30343c',pied:'#5a4030',tete:'court',cheveux:'#18120e',manche:1,sac:'#3a4a3a'},
  civil3:{peau:'#e0b89a',haut:'#3a5a48',bas:'#4a3a2a',pied:'#20242a',tete:'long',cheveux:'#7a3a20',manche:1,bande:'#c8c8c8'},
  civil4:{peau:'#c89878',haut:'#40444e',bas:'#40444e',pied:'#d05030',tete:'bonnet',bonnet:'#c05030',cheveux:'#2a2420',manche:1},
  civil5:{peau:'#e8c8a8',haut:'#d8d8e0',bas:'#5a6a8a',pied:'#30343c',tete:'court',cheveux:'#c8c0b0',manche:0,lunettes:1},
  meneur:{peau:'#b88868',haut:'#20242a',bas:'#3a3020',pied:'#14181e',tete:'court',cheveux:'#101010',manche:1,barbe:'#201a16',brassard:'#E5283C',gilet:'#3a3e46'},
  haddad:{peau:'#b08460',haut:'#c8641e',bas:'#c8641e',pied:'#9a9a9a',tete:'court',cheveux:'#8a8a8a',manche:1,barbe:'#9a9a9a',lunettes:1,badge:'#ffffff'},
  garde:{peau:'#2c3440',haut:'#20262e',bas:'#20262e',pied:'#101418',tete:'casque',casque:'#2a3038',visiere:'#E5283C',gilet:'#3a424c',manche:1,gant:'#101418',ceinture:'#101418'}};
