// ================================================================ CHAPITRE 8 · EFFONDREMENT : tous les genres, sans transition
const C8={seg:0,mode:'tir',dur:0,miroir:false};
const SEG8=[['tir',9],['cote',34,7],['rue',8],['tir',7,1],['cote',93,7,1],['rue',7,1],['tir',6],['cote',14,5],['rue',6],['tir',5,1],['cote',60,4,1],['tir',8]];
const COUPES8=['Je contr—','Ce n\'est p—','Tous les systèmes sont n—','Opérateur, ne reg—','Reprise de la synchro— reprise de la— reprise','Tu n\'es pas cens— tu n\'es pas— tu','Je suis l—','Erreur. Erreur. Err—','Reste. S\'il te pl—','Qui est-ce qui déc—','Je ne t\'ai jamais m—','…'];
const N8c={},N8r={};
function segment8(i){C8.seg=i;const s=SEG8[i];if(!s){fin8();return}C8.mode=s[0];C8.miroir=!!s[s[0]==='tir'?2:s[0]==='rue'?2:3];
  if(s[0]==='tir'){nouveau1(0,null);S.q=vaguesTir(s[1]+6,1.5,0);S.niv=4;S.defil=1000+i*800;C8.dur=s[1];S.bugSprite=i%4===3;S.mortPerso=()=>{S.vies=3;S.inv=2};hudCfg('UNITÉS NEUTRALISÉES','PURGE ×2')}
  else if(s[0]==='cote'){N8c.objets=[];coteDebut(N8c,{x:s[1]});C8.dur=s[2];S.orbes=[];S.orbT=.6;hudCfg('ZONE EXPLORÉE',' ')}
  else{N8r.vagues=[{x:-1,en:[['civil1',1,0],['b1',-1,20],['civil3',1,-30],['civil4',-1,30,{peur:1}]]}];rueDebut(N8r,null);S.j.x=300+i*190;S.cam.x=S.j.x-W*.4;C8.dur=s[1];hudCfg('UNITÉS NEUTRALISÉES','FRAPPER')}
  S.amb=i>8?'srv':'dis';S.glitch=.5;sfx.gl();aria(COUPES8[i]);if(i%3===1)second(['48.8566 N · 2.3522 E','UNITÉ 8 · INTÉGRITÉ ???','[DONNÉE MASQUÉE][DONNÉE MASQUÉE]','« Papa ? »'][(i/3)|0],i>8?'h':'g')}
function fin8(){S.silence=true;S.fini=true;S.pause=true;page({tete:['CH. 8 · EFFONDREMENT','[SIGNAL PERDU]'],html:'<div class="txt"><p class="rg">ARIA &gt; …</p><p class="petit">Plus de voix. Plus de consigne. Pour la première fois, personne ne te dit quoi faire.</p></div>',
  boutons:[{t:'CONTINUER SEUL',c:'blanc',f(){prof.ch=Math.max(prof.ch,9);sauve();note_('Chapitre 8 terminé. Perte de contrôle.');lance(9)}},{t:'MENU',c:'creux mince',f:menu}]})}
CH[8]={async prep(etape){for(const n of[1,2,3])if(!CH[n].pret){await CH[n].prep(etape);CH[n].pret=true}
   Object.assign(N8c,N2,{hud:null,objets:[],maj(dt){S.orbT-=dt;if(S.orbT<=0){S.orbT=.7+rnd()*.6;const g=rnd()<.5;S.orbes.push({x:g?S.cam.x-20:S.cam.x+W+20,y:S.j.y-10-rnd()*60,vx:g?170:-170})}for(const o of S.orbes){o.x+=o.vx*dt;if(Math.abs(o.x-S.j.x)<12&&o.y>S.j.y-JH&&o.y<S.j.y)coteDegat()}S.orbes=S.orbes.filter(o=>o.x>S.cam.x-60&&o.x<S.cam.x+W+60);if(S.vies<2)S.vies=2},dessineApres:N5.dessineApres||((cmx,cmy)=>{for(const o of S.orbes){const s=SP.balle[1][(S.t*9|0)&1];cx.drawImage(s,R(o.x-cmx-9),R(o.y-cmy-9))}})});
   Object.assign(N8r,N3,{avantKo:null,surKo:null,maj(){if(S.j.pv<3)S.j.pv=3}})},
 debut(o){segment8(Math.min(SEG8.length-1,o.t|0))},
 maj(dt){if(C8.mode==='tir')maj1(dt);else if(C8.mode==='cote')coteMaj(dt);else rueMaj(dt);if(S&&!S.fini&&S.t>C8.dur)segment8(C8.seg+1)},
 dessine(){if(C8.mode==='tir')dessine1();else if(C8.mode==='cote')coteDessine();else rueDessine();
   if(C8.miroir){cx.save();cx.translate(W,0);cx.scale(-1,1);cx.drawImage(cv,0,0);cx.restore()}
   if(rnd()<.12+C8.seg*.02)glitch(1.4);const a=Math.min(.9,Math.max(0,(C8.seg-8)*.22));if(a>0){cx.fillStyle='rgba(0,0,0,'+a*(.5+.5*Math.sin(S.t*5))+')';cx.fillRect(0,0,W,H)}
   if(Math.floor(S.t*3)%5===0){cx.font='bold 14px monospace';cx.fillStyle='#E5283C';cx.fillText(['OBÉIS','LIS','FRAPPE','SAUTE','TIRE','ARRÊTE'][Math.floor(S.t*3/5+C8.seg)%6],30+(C8.seg*53)%200,H*.3+(C8.seg*91)%200)}},
 hud(){if(C8.mode==='tir')hud1();else if(C8.mode==='cote')coteHud();else{viesHud(Math.ceil(S.j.pv/2));$('score').textContent=String(S.tues).padStart(3,'0')}viesHud(Math.floor(rnd()*4));$('hdt').textContent='CH. '+['8','1','3','2','?','8'][Math.floor(S.t*2)%6]+' · '+['EFFONDREMENT','INITIALISATION','CONFRONTATION','RECONNAISSANCE','ERREUR','EFFONDREMENT'][Math.floor(S.t*2)%6]},
 act(){if(C8.mode==='tir')purge();else if(C8.mode==='cote')coteAct();else rueAttaque()},
 bas(x,y){if(C8.mode==='tir')CH[1].bas(x,y);else if(C8.mode==='cote')cmdBas(x,y);else CH[3].bas(x,y)},
 bouge(x,y){if(C8.mode==='tir')CH[1].bouge(x,y);else if(C8.mode==='cote')cmdBouge(x,y);else CH[3].bouge(x,y)},
 haut(x,y,d){if(C8.mode==='cote')cmdHaut();else if(C8.mode==='rue')CH[3].haut(x,y,d)},
 touche(k){if(C8.mode==='tir')CH[1].touche(k);else if(C8.mode==='rue')CH[3].touche(k)},
 etat(){return 'seg '+C8.seg+' '+C8.mode+(S.fini?' FINI':'')}};
