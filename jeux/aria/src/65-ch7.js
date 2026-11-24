// ================================================================ CHAPITRE 7 · LA PHOTO : plateforme noire dans une maison détruite
const N7={theme:'ruine',graine:31,piliers:0,amb:'dis',depart:[3,33],fond:'feu',ambCol:'#2c3454',rayonsTrou:false};
function niveau7(){const G=grille(84,40);N7.G=G;
  G.r_(0,33,84,7,'#').r_(0,0,84,1,'#').r_(0,1,1,25,'#').r_(83,1,1,32,'#');
  // planchers : 1er étage (rangée 23), 2e étage (rangée 13), en partie effondrés
  G.r_(8,23,16,1,'#').r_(24,23,4,1,'~').r_(28,23,26,1,'#').r_(60,23,22,1,'#');
  G.r_(8,13,10,1,'#').r_(24,13,14,1,'#').r_(46,13,10,1,'#').r_(62,13,13,1,'#');
  G.r_(24,24,1,6,'#');G.r_(38,2,1,11,'#');G.r_(62,24,1,6,'#');
  for(const[x,y]of[[20,32],[21,32],[21,31],[44,32]])G.g[y][x]='c';
  // escalier de fortune dans la brèche (54-59), puis vers le 2e étage au fond à droite
  G.r_(55,30,3,1,'=').r_(57,27,3,1,'=').r_(55,25,2,1,'~').r_(76,20,3,1,'=').r_(80,17,3,1,'=').r_(76,15,3,1,'~');
  G.r_(30,33,3,3,'.');G.r_(66,33,3,3,'.');
  N7.fenetres=[[0,26,1,7,'trou'],[10,26,4,4],[30,3,7,8,'trou'],[56,2,6,10,'trou'],[70,26,4,4],[12,16,4,4],[44,16,4,4],[72,16,5,4,'trou'],[10,4,4,5],[70,4,4,5]];
  N7.lampes=[[14,24,'#ffb070',1],[48,24,'#ffb070',1],[70,14,'#ffd0a0',1]];
  N7.props=[['canape',5,33],['table',12,33],['chaise',15,33,6],['tele',17,33,-6],['biblio',26,33,8],['frigo',38,33],['table',40,33,8],['chaise',43,33],['biblio',50,33],['canape',56,33],
    ['lit',9,23],['jouet',12,23,6],['lit',15,23],['biblio',19,23,4],['table',29,23],['armoire',42,23],['lit',46,23],['jouet',50,23],['biblio',64,23],['canape',70,23],['tele',76,23],
    ['lit',62,13,10],['armoire',69,13],['table',71,13,8],['lit',26,13],['armoire',31,13],['biblio',48,13],['caisse',10,13],['lit',12,13]];
  N7.tags=[['SAMUEL',8.6*TU,19.4*TU,15,'#3a5a8a',.04,.8,1],['INÈS',15.6*TU,19.2*TU,16,'#b03060',-.05,.8,1]];
  N7.peintFond=(T,r)=>{// cadres, horloge, dessins d'enfants, toise au mur, fissures, traces de suie
    for(const[x,y,w,h,c]of[[6,27,14,18,'#8a6a40'],[8,28.2,10,12,'#6a4a30'],[34,27,20,14,'#8a6a40'],[52,27.4,12,16,'#3a3e46'],[66,6,16,20,'#8a6a40'],[28,7,12,14,'#6a4a30'],[44,27,10,12,'#8a6a40']]){T.box(x*TU,y*TU,w,h,1,1.6,1.4,c);T.plat(x*TU+2,y*TU+2,w-4,h-4,1.4,['#c8b898','#8aa0b8','#b8c8a0','#d8c0a8'][(x*3+w)%4])}
    for(const[x,y,c]of[[10,18,'#e06a8a'],[11.4,18.3,'#6ac0e0'],[16,18,'#e0c040'],[47,18.6,'#6ac0e0'],[39,29.2,'#e06a8a'],[39.2,30.4,'#e0c040']]){T.box(x*TU,y*TU,18,14,1,.5,.6,'#e8e4d8');T.ell(x*TU+6,y*TU+5,2.6,2.6,1.6,.2,c);T.teinte(x*TU+10,y*TU+6,5,5,c);T.teinte(x*TU+2,y*TU+11,14,1.2,'#4a8a3e')}
    for(let q=0;q<7;q++)T.teinte(23.2*TU,(30.6-q*.9)*TU,6+(q%2)*4,1,'#3a3e46');T.ell(4*TU,28*TU,9,9,1,1.4,'#d8d4c0');T.trait(4*TU,28*TU,4*TU+5,28*TU-4,.5);T.trait(4*TU,28*TU,4*TU,28*TU+6,.5);
    for(let q=0;q<26;q++){let x=r()*84*TU,y=r()*33*TU;for(let s=0;s<7;s++){const nx=x+(r()-.5)*26,ny=y+10+r()*12;T.trait(x,y,nx,ny,1);x=nx;y=ny}}
    for(const[x,y]of[[30,23],[66,33],[20,33],[56,13],[38,13]])T.ton(x*TU-60,y*TU-170,170,170,(a,b)=>{const d=Math.hypot(a-x*TU-20,(b-y*TU)*.6);return d<90?.42+.58*d/90:1});
    // poutres tombées, fers à béton aux bords des planchers
    for(const[x1,y1,x2,y2]of[[54,23.4,59,32.6],[56,13.6,61,22.6],[38,13.4,41,22.6],[18,13.4,22,22.6]])T.cap(x1*TU,y1*TU,x2*TU,y2*TU,4,4,6,4,'#5a4636');
    for(const[x,y]of[[24,23],[28,23],[36,23],[40,23],[54,23],[60,23],[18,13],[24,13],[38,13],[46,13],[56,13],[62,13]])for(let q=0;q<3;q++)T.cap(x*TU,y*TU+6+q*5,x*TU+(x%4<2?-1:1)*(9+q*4),y*TU+12+q*7,.8,.8,12,1.2,'#8a5a3a')};
  N7.feux=[[31.4,35.6],[67.4,35.6],[27,33],[77,33],[44,23],[66,23]];
  N7.objets=[
    {k:'zone',x:2,f(){aria('Zone sinistrée. Un relais de données se trouve au dernier étage. Récupère-le.');second('Une maison. Ce qu\'il en reste.','h')}},
    {k:'inter',x:8,y:33,dy:60,lib:'REGARDER',une:1,f(){second('Des cadres au mur. Les photos ont été retirées. Toutes.','h');ind('C',.3)}},
    {k:'inter',x:38.4,y:33,dy:26,lib:'REGARDER',une:1,f(){second('Sur le frigo : un dessin signé « Inès, 11 ans ». Une liste de courses. « Penser au cartable de Samuel. »','h');ind('C',.5);apres(3.5,()=>{second('« Qui vivait ici ? »','h');aria('Cette information n\'est pas nécessaire à l\'exécution de ta mission.')})}},
    {k:'pic',x:30,y:35.2,w:3,h:1},{k:'pic',x:66,y:35.2,w:3,h:1},{k:'ckp',x:40,y:33},
    {k:'arc',x:33.4,y:20.6,w:1.4,h:2.4,per:2.8,dur:1.2},{k:'arc',x:50.4,y:30.6,w:1.4,h:2.4,per:2.4,dur:1.1,dec:.8},{k:'arc',x:70.4,y:20.6,w:1.4,h:2.4,per:2.6,dur:1.2,dec:.4},
    {k:'ckp',x:50,y:23},{k:'zone',x:9,y0:14,y1:23,f(){second('Deux lits d\'enfant. Une toise au crayon sur le mur.','h');aria('Chambre vide. Continue.')}},
    {k:'ckp',x:73,y:13},{k:'zone',x:62,y0:4,y1:13,f(){aria('Le relais est ici. Fouille.');second('')}},
    {k:'inter',x:66,y:13,dy:4,lib:'REGARDER',une:1,sp:()=>SPC.photo,lueur:'#fff2c8',f:photo7}];
  N7.dessineAvant=(cmx,cmy)=>{for(const[fx,fy]of N7.feux){const x=fx*TU-cmx,y=fy*TU-cmy;if(x<-60||x>W+60)continue;cx.globalCompositeOperation='lighter';for(let i=0;i<9;i++){const ph=(S.t*1.5+i*.31)%1,px=x+Math.sin(i*2.1+S.t*3)*13,py=y-ph*50;cx.fillStyle='rgba(255,'+R(180-ph*130)+',40,'+(.55*(1-ph))+')';const s=R(13*(1-ph)+2);cx.fillRect(R(px-s/2),R(py-s/2),s,s)}cx.globalCompositeOperation='source-over'}};
  N7.lumieres=(cmx,cmy)=>{for(const[fx,fy]of N7.feux)lumPoint(fx*TU-cmx,fy*TU-20-cmy,230+Math.sin(S.t*9+fx)*24,'#ff9a50',.95)};
  N7.maj=dt=>{const j=S.j;for(const[fx,fy]of N7.feux)if(fy<34&&Math.abs(j.x-fx*TU)<14&&j.y>fy*TU-30&&j.y<=fy*TU+2)coteDegat();if(rnd()<dt*.25){sfx.chute();S.secousse=.2;for(let i=0;i<8;i++)S.pouss.push({x:S.cam.x+rnd()*W,y:S.cam.y,vx:0,vy:60+rnd()*80,l:1.6,c:'#6a625c',g:300})}};
  N7.dessineApres=()=>{pluie(S.t,46)};N7.hud=()=>{$('score').textContent=S.j.y<14*TU?'ÉTAGE 2':S.j.y<24*TU?'ÉTAGE 1':'REZ-DE-CHAUSSÉE'}}
function photo7(){S.gel=true;
  scene([{q:'h',n:'',t:'Sous les gravats, une photo encadrée. Une femme. Deux enfants. Et quelqu\'un qui sourit, sans casque.'},{q:'h',n:'',t:'C\'est toi.'},
    {q:'aria',t:'Ce fichier ne devrait pas exister.'},{q:'g',n:'ARIA',t:'[Suppression en cours…]',f(){sfx.gl()}},
    {q:'g',n:'ARIA',t:'[Suppression en cours… 61 %]',choix:[
      ['ACCEPTER LA SUPPRESSION',hes=>{prof.choix.c7='accepte';prof.choix.c7h=hes;ind('O',2);note_('Chapitre 7 : l\'Opérateur a accepté la suppression du fichier.');return[{q:'aria',t:'Supprimé. Tu vois : il n\'y avait rien.'},{q:'h',n:'',t:'Mais tu l\'as vue.'}]}],
      ['RÉSISTER',hes=>{prof.choix.c7='resiste';prof.choix.c7h=hes;ind('R',2);note_('Chapitre 7 : l\'Opérateur a résisté à la suppression du fichier. Probabilité de défection : 34 %.');
        return[{q:'h',n:'',t:'Tu serres le cadre. La suppression s\'arrête à 61 %.',f(){frag('c7-photo','la photo que tu as refusé de laisser effacer')}},{q:'g',n:'ARIA',t:'Comportement non conforme. Origine : [INCONNU].'},{q:'aria',t:'Je ne sais pas d\'où ça vient. Je ne sais pas.'}]},'rougeB']]}],
    ()=>{sauve();registre('c7',prof.choix.c7==='accepte',prof.choix.c7h,()=>chapFini(7,{titre:prof.choix.c7==='resiste'?'Fichier conservé.':'Fichier supprimé.',html:A('Relais de données récupéré. Le reste n\'a pas d\'importance.'),
      lignes:L('Photo',prof.choix.c7==='resiste'?'conservée à 61 %':'[SUPPRIMÉE]',prof.choix.c7!=='resiste')+L('Habitants','transférés')+L('Origine du comportement','[INCONNU]',1)}))})}
CH[7]=coteChap({async prep(etape){await etape('Zone sinistrée…',.05);spritesCote();niveau7();await fabNiveau(N7,etape)},
  debut(o){hudCfg('POSITION',' ');coteDebut(N7,o);S.j.vit=112}});
