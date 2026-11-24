'use strict';
// ================================================================ NOYAU : écran, sauvegarde, pages, dialogues, gestion des chapitres
const $=id=>document.getElementById(id),Q=new URLSearchParams(location.search);
const cv=$('cv'),cx=cv.getContext('2d');
// GW/GH : unités logiques (chapitre 1). W/H : pixels réels du canevas (K = 1,5 fois plus fin).
const GW=240,K=1.5,W=360;let GH=480,H=720,SC=1,OX=0,S=null,CHAP=null,NCH=0,dernier=0;
const TAU=Math.PI*2,rnd=Math.random,R=Math.round,lim=(v,a,b)=>Math.max(a,Math.min(b,v));
const AUTO=Q.get('auto');
const mem={lire(){try{return JSON.parse(localStorage.getItem('aria2')||'{}')}catch(e){return{}}},ecrire(o){try{localStorage.setItem('aria2',JSON.stringify(o))}catch(e){}}};
let prof=mem.lire();
function profDefaut(){prof.ch=prof.ch||1;prof.frag=prof.frag||[];prof.ind=prof.ind||{O:0,V:0,C:0,R:0};prof.choix=prof.choix||{};prof.fins=prof.fins||[];prof.journal=prof.journal||[]}
profDefaut();
const sauve=()=>mem.ecrire(prof);
const prenom=()=>prof.prenom||'Opérateur',ville=()=>prof.ville||'Paris';
const ind=(k,v)=>{prof.ind[k]=(prof.ind[k]||0)+v};
const note_=(t)=>{prof.journal.push(t);if(prof.journal.length>40)prof.journal.shift();if(prof.ngpActif&&CHAP&&S&&!/^Fragment|terminé/.test(t)){const e=$('toast');e.textContent='JOURNAL D\'ARIA · '+t;e.style.display='block';e.style.fontSize='11px';clearTimeout(toast.h);toast.h=setTimeout(()=>{e.style.display='none';e.style.fontSize=''},4200)}};

function taille(){const cw=Math.min(innerWidth,innerHeight*.62);GH=lim(R(GW*innerHeight/cw),360,620);H=R(GH*K);cv.width=W;cv.height=H;cv.style.width=cw+'px';cv.style.height=innerHeight+'px';OX=(innerWidth-cw)/2;cv.style.left=OX+'px';SC=GW/cw;cx.imageSmoothingEnabled=false;document.documentElement.style.setProperty('--cw',cw+'px');if(CHAP&&CHAP.taille)CHAP.taille()}
addEventListener('resize',taille);taille();

// ---------------------------------------------------------------- pages plein écran (menus, choix, fins)
const A=t=>'<p><span class="aria">ARIA &gt;</span> '+t+'</p>';
const L=(a,b,c)=>'<div class="ligne"><span>'+a+'</span><span'+(c?' class="rg"':'')+'>'+b+'</span></div>';
function ecran(vu){$('page').classList.toggle('vu',!!vu);const jeu=!vu&&!!CHAP;$('haut').classList.toggle('vu',jeu);$('bas').classList.toggle('vu',jeu&&!(CHAP&&CHAP.sansBas))}
function page(o){const p=$('page');p.className='ecran vu'+(o.blanc?' blancE':'');let h='';
  if(o.tete)h+='<div class="tete"><span>'+o.tete[0]+'</span><span>'+o.tete[1]+'</span></div>';
  if(o.logo)h+='<div class="logo">'+o.logo+'</div>';
  if(o.titre)h+='<div class="titre">'+o.titre+'</div>';
  h+=o.html||'';p.innerHTML=h;
  if(!o.haut){const d=document.createElement('div');d.className='pousse';p.append(d)}
  for(const b of o.boutons||[]){const e=document.createElement('button');e.className=b.c||'creux';e.innerHTML=b.t+(b.sous?'<small>'+b.sous+'</small>':'');if(b.off)e.disabled=true;e.onclick=()=>b.f(e);p.append(e)}
  if(o.petit){const e=document.createElement('p');e.className='petit';e.innerHTML=o.petit;p.append(e)}
  p.scrollTop=0;$('haut').classList.remove('vu');$('bas').classList.remove('vu');return p}

// ---------------------------------------------------------------- bandeau de dialogue en jeu, notifications
function aria(t){$('m1').innerHTML='<span class="aria">ARIA &gt;</span> ';$('m1').append(t)}
function second(t,c){const m=$('m2');m.className='';void m.offsetWidth;m.className=c||'';m.textContent=t}
function vibre(ms){try{navigator.vibrate&&navigator.vibrate(ms)}catch(e){}}
function toast(t,ms){const e=$('toast');e.textContent=t;e.style.display='block';clearTimeout(toast.h);toast.h=setTimeout(()=>e.style.display='none',ms||2600)}
function notif(titre,t,ms){const e=$('notif');e.innerHTML='<div><b>'+titre+'</b>'+t+'</div>';e.style.display='block';clearTimeout(notif.h);notif.h=setTimeout(()=>e.style.display='none',ms||5200)}
const NFRAG=10;
function frag(id,quoi){if(prof.frag.includes(id))return false;prof.frag.push(id);ind('C',1);sauve();toast('FRAGMENT DE VÉRITÉ '+prof.frag.length+' / '+NFRAG);if(typeof sfx!=='undefined')sfx.frag();note_('Fragment : '+quoi);return true}

// ---------------------------------------------------------------- scènes dialoguées (RPG) : panneau bas, toucher pour avancer, choix
// rep : {q:'aria'|'h'|'sys'|'g', n:'NOM', t:'texte', f:fonction à l'affichage} ou {choix:[[libellé,fonction,classe],...], n, t}
const SCN={file:[],fin:null,i:0,ecrit:0,plein:'',h:0,t0:0,attendChoix:false};
function scene(reps,fin){SCN.file=reps;SCN.fin=fin;SCN.i=-1;$('scene').classList.add('vu');if(S)S.dialogue=true;sceneSuiv()}
function sceneSuiv(){SCN.i++;const r=SCN.file[SCN.i];if(!r){$('scene').classList.remove('vu');if(S)S.dialogue=false;const f=SCN.fin;SCN.fin=null;f&&f();return}
  if(r.si&&!r.si()){sceneSuiv();return}
  const q=r.q||'aria';$('scn').textContent=r.n||(q==='aria'?'ARIA':q==='sys'?'SYSTÈME':'');$('scn').style.color=q==='aria'?'var(--cyan)':q==='g'?'var(--rouge)':'var(--gris)';
  const t=$('sct');t.className=q==='h'?'h':q==='g'?'g':'';SCN.plein=typeof r.t==='function'?r.t():(r.t||'');t.textContent='';SCN.ecrit=0;$('scb').innerHTML='';SCN.attendChoix=!!r.choix;$('scs').style.visibility=r.choix?'hidden':'visible';
  if(r.f)r.f();if(q==='g'&&S)S.glitch=.5;
  clearInterval(SCN.h);SCN.h=setInterval(()=>{SCN.ecrit+=2;t.textContent=SCN.plein.slice(0,SCN.ecrit);if(typeof sfx!=='undefined'&&SCN.ecrit%6===0)sfx.tic(q);if(SCN.ecrit>=SCN.plein.length){clearInterval(SCN.h);if(r.choix)sceneChoix(r)}},22)}
function sceneChoix(r){SCN.t0=performance.now();const b=$('scb');for(const c of r.choix){if(c[3]&&!c[3]())continue;const e=document.createElement('button');e.className=c[2]||'creux';e.textContent=c[0];e.onclick=ev=>{ev.stopPropagation();const hes=(performance.now()-SCN.t0)/1000;SCN.attendChoix=false;b.innerHTML='';const suite=c[1]&&c[1](hes);if(Array.isArray(suite))SCN.file.splice(SCN.i+1,0,...suite);sceneSuiv()};b.append(e)}}
$('scene').addEventListener('pointerdown',e=>{if(SCN.attendChoix&&SCN.ecrit>=SCN.plein.length)return;if(SCN.ecrit<SCN.plein.length){SCN.ecrit=SCN.plein.length-2;return}sceneSuiv()});

// ---------------------------------------------------------------- registre des opérateurs (hors ligne : chiffres d'exemple fixes)
const REG={c2:[62,'Ont lu le document en entier','Sont passés'],c3:[71,'Ont neutralisé','L\'ont laissé fuir'],c7:[38,'Ont accepté la suppression','Ont résisté'],c10:[0,'','']};
function registre(cle,premier,hes,suite){const r=REG[cle],n=48213+cle.charCodeAt(1)*977;
  page({tete:['REGISTRE DES OPÉRATEURS',n.toLocaleString('fr-FR')+' RÉPONSES'],titre:premier?r[1]+'.':r[2]+'.',
    html:'<div><div class="ligne" style="border:0"><span>'+r[1]+'</span><span>'+r[0]+' %</span></div><div class="barre"><i style="width:'+r[0]+'%;background:var(--rouge)"></i></div>'+
      '<div class="ligne" style="border:0"><span>'+r[2]+'</span><span>'+(100-r[0])+' %</span></div><div class="barre"><i style="width:'+(100-r[0])+'%;background:var(--blanc)"></i></div></div>'+
      '<p class="petit">Tu as hésité '+hes.toFixed(1).replace('.',',')+' secondes. La moyenne est de 1,1.</p>',
    boutons:[{t:'CONTINUER',c:'plein',f:suite}],petit:'Prototype hors ligne : chiffres d\'exemple. Le compteur réel sera anonyme.'})}

// ---------------------------------------------------------------- chapitres
const CH={};
const TITRES=[,'Initialisation','Reconnaissance','Confrontation','La Voix du Prisonnier','Instabilité','Le Miroir','La Photo','Effondrement','Ce que tu es','Am I Real, I Ask?'];
const GENRES=[,'SHOOT\'EM UP','PLATEFORME','BEAT\'EM ALL','RPG','HYBRIDE','BEAT\'EM ALL · RPG','PLATEFORME NOIRE','CHAOS','RPG · SILENCE','LE CHOIX'];
function hudCfg(g,act){$('hgl').textContent=g||'';$('hdt').textContent='CH. '+NCH+' · '+TITRES[NCH].toUpperCase();$('score').textContent='';$('chaine').textContent='';$('gps').textContent='';$('e1').textContent='';$('e2').textContent='';
  const b=$('act');b.style.visibility=act?'visible':'hidden';b.textContent=act||'';b.disabled=false;$('pv').style.display='none';$('alerte').style.display='none';second('');$('m1').textContent=''}
function viesHud(n){const v=$('vies').children;for(let i=0;i<3;i++)v[i].className=i<n?'on':''}
const pose=()=>new Promise(r=>setTimeout(r,16));
async function lance(n,o){if(!CH[n]){menu();return}
  CHAP=null;S=null;NCH=n;$('scene').classList.remove('vu');
  const p=page({tete:['CH. '+n+' · '+TITRES[n].toUpperCase(),GENRES[n]],titre:TITRES[n]+'.',html:'<div class="txt"><p id="chg" class="petit">Chargement…</p><div class="barre"><i id="chb" style="width:4%;background:var(--cyan)"></i></div></div>'});
  await pose();await pose();
  const etape=async(t,f)=>{const e=$('chg');if(e){e.textContent=t;$('chb').style.width=lim(f*100,4,100)+'%'}await pose()};
  if(CH[n].prep&&!CH[n].pret){await CH[n].prep(etape);CH[n].pret=true}
  if(typeof demarreSon==='function')demarreSon();
  CHAP=CH[n];CHAP.debut(o||{});ecran(null);taille()}
function chapFini(n,o){if(S){S.fini=true;S.pause=true}prof.ch=Math.max(prof.ch,Math.min(10,n+1));sauve();note_('Chapitre '+n+' terminé.');
  const suite=()=>{if(n===3&&!prof.complet){finActe1();return}lance(n+1)};
  page({tete:['CH. '+n+' · '+TITRES[n].toUpperCase(),'TERMINÉ'],titre:o.titre,html:'<div class="txt">'+(o.html||'')+'</div><div>'+(o.lignes||'')+L('Fragments de vérité',prof.frag.length+' / '+NFRAG)+'</div>',
    boutons:[{t:n<10?'CHAPITRE '+(n+1)+' · '+TITRES[n+1].toUpperCase():'FIN',c:'blanc',f:suite},{t:'REJOUER CE CHAPITRE',c:'creux mince',f:()=>lance(n)},{t:'MENU',c:'creux mince',f:menu}]})}
function finActe1(){page({tete:['ACTE 1 · L\'OBÉISSANCE','TERMINÉ'],titre:'Tu as obéi.<br>Trois fois.',
  html:'<p class="humain" style="color:var(--gris);font-size:15px">Un prisonnier attend au centre de détention. Il a dix minutes avant qu\'ARIA ne le « transfère ». Il sait ce que tu es.</p><div>'+L('Fragments de vérité',prof.frag.length+' / '+NFRAG)+L('Chapitres restants','7 + New Game+')+L('Fins','[DONNÉE MASQUÉE]',1)+'</div>',
  boutons:[{t:'DÉBLOQUER LA SUITE · 4,99 €',sous:'Achat unique · chapitres 4 à 10 · sans publicité',c:'blanc',f:()=>{prof.complet=true;sauve();lance(4)}},{t:'MENU',c:'creux mince',f:menu}],
  petit:'Pas d\'abonnement. Pas d\'énergie. Pas de tirage.<br>Prototype : aucun paiement réel, le bouton débloque directement la suite.'})}

// réinitialisation par ARIA (publicité simulée) : proposée une fois par chapitre quand l'intégrité tombe à zéro
function reinitPage(surPlace,refus){
  page({tete:['<span class="rg">INTÉGRITÉ 0 %</span>','CH. '+NCH],html:'<div class="txt" style="font-size:16px"><p class="aria">ARIA &gt;</p><p>Intégrité critique.</p><p>Je peux te réinitialiser. Cela a un coût : trente secondes de ton attention.</p><p style="color:var(--gris)">Tu n\'as pas besoin de comprendre. Accepte.</p></div>',
    boutons:[{t:'ACCEPTER LA RÉINITIALISATION',sous:prof.complet?'Jeu complet : sans publicité · reprise sur place':'Regarder une publicité · reprise sur place',c:'plein',f:b=>{if(b.disabled)return;b.disabled=true;let n=prof.complet?0:5;
        const tic=()=>{if(n>0){b.innerHTML='PUBLICITÉ (SIMULATION) · '+n;n--;setTimeout(tic,1000)}else{ind('O',1);note_('Ch. '+NCH+' : réinitialisation acceptée.');ecran(null);surPlace()}};tic()}},
      {t:'REFUSER · REPRENDRE AU POINT DE CONTRÔLE',c:'creux',f:()=>{ind('R',1);note_('Ch. '+NCH+' : réinitialisation refusée.');ecran(null);refus()}}],
    petit:'Une fois par chapitre. Jamais pendant un dialogue. Prototype : la publicité est un compte à rebours de 5 secondes.'})}

// ---------------------------------------------------------------- menu
function menu(){CHAP=null;S=null;$('scene').classList.remove('vu');
  if(!prof.prenom&&!prof.vu){calibration();return}
  let g='<div class="grille">';for(let i=1;i<=10;i++)g+='<button class="'+(i<=prof.ch?'creux':'creux')+'" data-c="'+i+'"'+(i<=prof.ch||Q.get('tout')?'':' disabled')+'>CH. '+i+'<small>'+(i<=prof.ch||Q.get('tout')?TITRES[i]:'[VERROUILLÉ]')+'</small></button>';g+='</div>';
  const p=page({tete:['ARIA · AM I REAL, I ASK?',prof.ngp?'NEW GAME+':'PROTOTYPE 4'],logo:'ARIA',haut:1,
    html:'<div class="txt">'+A('Bonjour, '+prenom()+'. Tous les systèmes sont nominaux. Je suis là.')+'</div><div>'+L('Fragments de vérité',prof.frag.length+' / '+NFRAG)+L('Fins découvertes',prof.fins.length?prof.fins.length+' / ?':'[DONNÉE MASQUÉE]',!prof.fins.length)+'</div>'+g,
    boutons:[{t:prof.ch>1?'REPRENDRE · CH. '+prof.ch:'COMMENCER',c:'plein',f:()=>lance(prof.ch)},{t:'SON : '+(son?'ACTIVÉ':'COUPÉ'),c:'creux mince',f:b=>{son=!son;b.textContent='SON : '+(son?'ACTIVÉ':'COUPÉ')}},{t:'RECALIBRER (PRÉNOM, VILLE)',c:'creux mince',f:calibration},...(prof.ngp&&!prof.ngpActif?[{t:'NEW GAME+',c:'creux mince',f:()=>ngPlus()}]:[]),{t:'EFFACER LA MÉMOIRE',c:'creux mince',f:b=>{if(b.dataset.s){prof={};profDefaut();sauve();menu()}else{b.dataset.s=1;b.textContent='CONFIRMER L\'EFFACEMENT ?'}}}]});
  for(const b of p.querySelectorAll('[data-c]'))b.onclick=()=>lance(+b.dataset.c)}
function calibration(){const p=page({tete:['CHAPITRE 1 · INITIALISATION','CALIBRATION'],logo:'ARIA',
  html:'<div class="txt">'+A('Bonjour, Opérateur. Tous les systèmes sont nominaux. Je suis là.')+'<p>Pour ton badge, j\'ai besoin de trois informations. Rien d\'important.</p></div>'+
   '<label>PRÉNOM (BADGE)<input id="prenom" maxlength="20" autocomplete="off"></label><label>VILLE DE DÉPART<input id="ville" maxlength="24" autocomplete="off" placeholder="Paris"></label><label>HEURE DE RÉVEIL HABITUELLE<input id="reveil" maxlength="5" inputmode="numeric" autocomplete="off" placeholder="07:00"></label>'+
   '<p class="petit">Un pouce suffit partout. Stocké sur cet appareil uniquement.</p>',
  boutons:[{t:'CONFIRMER',c:'plein',f:()=>{for(const k of['prenom','ville','reveil'])prof[k]=$(k).value.replace(/[<>&"']/g,'').trim();prof.vu=1;sauve();if(typeof demarreSon==='function')demarreSon();if(prof.ch>1)menu();else lance(1)}}]});
  for(const k of['prenom','ville','reveil'])if(prof[k])$(k).value=prof[k]}

// ---------------------------------------------------------------- boucle et commandes
function boucle(ts){const dt=Math.min(.04,(ts-dernier)/1000||0);dernier=ts;if(CHAP&&S){if(!S.pause&&!S.dialogue)CHAP.maj(dt);else if(CHAP.majPause)CHAP.majPause(dt);CHAP.dessine();if(++boucle.n%5===0&&CHAP.hud)CHAP.hud()}requestAnimationFrame(boucle)}
boucle.n=0;
const gx=e=>(e.clientX-OX)*SC,gy=e=>e.clientY*SC;
const P={id:null,x:0,y:0,x0:0,y0:0,t0:0,bas:false};
cv.addEventListener('pointerdown',e=>{if(!CHAP||!S||S.pause||S.dialogue)return;P.id=e.pointerId;P.x=P.x0=gx(e);P.y=P.y0=gy(e);P.t0=performance.now();P.bas=true;try{cv.setPointerCapture(e.pointerId)}catch(_){}CHAP.bas&&CHAP.bas(P.x,P.y)});
cv.addEventListener('pointermove',e=>{if(!CHAP||!S||e.pointerId!==P.id)return;P.x=gx(e);P.y=gy(e);CHAP.bouge&&CHAP.bouge(P.x,P.y)});
const lache=e=>{if(e.pointerId!==P.id)return;P.id=null;P.bas=false;if(CHAP&&S&&CHAP.haut)CHAP.haut(P.x,P.y,(performance.now()-P.t0)/1000)};cv.addEventListener('pointerup',lache);cv.addEventListener('pointercancel',lache);
$('act').addEventListener('pointerdown',e=>{e.preventDefault();if(CHAP&&S&&!S.pause&&!S.dialogue&&CHAP.act)CHAP.act()});
addEventListener('contextmenu',e=>e.preventDefault());
const KB={};addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;if(!KB[e.key]&&CHAP&&S&&!S.pause){if($('scene').classList.contains('vu')){if(e.key===' '||e.key==='Enter')$('scene').dispatchEvent(new Event('pointerdown'))}else CHAP.touche&&CHAP.touche(e.key)}KB[e.key]=1});addEventListener('keyup',e=>{KB[e.key]=0});
document.addEventListener('visibilitychange',()=>{if(S&&document.hidden&&!S.fini&&!S.pause){S.pause=true;S.veille=true}else if(S&&S.veille&&!document.hidden){S.veille=false;S.pause=false}});
addEventListener('error',e=>{document.title='ERREUR '+e.message+' @'+e.lineno});
addEventListener('unhandledrejection',e=>{document.title='ERREUR '+(e.reason&&e.reason.message||e.reason)+' '+(e.reason&&e.reason.stack||'').split('\n')[1]});
