// ================================================================ DÉMARRAGE et essais automatiques (?ch=N&t=..&sim=secondes&auto=1, ?planche=paris)
requestAnimationFrame(boucle);
if(Q.get('planche')==='paris'){(async()=>{const k=Q.get('k')||'seine',c=paris(k==='h'?'h':k,+(Q.get('g')||5));c.style.cssText='position:fixed;left:0;top:0;z-index:99;width:'+(Q.get('z')||720)+'px;image-rendering:pixelated';document.body.append(c);scrollTo(0,0);c.style.top=(-(+Q.get('y')||0))+'px';document.title='ok'})()}
else if(Q.get("essai")==="acces"){(async()=>{const r=[];for(const[n,N]of[[2,N2],[4,N4],[7,N7],[9,N9]]){await lance(n);for(const o of N.objets)if(o.k==="porte")for(let q=0;q<o.h;q++)N.G.g[o.y+q][o.x]=".";r.push(n+":"+(accessible(N).join(" ")||"tout accessible"))}document.title="ACCES "+r.join(" | ")})()}
else if(Q.get("essai")==="bot"){(async()=>{const n=+Q.get("n")||2;await lance(n,{x:Q.get("x")});const N=S.N;let mx=0;for(let i=0;i<60*70&&S&&!S.fini;i++){const j=S.j;KB.ArrowRight=1;const dev=solide(N,j.x+JL+10,j.y-4)||(!solide(N,j.x+30,j.y+6)&&N.G.get(Math.floor((j.x+30)/TU),Math.floor((j.y+6)/TU))!=="=");KB[" "]=j.sol&&dev&&i%3===0?1:0;if(!S.pause&&!S.dialogue)CHAP.maj(1/60);else S.pause=false;mx=Math.max(mx,j.x/TU)}document.title="BOT ch"+n+" xmax "+mx.toFixed(1)+" vies "+(S?S.vies:"-")})()}
else if(Q.get("essai")){}
else if(Q.get("ch")){const n=+Q.get('ch');lance(n,{t:parseFloat(Q.get('t'))||0,x:Q.get('x')}).then(()=>{const sim=parseFloat(Q.get('sim'))||0;for(let i=0;i<sim*60&&S&&!S.fini;i++){if(!S.pause&&!S.dialogue)CHAP.maj(1/60)}if(S&&CHAP){CHAP.hud&&CHAP.hud();document.title+=' | '+(CHAP.etat?CHAP.etat():'ok')}})}
else menu();
// essai de bout en bout des écrans et des dialogues : ?essai=1 (résultat dans le titre de la page)
if(Q.get('essai'))(async()=>{const att=ms=>new Promise(r=>setTimeout(r,ms)),vu=[];
  const clic=async i=>{const b=$('page').querySelectorAll('button')[i||0];if(!$('page').classList.contains('vu')||!b)throw new Error('bouton absent ('+vu.join(',')+')');b.click();await att(80)};
  const dial=async c=>{await att(60);for(let n=0;n<400&&$('scene').classList.contains('vu');n++){const bs=$('scb').querySelectorAll('button');if(bs.length)bs[Math.min(c,bs.length-1)].click();else $('scene').dispatchEvent(new Event('pointerdown'));await att(30)}};
  const tourne=s=>{for(let i=0;i<s*60&&S&&!S.fini;i++)if(!S.pause&&!S.dialogue)CHAP.maj(1/60)};
  const titre=()=>($('page').querySelector('.titre')||{}).textContent;
  try{prof={};profDefaut();prof.prenom='Tony';prof.vu=1;
    await lance(1);fin1();vu.push('1:'+titre());
    await lance(2);document2();await clic(0);await clic(0);await clic(0);fin2();tourne(4);vu.push('2:'+titre()+' f'+prof.frag.length);
    await lance(3);S.vague=4;S.verrou=N3.vagues[4];const e=rueEnnemi('civil4',200,660);ch3Dernier(e);await dial(0);await clic(0);vu.push('3:'+titre()+' f'+prof.frag.length);
    await clic(0);vu.push('acte:'+titre());
    await lance(4);S.inv.eau=true;haddad();await dial(0);vu.push('4:'+titre()+' f'+prof.frag.length);
    await lance(5);segment5(3);S.proche=N5.o3[2];coteAct();tourne(5);fin5();vu.push('5:'+titre()+' f'+prof.frag.length);
    await lance(6);pause6(2);await dial(0);N6.vagues[3].fin();await dial(0);vu.push('6:'+titre()+' f'+prof.frag.length);
    await lance(7);photo7();await dial(1);await clic(0);vu.push('7:'+titre()+' f'+prof.frag.length);
    await lance(8);fin8();vu.push('8:ok');
    await lance(9);for(let i=1;i<=5;i++){N9.objets[i].f();await clic(0)}S.proche=N9.objets[7];N9.objets[7].f();await clic(0);tourne(4);vu.push('9:'+titre()+' f'+prof.frag.length+' porte'+(S&&S.ouvert));
    for(const c of[0,1,2,3]){await lance(10);await att(2000);await dial(c);await att(4600);vu.push('fin:'+$('page').querySelector('.tete').textContent);try{await clic(0)}catch(_){}}
    await lance(10);await att(2000);for(let n=0;n<60&&!SCN.attendChoix;n++){$('scene').dispatchEvent(new Event('pointerdown'));await att(40)}for(let i=0;i<300;i++)CHAP.majPause(.25);await att(1800);vu.push('fin:'+$('page').querySelector('.tete').textContent);
    document.title='ESSAI OK '+vu.join(' | ')+' fins '+prof.fins.join('')+' ngp '+prof.ngp}catch(err){document.title='ESSAI ERREUR '+err.message+' :: '+vu.join(' | ')}})();
