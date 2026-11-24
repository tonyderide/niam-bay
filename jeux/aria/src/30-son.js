// ================================================================ SON : effets et musiques synthétisés (aucun fichier audio)
let ac=null,son=!Q.get('muet'),bruit=null,ambiance='mil',sortie=null;
function note(type,f,t,d,v,f2){const o=ac.createOscillator(),g=ac.createGain();o.type=type;o.frequency.setValueAtTime(f,t);if(f2)o.frequency.exponentialRampToValueAtTime(f2,t+d);g.gain.setValueAtTime(v,t);g.gain.exponentialRampToValueAtTime(.0001,t+d);o.connect(g).connect(sortie);o.start(t);o.stop(t+d+.02)}
function souffle(t,d,v,freq,type){const s=ac.createBufferSource(),g=ac.createGain(),f=ac.createBiquadFilter();s.buffer=bruit;f.type=type||'lowpass';f.frequency.setValueAtTime(freq,t);if(!type)f.frequency.exponentialRampToValueAtTime(80,t+d);g.gain.setValueAtTime(v,t);g.gain.exponentialRampToValueAtTime(.0001,t+d);s.connect(f).connect(g).connect(sortie);s.start(t);s.stop(t+d+.02)}
// piano : fondamentale + harmoniques à décroissance lente
function piano(m,t,v,d){const f=440*Math.pow(2,(m-69)/12);d=d||2.6;note('triangle',f,t,d,v);note('sine',f*2,t,d*.6,v*.35);note('sine',f*3,t,d*.3,v*.12);souffle(t,.02,v*.3,3000,'highpass')}
const ok=()=>ac&&son&&ac.state==='running';
const N=()=>ac.currentTime;
const sfx={
  boum(g){if(ok()){souffle(N(),.25+g*.5,.10+g*.12,900+g*1500);if(g>.5)note('sine',110,N(),.5,.2,35)}},
  prise(){if(ok())note('square',880,N(),.07,.03,1500)},
  module(){if(ok()){note('square',523,N(),.1,.05);note('square',784,N()+.09,.1,.05);note('square',1047,N()+.18,.18,.05)}},
  frag(){if(ok()){note('sine',660,N(),.5,.08);note('sine',990,N()+.12,.6,.07);note('sine',1320,N()+.24,.9,.06)}},
  cri(){if(ok()){note('sawtooth',760,N(),.45,.1,260);note('square',1500,N(),.4,.04,420);souffle(N()+.42,.12,.25,6000,'highpass')}},
  touche(){if(ok()){souffle(N(),.6,.3,2500);note('sawtooth',300,N(),.6,.12,40)}},
  purge(){if(ok()){souffle(N(),1,.3,5000);note('sine',900,N(),.9,.12,60)}},
  alarme(){if(ok())for(let i=0;i<6;i++)note('sawtooth',520,N()+i*.5,.3,.07,700)},
  saut(){if(ok())note('square',240,N(),.12,.04,480)},
  pas(){if(ok())souffle(N(),.05,.05,500+rnd()*300)},
  chute(){if(ok()){souffle(N(),.12,.14,700);note('sine',90,N(),.12,.12,50)}},
  coup(f){if(ok()){souffle(N(),.09,.22+.1*(f||0),1600+900*(f||0));note('sine',160,N(),.1,.18,60)}},
  vent(){if(ok())souffle(N(),.12,.06,4000,'highpass')},
  porte(){if(ok()){note('sawtooth',70,N(),.5,.08,50);souffle(N(),.5,.08,900)}},
  bip(){if(ok())note('sine',1200,N(),.08,.05)},
  tic(q){if(ok())note(q==='h'?'triangle':'square',q==='h'?220+rnd()*60:q==='g'?90:660,N(),.025,q==='h'?.03:.012)},
  gl(){if(ok()){souffle(N(),.18,.2,7000,'highpass');note('sawtooth',55,N(),.2,.12,880)}},
  elec(){if(ok()){souffle(N(),.25,.16,8000,'highpass');note('square',50,N(),.25,.06)}},
  coeur(){if(ok()){note('sine',60,N(),.14,.25,40);note('sine',55,N()+.22,.14,.18,38)}}};
const hz=m=>440*Math.pow(2,(m-69)/12);
function demarreSon(){if(ac){try{ac.resume()}catch(e){}return}
  try{ac=new (window.AudioContext||window.webkitAudioContext)();sortie=ac.createGain();sortie.gain.value=.9;sortie.connect(ac.destination);ac.resume();bruit=ac.createBuffer(1,ac.sampleRate,ac.sampleRate);const d=bruit.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=rnd()*2-1}catch(e){ac=null;return}
  let pas=0,suiv=ac.currentTime+.1;
  const PIANO=[[57,64,72],[53,60,69],[48,55,64],[55,62,71],[57,64,72],[53,60,69],[50,57,65],[52,59,68]];
  setInterval(()=>{if(!ok()||!S||S.pause||S.fini||S.silence){suiv=ac?ac.currentTime+.1:0;return}
    while(suiv<ac.currentTime+.2){const a=S.amb||ambiance,k=pas%16;
      if(a==='mil'){const boss=!!S.boss,d=60/(boss?168:146)/4,r=[45,45,41,43,45,45,48,43][(pas>>4)%8]+(boss?1:0);
        if(k%2===0)note('sawtooth',hz(r-12),suiv,d*1.7,.05);note('square',hz(r+12+[0,7,12,15,19,15,12,7][pas%8]),suiv,d*.9,.012);
        if(k%4===0)note('sine',130,suiv,.12,.16,40);if(k%8===4)souffle(suiv,.12,.05,3000,'highpass');if(k%2===1)souffle(suiv,.03,.014,7000,'highpass');
        if(boss&&k%4===2)note('square',hz(r+24),suiv,d,.012);suiv+=d}
      else if(a==='calme'){const d=60/92/4,r=[45,45,41,43][(pas>>4)%4];if(k===0)note('sawtooth',hz(r-12),suiv,d*14,.035);if(k%4===0)note('sine',hz(r+12+[0,7,3,10][(pas>>2)%4]),suiv,d*3.5,.03);if(k%8===0)note('sine',110,suiv,.14,.1,40);if(k%4===2)souffle(suiv,.04,.012,7000,'highpass');suiv+=d}
      else if(a==='rue'){const d=60/128/4,r=[40,40,43,38][(pas>>4)%4];if(k%2===0)note('sawtooth',hz(r),suiv,d*1.6,.06);if(k%4===0)note('sine',120,suiv,.14,.2,38);if(k%8===4){souffle(suiv,.14,.07,2600,'highpass')}if(k%2===1)souffle(suiv,.03,.016,7000,'highpass');if(k%16===6||k%16===13)note('square',hz(r+24+[0,3,7][pas%3]),suiv,d*1.5,.016);suiv+=d}
      else if(a==='dis'){const d=60/84/4,r=[45,46,41,44][(pas>>4)%4];if(k===0){note('sawtooth',hz(r-12),suiv,d*15,.035);note('sawtooth',hz(r-12)*1.012,suiv,d*15,.03)}if(k%4===0)note('sine',hz(r+12+[0,6,1,11][(pas>>2)%4]),suiv,d*4,.028);if(k%8===0)note('sine',100,suiv,.16,.1,36);if(rnd()<.06){souffle(suiv,.05,.05,9000,'highpass');note('square',hz(80+((rnd()*12)|0)),suiv,.04,.012)}suiv+=d}
      else if(a==='srv'){const d=.5;if(k%8===0)souffle(suiv,3.8,.035,220);if(rnd()<.25)note('sine',hz(84+((rnd()*10)|0)),suiv,.05,.012);if(rnd()<.1)souffle(suiv,.3,.03,5000,'highpass');if(k===0)note('sine',52,suiv,7,.05);suiv+=d}
      else if(a==='piano'){const d=.62,c=PIANO[(pas>>3)%8],q=pas%8;if(q===0)piano(c[0]-12,suiv,.09,4.4);if(q===2)piano(c[1],suiv,.05);if(q===4)piano(c[2],suiv,.06);if(q===6)piano(c[1],suiv,.04);if(q===7&&(pas>>3)%2)piano(c[2]+2,suiv,.035);suiv+=d}
      else suiv+=.25;
      pas++}},50)}
