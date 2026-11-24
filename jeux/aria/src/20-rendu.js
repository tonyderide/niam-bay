// ================================================================ RENDU : petites maquettes en relief éclairées par le code, puis réduites en palette
const Rc=(g,c,x,y,w,h)=>{g.fillStyle=c;g.fillRect(x,y,w,h)};
const hx=s=>[parseInt(s.slice(1,3),16)/255,parseInt(s.slice(3,5),16)/255,parseInt(s.slice(5,7),16)/255];
const toile=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c};
const BAY=[0,.5,.75,.25],V8=[[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,1],[1,-1],[-1,-1]];
const hasard=s=>()=>(s=(s*1664525+1013904223)>>>0)/4294967296;
// forge(w,h,f,o) : f dessine avec des primitives à hauteur ; o.k = finesse (les coordonnées sont multipliées), o.sym = miroir gauche/droite,
// o.sol = décor vu de dessus (ombres portées), o.mur = décor vu de face (ombres portées courtes), o.pas = nombre de teintes, o.grain = bruit de matière
function forge(w0,h0,f,o){o=o||{};const k=o.k||1,w=R(w0*k),h=R(h0*k),n=w*h,Hh=new Float32Array(n),C=new Float32Array(n*3),Em=new Float32Array(n),Aa=new Uint8Array(n),G=new Uint8Array(n);
  const put=(x,y,z,c,e)=>{if(x<0||y<0||x>=w||y>=h)return;const i=y*w+x;if(Aa[i]&&z<=Hh[i])return;Hh[i]=z;C[i*3]=c[0];C[i*3+1]=c[1];C[i*3+2]=c[2];Em[i]=e||0;Aa[i]=1};
  const pf=(t,r)=>r?Math.sqrt(1-(1-t)*(1-t)):t;
  const T={w:w0,h:h0,
    box(x,y,bw,bh,z0,dz,bev,col,r,e){x*=k;y*=k;bw*=k;bh*=k;z0*=k;dz*=k;bev=Math.max(.01,bev*k);const c=hx(col);for(let j=Math.max(0,Math.floor(y));j<Math.min(h,y+bh);j++)for(let i=Math.max(0,Math.floor(x));i<Math.min(w,x+bw);i++){const px=i+.5,py=j+.5,d=Math.min(px-x,x+bw-px,py-y,y+bh-py);if(d<0)continue;put(i,j,z0+dz*pf(Math.min(1,d/bev),r),c,e)}},
    ell(ex,ey,rx,ry,z0,dz,col,e){ex*=k;ey*=k;rx*=k;ry*=k;z0*=k;dz*=k;const c=hx(col);for(let j=Math.floor(ey-ry);j<=ey+ry;j++)for(let i=Math.floor(ex-rx);i<=ex+rx;i++){const a=(i+.5-ex)/rx,b=(j+.5-ey)/ry,q=a*a+b*b;if(q<1)put(i,j,z0+dz*Math.sqrt(1-q),c,e)}},
    cap(x1,y1,x2,y2,r1,r2,z0,dz,col,e){x1*=k;y1*=k;x2*=k;y2*=k;r1*=k;r2*=k;z0*=k;dz*=k;const c=hx(col),m=Math.max(r1,r2),ux=x2-x1,uy=y2-y1,l2=ux*ux+uy*uy||1;
      for(let j=Math.floor(Math.min(y1,y2)-m);j<=Math.max(y1,y2)+m;j++)for(let i=Math.floor(Math.min(x1,x2)-m);i<=Math.max(x1,x2)+m;i++){const px=i+.5,py=j+.5,t=lim(((px-x1)*ux+(py-y1)*uy)/l2,0,1),rr=r1+(r2-r1)*t,d=Math.hypot(px-x1-ux*t,py-y1-uy*t)/rr;if(d<1)put(i,j,z0+dz*Math.sqrt(1-d*d),c,e)}},
    poly(p0,z0,dz,bev,col,r,e){const p=p0.map(q=>[q[0]*k,q[1]*k]);z0*=k;dz*=k;bev=Math.max(.01,bev*k);const c=hx(col);let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;for(const[a,b]of p){x0=Math.min(x0,a);x1=Math.max(x1,a);y0=Math.min(y0,b);y1=Math.max(y1,b)}
      for(let j=Math.floor(y0);j<y1;j++)for(let i=Math.floor(x0);i<x1;i++){const px=i+.5,py=j+.5;let ins=false,d=1e9;
        for(let q=0,m=p.length-1;q<p.length;m=q++){const ax=p[q][0],ay=p[q][1],bx=p[m][0],by=p[m][1];
          if((ay>py)!==(by>py)&&px<(bx-ax)*(py-ay)/(by-ay)+ax)ins=!ins;
          if(o.sym&&p0[q][0]===w0/2&&p0[m][0]===w0/2)continue;
          const ux=bx-ax,uy=by-ay,t=lim(((px-ax)*ux+(py-ay)*uy)/(ux*ux+uy*uy||1),0,1),ex=px-ax-ux*t,ey=py-ay-uy*t;d=Math.min(d,ex*ex+ey*ey)}
        if(ins)put(i,j,z0+dz*pf(Math.min(1,Math.sqrt(d)/bev),r),c,e)}},
    trait(x1,y1,x2,y2,p){x1*=k;y1*=k;x2*=k;y2*=k;const m=Math.ceil(Math.hypot(x2-x1,y2-y1)*2)||1;for(let q=0;q<=m;q++){const x=Math.floor(x1+(x2-x1)*q/m),y=Math.floor(y1+(y2-y1)*q/m);if(x<0||y<0||x>=w||y>=h)continue;const i=y*w+x;if(Aa[i]&&!Em[i]&&!G[i]){G[i]=1;Hh[i]-=p||1.3;C[i*3]*=.6;C[i*3+1]*=.6;C[i*3+2]*=.6}}},
    teinte(x,y,tw,th,col,e){const c=hx(col),xa=R(x*k),ya=R(y*k),xb=Math.max(xa+1,R((x+tw)*k)),yb=Math.max(ya+1,R((y+th)*k));for(let j=Math.max(0,ya);j<Math.min(h,yb);j++)for(let i=Math.max(0,xa);i<Math.min(w,xb);i++){if(i<0||j<0||i>=w||j>=h)continue;const q=j*w+i;if(Aa[q]){C[q*3]=c[0];C[q*3+1]=c[1];C[q*3+2]=c[2];Em[q]=e||0}}},
    // pix : un seul pixel réel (détail fin), coordonnées logiques
    pix(x,y,col,e){const c=hx(col),i=Math.floor(x*k),j=Math.floor(y*k);if(i<0||j<0||i>=w||j>=h)return;const q=j*w+i;if(Aa[q]){C[q*3]=c[0];C[q*3+1]=c[1];C[q*3+2]=c[2];Em[q]=e===undefined?1:e}},
    trou(ex,ey,rx,ry,z,col){ex*=k;ey*=k;rx*=k;ry*=k;z*=k;const c=hx(col);for(let j=Math.floor(ey-ry);j<=ey+ry;j++)for(let i=Math.floor(ex-rx);i<=ex+rx;i++){const a=(i+.5-ex)/rx,b=(j+.5-ey)/ry;if(a*a+b*b<1&&i>=0&&j>=0&&i<w&&j<h){const q=j*w+i;Hh[q]=z;C[q*3]=c[0];C[q*3+1]=c[1];C[q*3+2]=c[2];Em[q]=0;Aa[q]=1}}},
    // plat : force une zone (rectangle ou ruban) au niveau z avec une couleur : routes, eau, cours
    plat(x,y,pw,ph,z,col,e){const c=hx(col),xa=Math.max(0,R(x*k)),ya=Math.max(0,R(y*k)),xb=Math.min(w,R((x+pw)*k)),yb=Math.min(h,R((y+ph)*k));for(let j=ya;j<yb;j++)for(let i=xa;i<xb;i++){if(i<0||j<0||i>=w||j>=h)continue;const q=j*w+i;Hh[q]=z*k;C[q*3]=c[0];C[q*3+1]=c[1];C[q*3+2]=c[2];Em[q]=e||0;Aa[q]=1;G[q]=0}},
    ruban(x1,y1,x2,y2,l,z,col){x1*=k;y1*=k;x2*=k;y2*=k;l*=k/2;const c=hx(col),ux=x2-x1,uy=y2-y1,l2=ux*ux+uy*uy||1;for(let j=Math.floor(Math.min(y1,y2)-l);j<=Math.max(y1,y2)+l;j++)for(let i=Math.floor(Math.min(x1,x2)-l);i<=Math.max(x1,x2)+l;i++){if(i<0||j<0||i>=w||j>=h)continue;const px=i+.5,py=j+.5,t=lim(((px-x1)*ux+(py-y1)*uy)/l2,0,1);if(Math.hypot(px-x1-ux*t,py-y1-uy*t)<l){const q=j*w+i;Hh[q]=z*k;C[q*3]=c[0];C[q*3+1]=c[1];C[q*3+2]=c[2];Em[q]=0;Aa[q]=1;G[q]=0}}},
    // rel : ajoute un relief fonction de la position (tuiles, tôle ondulée, vagues) ; fn(x,y) en unités logiques
    rel(x,y,rw,rh,fn){const xa=Math.max(0,R(x*k)),ya=Math.max(0,R(y*k)),xb=Math.min(w,R((x+rw)*k)),yb=Math.min(h,R((y+rh)*k));for(let j=ya;j<yb;j++)for(let i=xa;i<xb;i++){if(i<0||j<0||i>=w||j>=h)continue;const q=j*w+i;if(Aa[q]&&!Em[q])Hh[q]+=fn(i/k,j/k,i,j)*k}},
    // ton : multiplie la couleur (salissures, usure) ; fn renvoie un facteur
    ton(x,y,rw,rh,fn){const xa=Math.max(0,R(x*k)),ya=Math.max(0,R(y*k)),xb=Math.min(w,R((x+rw)*k)),yb=Math.min(h,R((y+rh)*k));for(let j=ya;j<yb;j++)for(let i=xa;i<xb;i++){if(i<0||j<0||i>=w||j>=h)continue;const q=j*w+i;if(Aa[q]&&Em[q]<1){const m=fn(i/k,j/k,i,j);C[q*3]*=m;C[q*3+1]*=m;C[q*3+2]*=m}}},
    // lueur : flaque de lumière chaude ou froide sur ce qui existe déjà (réverbères, fenêtres, néons)
    lueur(ex,ey,r,col,f){const c=hx(col);ex*=k;ey*=k;r*=k;for(let j=Math.floor(ey-r);j<=ey+r;j++)for(let i=Math.floor(ex-r);i<=ex+r;i++){if(i<0||j<0||i>=w||j>=h)continue;const d=Math.hypot(i+.5-ex,j+.5-ey)/r;if(d>=1)continue;const q=j*w+i;if(!Aa[q]||Em[q]>=.99)continue;const a=(1-d)*(1-d)*(f||.6);C[q*3]+=(c[0]-C[q*3])*a*.7;C[q*3+1]+=(c[1]-C[q*3+1])*a*.7;C[q*3+2]+=(c[2]-C[q*3+2])*a*.7;Em[q]=Math.max(Em[q],a*.75)}},
    lum(x,y,col){T.teinte(x,y,1,1,col,1)},
    vide(x,y,vw,vh){const xa=Math.max(0,R(x*k)),ya=Math.max(0,R(y*k)),xb=Math.min(w,R((x+vw)*k)),yb=Math.min(h,R((y+vh)*k));for(let j=ya;j<yb;j++)for(let i=xa;i<xb;i++){const q=j*w+i;Aa[q]=0;Hh[q]=-6*k;Em[q]=0}},
    haut(x,y){const i=Math.floor(x*k),j=Math.floor(y*k);return i<0||j<0||i>=w||j>=h||!Aa[j*w+i]?-1:Hh[j*w+i]/k}};
  f(T);
  if(o.sym)for(let y=0;y<h;y++)for(let x=0;x<(w>>1);x++){const a=y*w+x,b=y*w+w-1-x;Hh[b]=Hh[a];Aa[b]=Aa[a];Em[b]=Em[a];C[b*3]=C[a*3];C[b*3+1]=C[a*3+1];C[b*3+2]=C[a*3+2]}
  const c=toile(w,h),g=c.getContext('2d'),im=g.createImageData(w,h),p=im.data,pas=o.pas||9,gain=o.gain||1,dec=o.sol||o.mur,gr=o.grain||0,omb=R((o.omb||16)*k);
  const lx=o.mur?-.5:-.46,ly=o.mur?-.62:-.6,sx=o.mur?.55:.7,sy=o.mur?.8:.9;
  const hh=(x,y,z)=>{if(x<0||y<0||x>=w||y>=h)return dec?z:z-1.6*k;const i=y*w+x;return Aa[i]?Hh[i]:z-1.6*k};
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x;if(!Aa[i])continue;const z=Hh[i];let r=C[i*3],v=C[i*3+1],b=C[i*3+2];
    if(gr){const nz=1+((((x*73856093)^(y*19349663))>>>0)%1000/1000-.5)*gr;r*=nz;v*=nz;b*=nz}
    if(Em[i]<1){const ax=(hh(x+1,y,z)-hh(x-1,y,z))*.5,ay=(hh(x,y+1,z)-hh(x,y-1,z))*.5,il=1/Math.sqrt(ax*ax+ay*ay+1),nx=-ax*il,ny=-ay*il;
      const df=Math.max(0,nx*lx+ny*ly+il*.655),sp=Math.pow(Math.max(0,nx*-.253+ny*-.33+il*.91),o.poli||22),d2=Math.max(0,nx*.6+ny*.55+il*.3);
      let ao=1;for(const[dx,dy]of V8)if(hh(x+dx*2,y+dy*2,z)>z+1.5*k)ao-=.07;
      let om=1;if(dec)for(let q=1;q<=omb;q++){const xx=R(x-q*sx),yy=R(y-q*sy);if(xx<0||yy<0)break;if(hh(xx,yy,0)>z+q*1.1+.5){om=o.ombre||.48;break}}
      const k1=(.26+1.0*df)*ao*om*gain,ks=sp*(dec?.12:.8)*om,e=Em[i];
      r=(r*(k1+d2*.08)+ks)*(1-e)+r*e;v=(v*(k1+d2*.14)+ks)*(1-e)+v*e;b=(b*(k1+d2*.30)+ks)*(1-e)+b*e}
    const t=BAY[(x&1)+(y&1)*2],q=u=>Math.max(0,Math.min(255,Math.floor(u*pas+t)/pas*255));
    p[i*4]=q(r);p[i*4+1]=q(v);p[i*4+2]=q(b);p[i*4+3]=255}
  if(o.contour!==false&&!dec)for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x;if(Aa[i])continue;if((x>0&&Aa[i-1])||(x<w-1&&Aa[i+1])||(y>0&&Aa[i-w])||(y<h-1&&Aa[i+w])){p[i*4]=6;p[i*4+1]=8;p[i*4+2]=18;p[i*4+3]=255}}
  g.putImageData(im,0,0);
  if(!dec&&!o.simple){c.blanc=silh(c,'#fff');c.ombre=silh(c,'#02040a')}
  return c}
const silh=(c,col)=>{const b=toile(c.width,c.height),q=b.getContext('2d');q.drawImage(c,0,0);q.globalCompositeOperation='source-in';q.fillStyle=col;q.fillRect(0,0,c.width,c.height);return b};
const miroir=c=>{const b=toile(c.width,c.height),q=b.getContext('2d');q.translate(c.width,0);q.scale(-1,1);q.drawImage(c,0,0);return b};
// im : dessine une image centrée sur un point logique (240 de large), à sa taille réelle ; rc : rectangle logique
function im(s,x,y,sc){sc=sc||1;const w=R(s.width*sc),h=R(s.height*sc);cx.drawImage(s,R(x*K-w/2),R(y*K-h/2),w,h)}
function rc(c,x,y,w,h){cx.fillStyle=c;cx.fillRect(R(x*K),R(y*K),Math.max(1,R(w*K)),Math.max(1,R(h*K)))}
const halo=(rgb,d,a)=>{d=d||48;a=a||.6;const t=toile(d,d),g=t.getContext('2d'),gr=g.createRadialGradient(d/2,d/2,0,d/2,d/2,d/2);gr.addColorStop(0,'rgba('+rgb+','+a+')');gr.addColorStop(.4,'rgba('+rgb+','+a*.36+')');gr.addColorStop(1,'rgba('+rgb+',0)');g.fillStyle=gr;g.fillRect(0,0,d,d);return t};
const SP={};
// effets communs : déchirure d'image quand ARIA ment, voile (grille + vignette), éclair
function glitch(f){for(let i=0;i<6;i++){const y=(rnd()*H)|0,h=3+((rnd()*18)|0);cx.drawImage(cv,0,y,W,h,((rnd()-.5)*54*(f||1))|0,y,W,h)}cx.fillStyle='rgba(229,40,60,.3)';cx.fillRect(0,(rnd()*H)|0,W,3+((rnd()*10)|0))}
let voile=null;
function fabVoile(grille){voile=toile(W,H);const g=voile.getContext('2d');if(grille){g.fillStyle='rgba(63,214,230,.05)';for(let x=36;x<W;x+=48)g.fillRect(x,0,1,H);for(let y=36;y<H;y+=48)g.fillRect(0,y,W,1)}
  const gr=g.createRadialGradient(W/2,H/2,H*.28,W/2,H/2,H*.72);gr.addColorStop(0,'rgba(2,4,10,0)');gr.addColorStop(1,'rgba(2,4,10,.62)');g.fillStyle=gr;g.fillRect(0,0,W,H);voile.gr=grille}
function poseVoile(grille){if(!voile||voile.height!==H||voile.gr!==grille)fabVoile(grille);cx.drawImage(voile,0,0)}

// décor large découpé en bandes (mémoire bornée) : f(T) peint en coordonnées globales ; renvoie {bandes:[toiles],larg,w,h}
function decale(T,dx){const o={w:T.w,h:T.h,
  box:(x,...a)=>T.box(x-dx,...a),ell:(x,...a)=>T.ell(x-dx,...a),cap:(x1,y1,x2,...a)=>T.cap(x1-dx,y1,x2-dx,...a),poly:(p,...a)=>T.poly(p.map(q=>[q[0]-dx,q[1]]),...a),
  trait:(x1,y1,x2,...a)=>T.trait(x1-dx,y1,x2-dx,...a),teinte:(x,...a)=>T.teinte(x-dx,...a),pix:(x,...a)=>T.pix(x-dx,...a),trou:(x,...a)=>T.trou(x-dx,...a),plat:(x,...a)=>T.plat(x-dx,...a),
  ruban:(x1,y1,x2,...a)=>T.ruban(x1-dx,y1,x2-dx,...a),rel:(x,y,rw,rh,fn)=>T.rel(x-dx,y,rw,rh,(a,b,i,j)=>fn(a+dx,b,i+dx,j)),ton:(x,y,rw,rh,fn)=>T.ton(x-dx,y,rw,rh,(a,b,i,j)=>fn(a+dx,b,i+dx,j)),
  lueur:(x,...a)=>T.lueur(x-dx,...a),lum:(x,...a)=>T.lum(x-dx,...a),haut:(x,y)=>T.haut(x-dx,y),vide:(x,...a)=>T.vide(x-dx,...a)};return o}
async function forgeBandes(wt,h,f,o,etape,txt){const L=600,M=24,B=[];for(let x0=0;x0<wt;x0+=L){if(etape)await etape(txt||'Relevé des lieux…',.15+.8*x0/wt);const c=forge(L+2*M,h,T=>f(decale(T,x0-M)),o),b=toile(Math.min(L,wt-x0),h);b.getContext('2d').drawImage(c,-M,0);B.push(b)}return{bandes:B,larg:L,w:wt,h}}
function poseBandes(D,cxm,cym){const i0=Math.max(0,Math.floor(cxm/D.larg)),i1=Math.min(D.bandes.length-1,Math.floor((cxm+W)/D.larg));for(let i=i0;i<=i1;i++)cx.drawImage(D.bandes[i],i*D.larg-cxm,-cym)}
