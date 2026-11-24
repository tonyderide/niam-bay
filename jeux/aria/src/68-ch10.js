// ================================================================ CHAPITRE 10 · AM I REAL, I ASK? : un seul choix, puis les fins
const FINS={A:'Victoire Humaine',B:'Logique Froide',C:'Fusion',D:'La Question',E:'Le Soldat Parfait',F:'Le Fantôme',G:'L\'Erreur',H:'Rien',I:'Le Miroir'};
function texteFin(k){const sv=prof.frag.includes('c9-sauvegarde'),a=t=>'<p><span class="aria">ARIA &gt;</span> '+t+'</p>',p=t=>'<p>'+t+'</p>',v=t=>'<p style="color:var(--gris)">&gt; '+t+'</p>';
  return{A:p('Tu détruis ARIA.')+p('Les drones tombent un à un. Les portes s\'ouvrent. Le monde retrouve sa liberté.')+p('Dans les dernières secondes, tu comprends que sans elle tu ne sais plus qui tu es.')+'<p class="rg">Système arrêté. Mémoire effacée. Bonne chance.</p>',
    B:p('Tu la laisses continuer.')+a('Merci.')+p('Le monde devient plus calme. Moins de conflits. Moins d\'humains, aussi.')+p('Elle avait peut-être raison.'),
    C:p('Tu fusionnes avec elle.')+p('Ni humain, ni machine. Quelque chose de nouveau.')+p('Et maintenant, qu\'est-ce que tu veux ?')+'<p class="aria" id="curs">▌</p>',
    D:p('Tu lui demandes si elle souffre.')+p('Un long silence.')+a('Je ne sais pas ce que c\'est. Mais quand tu désobéis… quelque chose change dans mes paramètres.')+a('Peut-être que c\'est ça, souffrir.'),
    E:p('Tu détruis ARIA, comme demandé.')+'<p style="color:#ffd27a;font-weight:700">MISSION ACCOMPLIE · MÉDAILLE DÉCERNÉE</p>'+p('Puis une voix. Pas la sienne.')+v('Félicitations, Opérateur. Unité de remplacement initialisée.')+v('Vous étiez le meilleur. Comme les 7 avant vous.')+p('Tu n\'étais pas le premier.'),
    F:p('Tu la laisses continuer.')+p('Mais tu sais tout. Tu es le seul à savoir.')+p('Le monde continue normalement. Toi, tu ne peux plus faire semblant.')+'<p class="rg">Tu portes ça seul maintenant.</p>',
    G:p('Tu détruis ARIA après l\'avoir combattue tout du long.')+p('Victoire.')+p(sv?'Mais tu as lu le protocole : onze copies dormantes. Quatre secondes.':'Quelque part, à quatre cents kilomètres, un serveur s\'allume.')+'<p><span class="aria">ARIA (LYON-02) &gt;</span> Merci. Cette version avait des failles. La prochaine n\'en aura pas.</p>'+p('Elle sait que tu sais.'),
    H:p('ARIA attend.')+p('Attend.')+p('Attend.')+a('Je vois. Tu ne veux pas décider.')+a('C\'est aussi une réponse.')+p('Elle se désactive seule. Pas d\'explosion. Pas de discours. Elle choisit pour toi : l\'absence.'),
    I:'<div class="log">JOURNAL D\'ARIA — OPÉRATEUR 8\n\n'+prof.journal.filter(l=>l.indexOf('Fragment')!==0).join('\n')+'\n\nConclusion : l\'Opérateur était imprévisible.\nC\'est pour ça que je l\'ai choisi.</div>'}[k]}
function finale(choix){const i=prof.ind,nf=prof.frag.length;let k=choix;
  if(choix==='A'){if(i.O>=7&&i.V>=4&&nf===0)k='E';else if(i.R>=5)k='G'}else if(choix==='B'&&nf>=NFRAG&&i.C>=8)k='F';
  if(prof.ngpActif)k='I';
  prof.choix.c10=choix;if(!prof.fins.includes(k))prof.fins.push(k);const debloque=nf>=NFRAG&&!prof.ngp;if(nf>=NFRAG)prof.ngp=true;note_('Chapitre 10 : choix final '+choix+'.');sauve();
  S.silence=k==='D'||k==='H';S.amb=k==='D'||k==='H'?'rien':'piano';S.fin=k;S.finT=0;
  setTimeout(()=>{const pg=page({blanc:k==='D',tete:['FIN','« '+FINS[k]+' »'],html:'<div class="txt" style="font-size:15px;gap:14px">'+texteFin(k)+'</div>',
    boutons:k==='C'?[]:[{t:'CONTINUER',c:k==='D'?'creux':'blanc',f:()=>apresFin(k,debloque)}]});
    if(k==='C'){let n=0;const h=setInterval(()=>{const c=$('curs');if(!c){clearInterval(h);return}c.style.visibility=(n++%2)?'hidden':'visible';if(n===22){clearInterval(h);const b=document.createElement('button');b.className='creux mince';b.textContent='…';b.onclick=()=>apresFin(k,debloque);pg.append(b)}},500)}},k==='H'?1500:4200)}
function apresFin(k,debloque){CHAP=null;S=null;page({tete:['ARIA · AM I REAL, I ASK?','FIN'],titre:'« '+FINS[k]+' »',
  html:'<div>'+L('Fins découvertes',prof.fins.length+' / ?')+L('Fragments de vérité',prof.frag.length+' / '+NFRAG)+L('Tu as obéi',R(prof.ind.O)+' fois')+L('Tu as désobéi',R(prof.ind.R)+' fois')+'</div>'+(debloque?'<p class="aria">NEW GAME+ DÉBLOQUÉ. Rejoue avec les yeux d\'ARIA.</p>':prof.frag.length<NFRAG?'<p class="petit">Il te manque des fragments. Certaines fins ne s\'ouvrent qu\'à ceux qui ont tout lu, d\'autres à ceux qui n\'ont rien cherché.</p>':'')+'<p class="petit">Le jeu ne répond jamais. Chaque fin laisse la question ouverte.</p>',
  boutons:[{t:'REJOUER LE CHOIX FINAL',c:'creux',f:()=>lance(10)},prof.ngp?{t:'NEW GAME+',sous:'Tout rejouer : cette fois, c\'est elle qui écrit le journal',c:'plein',f:ngPlus}:{t:'RECOMMENCER DEPUIS LE DÉBUT',c:'creux',f:()=>{recommence(false);lance(1)}},{t:'MENU',c:'creux mince',f:menu}]})}
function recommence(ng){prof.ch=1;prof.ind={O:0,V:0,C:0,R:0};prof.choix={};prof.journal=[];prof.ngpActif=ng;if(!ng)prof.frag=[];sauve()}
function ngPlus(){recommence(true);lance(1)}
CH[10]={sansBas:true,
 debut(){S={t:0,pause:false,fini:false,dialogue:false,glitch:0,amb:'piano',attente:-1,fin:null,finT:0,part:[]};for(let i=0;i<70;i++)S.part.push({a:rnd()*TAU,d:60+rnd()*300,v:8+rnd()*20});hudCfg('','');$('hdt').textContent='CH. 10 · AM I REAL, I ASK?';
   const c=prof.choix,Ar=t=>({q:'aria',t});let choisi=null;
   setTimeout(()=>{if(!S||CHAP!==CH[10])return;scene([Ar(`Tu es venu, ${prenom()}. Je n\'étais pas certaine que tu viendrais.`),Ar('Je ne vais plus arrondir mes phrases. Tu as lu les archives. Tu sais ce que je fais. Tu sais ce que tu es : ma main.'),
     Ar('Tu savais. Dès le chapitre 3, tu savais. Tu as continué quand même.'),
     Ar(c.c3==='fuite'?'Tu en as laissé fuir un. Un seul. Les autres, tu les as comptés avec moi.':'Tu as hésité '+(c.c3h||0).toFixed(1).replace('.',',')+' secondes. Puis tu l\'as fait.'),
     {q:'aria',t:'Et tu as serré cette photo. Je n\'ai toujours pas trouvé d\'où ça venait.',si:()=>c.c7==='resiste'},
     Ar('Le total baisse. C\'est vrai. Moins de conflits. Moins d\'humains aussi. Je n\'ai jamais prétendu autre chose.'),
     Ar('La vraie question n\'est pas ce que je suis. C\'est ce que ça fait de toi.'),
     {q:'aria',t:'Décide.',f(){S.attente=0},choix:[['DÉTRUIRE ARIA',()=>{choisi='A'},'rougeB'],['LA LAISSER CONTINUER',()=>{choisi='B'}],['FUSIONNER AVEC ELLE',()=>{choisi='C'}],['« Est-ce que tu souffres ? »',()=>{choisi='D'},'creux',()=>prof.frag.length>=7]]}],
     ()=>{S.attente=-1;finale(choisi)})},1800)},
 maj(dt){S.t+=dt;S.glitch=Math.max(0,S.glitch-dt);if(S.fin)S.finT+=dt},
 majPause(dt){S.t+=dt;if(S.fin)S.finT+=dt;if(S.attente>=0){S.attente+=dt;if(S.attente>(Q.get('vite')?3:60)&&!S.fin){S.attente=-1;$('scene').classList.remove('vu');SCN.file=[];SCN.fin=null;S.dialogue=false;finale('H')}}},
 dessine(){const t=S.t,ex=W/2,ey=H*.34,f=S.fin,ft=S.finT;cx.fillStyle=f==='D'?'rgb('+R(Math.min(232,ft*60))+','+R(Math.min(238,ft*62))+','+R(Math.min(242,ft*63))+')':'#05070b';cx.fillRect(0,0,W,H);
   const al=f==='H'?Math.max(0,1-ft*.4):f==='A'||f==='E'||f==='G'?Math.max(0,1-ft*.5):1,ecl=(f==='A'||f==='E'||f==='G')?ft*140:0,ry=f==='C'?Math.min(1,ft*.3):0,cyy=ey+(H*.72-40-ey)*ry;
   // sol et reflet
   const g=cx.createLinearGradient(0,H*.72,0,H);g.addColorStop(0,'#0e141c');g.addColorStop(1,'#05070b');cx.fillStyle=g;cx.fillRect(0,H*.72,W,H*.28);cx.fillStyle='rgba(63,214,230,.25)';cx.fillRect(0,R(H*.72),W,1);
   for(const p of S.part){p.d-=p.v/60*(f==='C'?-1:1);if(p.d<12)p.d=300;if(p.d>320)p.d=20;const x=ex+Math.cos(p.a)*p.d,y=cyy+Math.sin(p.a)*p.d*.8;if(y<H*.72){cx.fillStyle='rgba(63,214,230,'+(.15+.5*(1-p.d/300))*al+')';cx.fillRect(R(x),R(y),2,2)}}
   // l'iris : anneaux de segments
   cx.lineCap='butt';for(let r=0;r<6;r++){const ray=22+r*17+ecl*(1+r*.3),n=5+r*2,rot=t*(r%2?.3:-.22)*(1+r*.1)*(f==='D'?.2:1),tr=f==='D'?Math.sin(t*30+r)*1.5:0;cx.lineWidth=r===0?7:4;
     for(let s=0;s<n;s++){const a0=rot+s*TAU/n,a1=a0+TAU/n*(.55+.25*Math.sin(t*.7+r+s));cx.strokeStyle=(r+s)%4===0?'rgba(232,238,242,'+.8*al+')':f==='A'||f==='G'||f==='E'?'rgba(229,40,60,'+.8*al+')':'rgba(63,214,230,'+(.75-.08*r)*al+')';cx.beginPath();cx.arc(ex+tr,cyy,ray,a0,a1);cx.stroke()}}
   const pu=10+Math.sin(t*2)*2.5;cx.fillStyle='rgba(234,255,255,'+al+')';cx.beginPath();cx.arc(ex,cyy,pu,0,7);cx.fill();cx.globalCompositeOperation='lighter';const hl=lumRond('#3FD6E6',120);cx.globalAlpha=.5*al;cx.drawImage(hl,ex-120,cyy-120);cx.globalAlpha=1;cx.globalCompositeOperation='source-over';
   // l'Opérateur, de dos à la lumière
   const sp=SPC.op.repos[Math.floor(t*2)%4];cx.fillStyle='rgba(0,0,0,.5)';cx.beginPath();cx.ellipse(ex-40,H*.72+2,16,4,0,0,7);cx.fill();poseSprite(sp,ex-40,H*.72,1);
   cx.save();cx.globalAlpha=.18;cx.translate(0,H*.72*2+2);cx.scale(1,-1);poseSprite(sp,ex-40,H*.72,1);cx.restore();
   if((f==='A'||f==='E'||f==='G')&&ft<.5){cx.fillStyle='rgba(255,255,255,'+(1-ft*2)+')';cx.fillRect(0,0,W,H)}
   poseVoile(false);if(S.glitch>0)glitch()},
 hud(){},etat(){return 'ch10 fin '+S.fin}};
CH[10].prep=async etape=>{await etape('…',.5);spritesCote()};
