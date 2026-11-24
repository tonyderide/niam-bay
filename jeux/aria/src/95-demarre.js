// ================================================================ DÉMARRAGE et essais automatiques (?ch=N&t=..&sim=secondes&auto=1, ?planche=paris)
requestAnimationFrame(boucle);
if(Q.get('planche')==='paris'){(async()=>{const k=Q.get('k')||'seine',c=paris(k==='h'?'h':k,+(Q.get('g')||5));c.style.cssText='position:fixed;left:0;top:0;z-index:99;width:'+(Q.get('z')||720)+'px;image-rendering:pixelated';document.body.append(c);scrollTo(0,0);c.style.top=(-(+Q.get('y')||0))+'px';document.title='ok'})()}
else if(Q.get('ch')){const n=+Q.get('ch');lance(n,{t:parseFloat(Q.get('t'))||0,x:Q.get('x')}).then(()=>{const sim=parseFloat(Q.get('sim'))||0;for(let i=0;i<sim*60&&S&&!S.fini;i++){if(!S.pause&&!S.dialogue)CHAP.maj(1/60)}if(S&&CHAP){CHAP.hud&&CHAP.hud();document.title+=' | '+(CHAP.etat?CHAP.etat():'ok')}})}
else menu();
