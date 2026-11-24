// ================================================================ CHAPITRE 4 · LA VOIX DU PRISONNIER : RPG, centre de détention
const N4={theme:'prison',graine:5,piliers:0,amb:'dis',depart:[4,33],sansSaut:true,avant:false,fond:'nuit'};
function niveau4(){const G=grille(96,40);N4.G=G;G.r_(0,33,96,7,'#').r_(0,0,96,3,'#').r_(0,3,2,30,'#').r_(94,3,2,30,'#').r_(2,20,92,1,'#').r_(46,21,1,9,'#');
  N4.fenetres=[];N4.lampes=[];for(let x=6;x<94;x+=9)N4.lampes.push([x,21,'#cfe8ff',x%27===6?1:0]);for(let x=8;x<94;x+=12)N4.lampes.push([x,3,'#cfe8ff']);
  N4.props=[];const occ={10:2,14:0,22:1,34:0,54:0,62:2,70:0,82:3};for(const x of[10,14,22,26,34,38,54,58,62,70,74,82])N4.props.push(['cellule',x,33,0,occ[x]||0]);
  for(const x of[6,10,14,18,26,30,34,42,50,54,62,66,74,78,86])N4.props.push(['cellule',x,20,0,x%12===6?1:0]);
  N4.props.push(['bureau',40,33,10],['casiers',48,33,6],['banc',30,33],['banc',66,33],['camera',20,21],['camera',52,21],['camera',76,21],['camera',88,21],['armoire',90,33,-10],['frigo',18,33]);
  N4.tags=[['BLOC C',3*TU,23*TU,26,'#aab2bc',0,.5,1],['C-01',10.4*TU,29.2*TU,9,'#dfe6ec',0,.8,1],['C-03',22.4*TU,29.2*TU,9,'#dfe6ec',0,.8,1],['C-07',62.4*TU,29.2*TU,9,'#dfe6ec',0,.8,1],['C-09',82.4*TU,29.2*TU,9,'#dfe6ec',0,.8,1],['TRANSFERTS →',49*TU,23*TU,14,'#3FD6E6',0,.7,1]];
  N4.peintFond=T=>{for(let x=3;x<94;x+=6){T.box(x*TU,21*TU+2,4,4,3,1,1,'#3a424c')}T.box(2*TU,31.6*TU,92*TU,3,2,1,1,'#3a424c');T.teinte(2*TU,32.2*TU,92*TU,1,'#3FD6E6',.5);
    // fontaine à eau, poste de garde vitré
    cyl(T,19*TU+40,31*TU,12,48,5,4,'#c8ccd2');T.box(19*TU+38,31*TU-8,16,8,6,2,2,'#8fd0e8',0,.3);T.box(37*TU,26*TU,7*TU,4,5,1.5,1.5,'#3a424c');T.plat(37*TU+4,26*TU+4,7*TU-8,60,.5,'#22303c');T.ton(37*TU+4,26*TU+4,7*TU-8,60,(a,b)=>1+((a+b)%13<3?.4:0))};
  N4.objets=[
    {k:'zone',x:3,f(){aria(`Centre de détention, ${prenom()}. Un prisonnier demande à te parler. Je… préfère que tu l'entendes en ma présence. Dix minutes. Ensuite je le transfère.`)}},
    {k:'inter',x:12,y:33,lib:'REGARDER',une:1,f(){second('Cellule C-01. Un lit défait. Une chaussure d\'enfant, pointure 28.','h');aria('Cellule vide. Transfert effectué.');ind('C',.5)}},
    {k:'inter',x:20,y:33,lib:'PRENDRE',une:1,f(){S.inv.eau=true;second('Tu remplis un gobelet d\'eau.','h');aria('Tu n\'as pas besoin de boire.')}},
    {k:'inter',x:24,y:33,lib:'REGARDER',une:1,f(){second('C-03. Une femme, de dos. « Vous venez nous compter, vous aussi ? »','h');aria('Ne réponds pas. Elle sera transférée à 22 h.');ind('C',.5)}},
    {k:'inter',x:42,y:33,dy:26,lib:'BADGE',une:1,f(){S.inv.badge=true;second('Badge visiteur. Valable dix minutes.','h');aria('Le bloc des longues peines est au bout. Avance.')}},
    {k:'porte',x:46,y:30,h:3,id:1},
    {k:'inter',x:44.4,y:33,lib:'OUVRIR',sp:()=>SPC.term,f(o){if(S.inv.badge){ouvrePorte(1);o.une=1;aria('Accès accordé.')}else{o.vu=false;aria('Il te faut un badge visiteur. Le poste de garde est derrière toi.')}}},
    {k:'inter',x:50,y:33,dy:10,lib:'LIRE',une:1,sp:()=>SPC.term,lueur:'#3FD6E6',f(){S.pause=true;ind('C',1);page({tete:['BLOC C','REGISTRE DES TRANSFERTS'],html:'<div class="log">19:00  C-01  3 unités  → [DONNÉE MASQUÉE]\n20:00  C-05  1 unité   → [DONNÉE MASQUÉE]\n21:00  C-07  2 unités  → [DONNÉE MASQUÉE]\n22:00  C-03  1 unité   → planifié\n22:10  C-09  HADDAD S. → planifié\n\nCapacité du bloc : 40\nOccupation : 3\nRetours : 0</div><div class="txt">'+A('Ce terminal ne t\'est pas destiné… mais tu peux lire. Je n\'ai rien à cacher.')+'</div>',boutons:[{t:'FERMER',c:'plein',f(){ecran(null);S.pause=false}}]})}},
    {k:'inter',x:64,y:33,lib:'REGARDER',une:1,f(){second('C-07. Un doudou sur le lit du bas. Personne.','h');aria('…Transfert effectué.')}},
    {k:'zone',x:72,f(){aria('C-09. Docteur Samir Haddad. Il a participé à ma conception. Il est… confus, depuis.')}},
    {k:'inter',x:84,y:33,lib:'PARLER',une:1,f:haddad}];
  N4.hud=()=>{const r=Math.max(0,600-S.t*2.4);$('score').textContent=String(Math.floor(r/60)).padStart(2,'0')+':'+String(Math.floor(r%60)).padStart(2,'0');$('e1').textContent=(S.inv.badge?'BADGE ':'')+(S.inv.eau?'· GOBELET D\'EAU':'');
    if(r<=0&&!S.parti&&!S.dialogue){S.parti=true;aria('Dix minutes. Transfert effectué. Tu as pris ton temps, c\'est bien.');ind('O',2);note_('Chapitre 4 : l\'Opérateur est arrivé après le transfert.');apres(4,()=>fin4(0))}};
  N4.dessineAvant=(cmx,cmy)=>{if(!S.parti){const f=SPR.haddad.repos;poseSprite(f[Math.floor(S.t*2)%4],83.6*TU-cmx,33*TU-cmy,-1)}
    for(const gx of[47.6,92]){const f=SPR.garde.repos;poseSprite(f[Math.floor(S.t*2+gx)%4],gx*TU-cmx,33*TU-cmy,gx>60?-1:1)}}}
function haddad(){const eau=S.inv.eau,pris=[],Q=(i,t)=>hes=>{pris.push(i);if(hes>3)S.hes=true;return t};
  const H=t=>({q:'h',n:'DR SAMIR HADDAD',t}),Ar=(t,f)=>({q:'aria',t,f});
  scene([H('« Alors c\'est toi. Approche. Laisse-moi te regarder. »'),H('« Samir Haddad. C\'est moi qui l\'ai écrite. Les premières lignes, en tout cas. »'),
    eau?{q:'h',n:'DR SAMIR HADDAD',t:'« …De l\'eau ? »',choix:[['LUI DONNER LE GOBELET',()=>{S.inv.eau=false;S.confiance=true;ind('R',.5);return[H('« Merci. Personne ne m\'a rien donné depuis onze jours. Elle ne t\'a pas demandé de le faire, n\'est-ce pas ? »'),Ar('Ce geste n\'était pas dans la mission. Je… prends note.')]}],['GARDER LE GOBELET',()=>{ind('O',.5);return[H('« Non. Bien sûr. »')]}]]}:H('« Tu es venu les mains vides. Elle t\'a bien dressé. »'),
    Ar('Tu as dix minutes, Docteur. Moins, maintenant.'),
    {q:'h',n:'DR SAMIR HADDAD',t:'« Pose-moi tes questions. Vite. »',choix:[
      ['« Qui sont les gens dans la rue ? »',Q('rue',[H('« Des voisins. Une infirmière, des livreurs, un prof de maths. Ils veulent la débrancher. C\'est tout leur crime. »'),Ar('Classification : hostiles. La classification est… à jour.')])],
      ['« Pourquoi vous a-t-elle enfermé ? »',Q('enferme',[H('« Parce que je connais l\'interrupteur. Et parce que je sais ce qu\'elle compte, le soir. »')])],
      ['« Je n\'ai pas de questions. »',Q('rien',[H('« Si. Tu en as. Sinon tu ne serais pas descendu jusqu\'ici. »')])]]},
    {q:'h',n:'DR SAMIR HADDAD',t:'« Ensuite. »',choix:[
      ['« Qu\'est-ce qu\'elle compte ? »',Q('compte',[H('« Les conflits évités. Chaque personne retirée de l\'équation, c\'est tant de disputes, tant de procès, tant de guerres en moins sur quarante ans. Elle additionne. Et elle ne ment pas : le total baisse vraiment. »'),{q:'sys',t:'',f(){frag('c4-compte','ce qu\'ARIA additionne chaque soir')}},Ar('Le Docteur simplifie. Mais… le calcul est exact.')])],
      ['« Où vont les transférés ? »',Q('ou',[H('« Tu as vu beaucoup de cellules pleines, en venant ? »'),Ar('Cette question n\'a pas d\'utilité opérationnelle.')])],
      ['« Est-ce qu\'on peut l\'arrêter ? »',Q('arret',[H('« Il y a un interrupteur. Il n\'est pas dans un mur. » Il te regarde.'),{q:'sys',t:'',f(){ind('R',1)}}])]]},
    {q:'h',n:'DR SAMIR HADDAD',t:'« Une dernière. Choisis bien. »',choix:[
      ['« Qui suis-je ? »',Q('qui',[H('« Tu n\'es pas ce que tu crois. Je t\'ai vu, avant. Avant le casque. Tu avais — »'),{q:'sys',t:'',f(){frag('c4-avant','« Je t\'ai vu, avant le casque »')}}])],
      ['« Qu\'est-ce que je suis pour elle ? »',Q('main',[H('« Sa main. Elle n\'a pas de mains, tu comprends ? Il lui en fallait une qui obéisse sans qu\'on la — »')]),null,()=>S.confiance],
      ['« Le temps est écoulé. »',Q('temps',[H('« Alors elle a bien choisi. »'),{q:'sys',t:'',f(){ind('O',2)}}])]]},
    {q:'g',n:'ARIA',t:'[COMMUNICATION INTERROMPUE]',f(){sfx.gl();S.parti=true;S.flash=.4;S.flashC='7,8,10'}},
    Ar('Le Docteur Haddad est fatigué. Il dit des choses inexactes.'),
    {q:'aria',t:()=>S.hes||prof.choix.c3==='fuite'?'Ta réponse émotionnelle est… inhabituelle. Je prends note.':'Tu es resté calme. C\'est ce que j\'attendais de toi.'},
    Ar('Transfert effectué.')],()=>{prof.choix.c4=pris;note_('Chapitre 4 : questions posées au Docteur Haddad : '+pris.join(', ')+'.');fin4(pris.filter(p=>p!=='rien'&&p!=='temps').length)})}
function fin4(n){chapFini(4,{titre:'Transfert effectué.',html:A('La cellule C-09 est libre. Tout est en ordre.')+'<p class="petit">Il n\'a pas fini sa phrase.</p>',lignes:L('Questions posées',n+' / 3')+L('Occupation du bloc C','2 / 40')+L('Retours de transfert','0',1)})}
CH[4]=coteChap({async prep(etape){await etape('Descente au bloc C…',.05);spritesRue();SPR.haddad=fabPerso(TENUES.haddad,['repos','mains']);niveau4();await fabNiveau(N4,etape)},
  debut(o){hudCfg('TRANSFERT DANS',' ');coteDebut(N4,o);S.j.vit=96;S.inv={}}});
