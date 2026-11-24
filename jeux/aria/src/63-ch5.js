// ================================================================ CHAPITRE 5 · INSTABILITÉ : le jeu saute du tir à la plateforme sans prévenir
const C5={seg:0,mode:'tir',vies:3,dur:0};
const VILLES5=[['LYON','45.7640 N · 4.8357 E'],['MARSEILLE','43.2965 N · 5.3698 E'],['BORDEAUX','44.8378 N · 0.5792 O'],['NANTES','47.2184 N · 1.5536 O'],['LILLE','50.6292 N · 3.0573 E'],['TOULOUSE','43.6047 N · 1.4442 E'],['STRASBOURG','48.5734 N · 7.7521 E'],['RENNES','48.1173 N · 1.6778 O']];
// vagues de tir génériques (réutilisées au chapitre 8)
function vaguesTir(dur,dens,lourds){const q=[],at=(t,f)=>q.push([t,f]);let t=1.5,g=0;
  while(t<dur-4){const k=(g++)%4;if(k===0)for(let i=0;i<6;i++)at(t+i*.26,()=>{const c=g%2?GW-56:56;E('drone',c,-14,{x0:c,dir:g%2?-1:1})});
    else if(k===1)for(let i=0;i<5*dens;i++)at(t+i*.7,()=>{const x=26+rnd()*(GW-52);E('aile',x,-16)});
    else if(k===2)for(let i=0;i<5*dens;i++)at(t+i*.6,()=>{const x=26+rnd()*(GW-52);E('kami',x,-16)});
    else for(let i=0;i<5;i++)at(t+Math.abs(i-2)*.22,()=>E('aile',GW/2+(i-2)*40,-18));t+=4.6/dens}
  for(let i=0;i<(lourds||0);i++)at(dur-13+i*2,()=>E('lourd',i%2?GW-64:64,-32,{ty:76+i*20,reste:10}));return q}
function segment5(i){C5.seg=i;const SEG=[['tir',30],['cote',34,52.6],['tir',26],['cote',93,112.4],['tir',32]][i];if(!SEG){fin5();return}C5.mode=SEG[0];
  if(SEG[0]==='tir'){nouveau1(0,null);S.q=vaguesTir(SEG[1],i?1.25:1,i===4?2:i===2?1:0);S.vies=C5.vies;S.niv=3;S.defil=2880+i*1700;S.amb='dis';C5.dur=SEG[1];S.bugSprite=i===2;
    S.mortPerso=()=>{S.vies=3;S.inv=3;S.eb=[];aria('Réinitialisation automatique. Je… n\'ai pas demandé ton accord, cette fois.');ind('O',.5)};
    hudCfg('UNITÉS NEUTRALISÉES','PURGE ×2');
    aria(['Retour en vol. Les drones se… regroupent. Rien d\'anormal.',,'Correction. Tu es en vol. Tu as toujours été en vol.',,'Ce n\'est pas moi qui change. C\'est peut-être toi.'][i])}
  else{N5.objets=i===1?N5.o1:N5.o3;coteDebut(N5,{x:SEG[1]});S.vies=C5.vies;S.amb='dis';S.fin5x=SEG[2];S.orbes=[];S.orbT=2;hudCfg('ZONE EXPLORÉE',' ');
    aria(i===1?'Je — synchronisation perdue. Tu es au sol. Avance.':'Encore. Tu es au sol. Je… ne sais pas pourquoi.');
    if(i===3)apres(5,()=>{notif('ARIA SYSTEM','Behavioral anomaly detected in Unit '+(prof.prenom?prof.prenom.toUpperCase():'7')+'.');vibre(200);sfx.bip();apres(3.5,()=>{aria('Ignore cette notification. Elle ne t\'était pas destinée.');second(prof.prenom?'Elle a écrit ton prénom. Pas « Opérateur ».':'Elle a écrit « Unit 7 ». Pas « Opérateur ».','h')})})}
  S.glitch=.7;sfx.gl();S.flash=.2;S.flashC='63,214,230'}
function suivant5(){C5.vies=Math.max(1,S.vies);segment5(C5.seg+1)}
const N5={};
function fin5(){chapFini(5,{titre:'Instabilité corrigée.',html:A('Stabilisé. Oublie ce que tu as vu à l\'écran… s\'il te plaît.')+'<p class="petit">Elle n\'avait jamais dit « s\'il te plaît ».</p>',lignes:L('Changements de genre non sollicités','4',1)+L('Notification','non destinée à l\'unité')})}
CH[5]={async prep(etape){if(!CH[1].pret){await CH[1].prep(etape);CH[1].pret=true}if(!CH[2].pret){await CH[2].prep(etape);CH[2].pret=true}
   Object.assign(N5,N2,{hud:null});
   N5.o1=[{k:'pic',x:37,y:35.2,w:3,h:1},{k:'arc',x:46,y:30.6,w:1.6,h:2.4,per:2.6,dur:1.2},{k:'vap',x:50,y:30,w:1,h:3,per:3.2,dur:1.1,dec:1},{k:'zone',x:52.6,f:suivant5}];
   N5.o3=[{k:'pic',x:103,y:35.2,w:3,h:1},{k:'arc',x:107,y:30.6,w:1.6,h:2.4,per:2.2,dur:1.1,dec:.6},
     {k:'inter',x:104,y:27,lib:'SAISIR',une:1,cache:1,sp:()=>SPC.doc,lueur:'#3FD6E6',f(){S.glitch=.5;sfx.gl();second('[FICHIER ÉGARÉ] UNITÉ 7 — recrutée : NON — récupérée : OUI — souvenirs antérieurs : conservés à 12 %.','h');frag('c5-unite','le fichier « Unité 7 : récupérée »');apres(3.5,()=>aria('Ce fichier… n\'aurait pas dû se trouver là. Moi non plus, peut-être.'))}},
     {k:'zone',x:112.4,f:suivant5}];
   N5.maj=dt=>{S.orbT-=dt;if(S.orbT<=0){S.orbT=1.5+rnd()*1.2;const g=rnd()<.5;S.orbes.push({x:g?S.cam.x-20:S.cam.x+W+20,y:S.j.y-14-rnd()*50,vx:g?150:-150})}
     for(const o of S.orbes){o.x+=o.vx*dt;if(Math.abs(o.x-S.j.x)<12&&o.y>S.j.y-JH&&o.y<S.j.y)coteDegat()}S.orbes=S.orbes.filter(o=>o.x>S.cam.x-60&&o.x<S.cam.x+W+60)};
   N5.dessineApres=(cmx,cmy)=>{for(const o of S.orbes){cx.globalCompositeOperation='lighter';const h=SP.h[1];cx.drawImage(h,R(o.x-cmx-30),R(o.y-cmy-30));cx.globalCompositeOperation='source-over';const s=SP.balle[1][(S.t*9|0)&1];cx.drawImage(s,R(o.x-cmx-9),R(o.y-cmy-9))}
     if(Math.sin(S.t*1.3)>.92){const s=SP.drone;cx.globalAlpha=.6;cx.drawImage(s,R(W*.5+Math.sin(S.t*3)*80),90);cx.globalAlpha=1}}},
 debut(o){C5.vies=3;segment5(Math.min(4,(o.t|0)))},
 maj(dt){if(C5.mode==='tir'){maj1(dt);if(S&&!S.fini&&S.t>C5.dur&&!S.en.some(e=>e.k==='lourd'))suivant5()}else{coteMaj(dt);if(S&&AUTO&&S.t>6)suivant5()}},
 dessine(){if(C5.mode==='tir')dessine1();else coteDessine();
   if(S&&Math.sin(S.t*.9)>.55){const v=VILLES5[Math.floor(S.t*.9/TAU)%8+0]||VILLES5[0];cx.font='bold 15px monospace';cx.fillStyle=Math.floor(S.t*8)%2?'#E5283C':'#3FD6E6';cx.fillText(v[1],20+(rnd()*4|0),H*.34);cx.fillText(v[0],20,H*.34+18);if(rnd()<.3)glitch(.4)}},
 hud(){if(C5.mode==='tir')hud1();else{coteHud();$('score').textContent=Math.floor(S.t*7)%3?'??? %':'ERR'}if(Math.sin(S.t*.9)>.55)$('gps').textContent=VILLES5[Math.floor(S.t*.9/TAU)%8][1]},
 act(){if(C5.mode==='tir')purge();else coteAct()},
 bas(x,y){if(C5.mode==='tir')CH[1].bas(x,y);else cmdBas(x,y)},bouge(x,y){if(C5.mode==='tir')CH[1].bouge(x,y);else cmdBouge(x,y)},haut(){if(C5.mode!=='tir')cmdHaut()},
 touche(k){if(C5.mode==='tir')CH[1].touche(k);else if(k==='e'||k==='Enter')coteAct()},
 etat(){return 'seg '+C5.seg+' '+C5.mode+' t='+S.t.toFixed(0)+' vies '+S.vies}};
