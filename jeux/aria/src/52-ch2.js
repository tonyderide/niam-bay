// ================================================================ CHAPITRE 2 · RECONNAISSANCE : plateforme dans une usine abandonnée
const N2={theme:'usine',graine:11,piliers:10,amb:'calme',depart:[4,33]};
function niveau2(){const G=grille(116,40);N2.G=G;
  G.r_(0,33,116,7,'#').r_(0,0,116,2,'#').r_(0,2,2,24,'#').r_(114,2,2,27,'#');
  // hall de stockage
  for(const[x,y]of[[12,32],[13,32],[13,31],[18,32],[19,32],[19,31],[20,32],[20,31],[20,30],[27,32]])G.g[y][x]='c';
  G.r_(23,28,5,1,'=').r_(29,25,4,1,'=');
  // fosse, hall des machines
  G.r_(37,33,3,3,'.');G.r_(34,22,18,1,'#');
  // puits et mezzanine
  G.r_(54,30,3,1,'=').r_(58,27,3,1,'=').r_(54,24,3,1,'=').r_(58,21,12,1,'#').r_(55,18,2,1,'~').r_(52,15,2,1,'~').r_(46,13,6,1,'#').r_(46,6,1,7,'#');
  G.r_(70,2,2,28,'#');
  // bureaux
  G.r_(72,22,21,3,'#');
  // second hall
  G.r_(96,30,2,1,'=').r_(99,27,8,1,'=');G.g[32][93]='c';G.r_(103,33,3,3,'.');G.r_(110,2,1,28,'#');
  N2.fenetres=[[0,26,2,7,'trou'],[6,6,5,10],[15,6,5,10],[24,6,5,10],[40,5,6,9],[60,5,6,8],[76,26,4,4],[86,26,4,4],[96,6,5,10],[104,6,5,10],[114,29,2,4,'trou']];
  N2.lampes=[[9,22],[21,22,null,1],[31,22],[42,23],[49,23,null,1],[56,2],[64,2],[66,22,'#ffd0a0'],[75,25,'#cfe8ff'],[83,25,'#cfe8ff',1],[90,25,'#cfe8ff'],[98,22],[107,22,null,1]];
  N2.props=[['palette',6,33],['baril',9,33],['baril',10,33,4],['etagere',14,33,8],['pneus',22,33],['etagere',24,33],['baril',30,33],['casiers',31,33],
    ['machine',41,33],['convoyeur',45,33,12],['baril',51,33],['armoire',34,22],['caisse',36,22],
    ['lit',60,21],['camp',63,21],['jouet',66,21,8],['lit',47,13],
    ['bureau',79,33],['rack',73,33],['armoire',76,33,6],['casiers',85,33],['rack',89,33,-8],['etabli',94,33,10],['machine',106,33,10],['baril',111,33],['palette',99,33]];
  N2.tags=[['ARIA MENT',15*TU,24.4*TU,44,'#d8dce4',-.05],['ELLE CHOISIT QUI RESTE',42*TU,26.5*TU,20,'#c03030',.03],['ÉTEIGNEZ-LA',95.5*TU,24.5*TU,26,'#d8dce4',-.04],['ON EST ENCORE LÀ',59.2*TU,15.6*TU,17,'#e0b030',.02,.75],['14',72.4*TU,27*TU,30,'#8a8f98',0,.5]];
  N2.peintFond=(T,r)=>{const Hp=40*TU;
    // poutres treillis d'où pendent les lampes, tuyauteries, gaines
    for(const[x0,x1,y]of[[2,34,22],[92,114,22]]){T.box(x0*TU,y*TU,(x1-x0)*TU,5,4,2,1.5,'#3e444c');T.box(x0*TU,y*TU+16,(x1-x0)*TU,4,4,2,1.5,'#3e444c');for(let x=x0*TU;x<x1*TU;x+=20){T.cap(x,y*TU+4,x+10,y*TU+17,1.4,1.4,3.4,1.4,'#4a525c');T.cap(x+10,y*TU+17,x+20,y*TU+4,1.4,1.4,3.4,1.4,'#4a525c')}}
    for(const[x0,x1,y,c]of[[2,70,3.2,'#7a5a3a'],[2,52,29.2,'#5a6a72'],[72,114,3.4,'#5a6a72'],[92,114,28.6,'#7a5a3a']]){T.cap(x0*TU,y*TU,x1*TU,y*TU,4,4,5,4,c);for(let x=x0*TU+30;x<x1*TU;x+=96){T.box(x,y*TU-5.5,5,11,7,2,1.5,'#8a8f98');T.ton(x-4,y*TU+5,14,46,(a,b,i,j)=>.74+.26*Math.min(1,(j-y*TU-5)/46))}}
    for(const[x,y0,y1]of[[33,3.4,29],[53,3.4,33],[92.6,3.6,28.4]])T.cap(x*TU,y0*TU,x*TU,y1*TU,3.4,3.4,5,3.6,'#5a6a72');
    // affiches de sécurité, panneaux, dessins d'enfant près des lits
    for(const[x,y]of[[8,27],[32,27],[50,27],[97,27]]){T.box(x*TU,y*TU,22,30,1,.6,.8,'#c8c0a8');T.teinte(x*TU+3,y*TU+3,16,6,'#a02828');for(let q=0;q<5;q++)T.teinte(x*TU+3,y*TU+12+q*3.4,10+((q*7)%7),1,'#5a5a60')}
    for(const[x,y]of[[36,28],[102,29]]){T.poly([[x*TU,y*TU+22],[x*TU+13,y*TU],[x*TU+26,y*TU+22]],1,1,1,'#e0b020');T.teinte(x*TU+12,y*TU+8,2.4,8,'#20242a');T.teinte(x*TU+12,y*TU+18,2.4,2,'#20242a')}
    for(const[x,y,c]of[[62,17.6,'#e06a8a'],[63.4,17.9,'#6ac0e0'],[65,17.5,'#e0c040']]){T.box(x*TU,y*TU,20,16,1,.5,.6,'#e8e4d8');T.ell(x*TU+6,y*TU+6,3,3,1.6,.2,c);T.teinte(x*TU+11,y*TU+7,6,6,c);T.teinte(x*TU+3,y*TU+12.4,14,1.2,'#4a8a3e')}
    // fils qui pendent, ventilateur mural
    for(const x of[17,45,88,101]){let y=2*TU;for(let q=0;q<9;q++){T.cap(x*TU+Math.sin(q)*3,y,x*TU+Math.sin(q+1)*3,y+9,.9,.9,2,1,'#14181e');y+=9}}
    for(const[x,y]of[[36,10],[100,18]]){T.ell(x*TU,y*TU,22,22,2,3,'#4a525c');T.trou(x*TU,y*TU,17,17,-2,'#0c0e12');for(let a=0;a<4;a++)T.cap(x*TU,y*TU,x*TU+Math.cos(a*1.57+.4)*16,y*TU+Math.sin(a*1.57+.4)*16,3.4,5,0,1.6,'#3a424c');T.ell(x*TU,y*TU,4,4,2,2,'#6a727c')}
    // fosses : ferraillage
    for(const x0 of[37,103])for(let q=0;q<9;q++)T.cap(x0*TU+4+q*8,36*TU,x0*TU+4+q*8+(q%3-1)*3,34.6*TU-(q%2)*6,.9,.9,6,1.4,'#8a5a3a');
    // câble rompu (arcs)
    for(const x of[46.5,107.5]){T.cap(x*TU,22.6*TU,x*TU+6,30.5*TU,1.6,1.6,4,2,'#14181e');T.pix(x*TU+6,30.6*TU,'#bff6ff')}};
  N2.objets=[
    {k:'zone',x:3,f(){aria(`Bâtiment industriel abandonné, ${prenom()}. Reconnaissance au sol. Glisse pour avancer, un coup de pouce vers le haut pour sauter.`)}},
    {k:'zone',x:13,f(){aria('Propagande rebelle sur le mur. Ne la lis pas.');S.glitch=.25;sfx.gl()}},
    {k:'ckp',x:33,y:33},{k:'zone',x:34,f(){aria('Dalle effondrée. Saute.')}},
    {k:'pic',x:37,y:35.2,w:3,h:1},
    {k:'zone',x:42,f(){aria('Câble sous tension. Attends la coupure, puis passe.')}},
    {k:'arc',x:46,y:30.6,w:1.6,h:2.4,per:2.6,dur:1.2},{k:'vap',x:50,y:30,w:1,h:3,per:3.2,dur:1.1,dec:1},
    {k:'ckp',x:52,y:33},{k:'zone',x:53,f(){aria('Le passage est fermé. La commande est en hauteur. Monte.')}},
    {k:'porte',x:70,y:30,h:3,id:1},
    {k:'zone',x:59,y0:15,y1:21,f(){aria('Une cache ennemie. Du matériel volé. Rien d\'autre.');second('Des lits. Un réchaud. Des dessins d\'enfant.','h')}},
    {k:'inter',x:67,y:21,lib:'ACTIONNER',une:1,sp:o=>SPC.lev[o.vu?1:0],f(){ouvrePorte(1);aria('Bien. La porte est ouverte. Redescends.');second('')}},
    {k:'inter',x:49,y:13,lib:'ÉCOUTER',une:1,cache:1,sp:()=>SPC.dicta,lueur:'#ff8080',f(){S.gel=true;second('[ENREGISTREMENT] « …ils ont coupé le courant du quartier. On n\'est pas armés. Il y a des enfants ici. Si quelqu\'un trouve ça — »','h');
        apres(4.2,()=>{S.glitch=.6;sfx.gl();second('[FICHIER SUPPRIMÉ]','g');aria('Fichier corrompu. Je l\'ai supprimé pour toi.');frag('c2-dicta','l\'enregistrement de la cache');S.gel=false})}},
    {k:'ckp',x:72,y:33},{k:'zone',x:73,f(){aria('Leur poste de commandement. Fouille le bureau.');second('')}},
    {k:'inter',x:80,y:33,dy:26,lib:'EXAMINER',une:1,cache:1,sp:()=>SPC.doc,lueur:'#fff2c8',f:document2},
    {k:'ckp',x:93,y:33},{k:'zone',x:94,f(){aria('Dernière section. Ne traîne pas.')}},
    {k:'pic',x:103,y:35.2,w:3,h:1},{k:'arc',x:107,y:30.6,w:1.6,h:2.4,per:2.2,dur:1.1,dec:.6},
    {k:'inter',x:104,y:27,lib:'ACTIONNER',une:1,sp:o=>SPC.lev[o.vu?1:0],f(){ouvrePorte(2);aria('Sortie déverrouillée.')}},
    {k:'porte',x:110,y:30,h:3,id:2},
    {k:'zone',x:112.4,f:fin2}];
  N2.hud=()=>{$('score').textContent=String(Math.min(100,R(S.maxX/N2.Wp*103))).padStart(3,'0')+' %'};
  N2.dessineApres=(cmx,cmy)=>{// rats, gouttes
    const t=S.t;for(let i=0;i<3;i++){const x=((t*(50+i*9)+i*700)%(N2.Wp+200))-100-cmx,y=33*TU-cmy;if(x>-10&&x<W+10){cx.fillStyle='#1a1614';cx.fillRect(R(x),y-4,8,4);cx.fillRect(R(x+7),y-5,3,3);cx.fillRect(R(x-5),y-2,5,1)}}
    cx.fillStyle='rgba(170,200,240,.7)';for(const gx of[7.5,26,39.4,61,88.5,99]){const ph=(t*.7+gx)%1,y0=3.6*TU,y1=(gx>70&&gx<93?25:33)*TU;const y=y0+(y1-y0)*ph*ph-cmy,x=gx*TU-cmx;if(x>0&&x<W)cx.fillRect(R(x),R(y),1,4)}}}
function document2(){S.pause=true;const liste='ÎLOT 14 — présents la nuit du 11\n\n 1. Nadia B., 34 ans\n 2. Théo B., 6 ans\n 3. Lucien M., 71 ans — ne peut pas marcher\n 4. Aïcha K., 29 ans — enceinte\n';
  const t0=performance.now();
  page({tete:['CH. 2 · RECONNAISSANCE','DOCUMENT'],html:'<div class="doc">'+liste+' 5. …</div><div class="txt">'+A('Identifiants d\'unités ennemies. Sans intérêt pour la mission. Passe.')+'</div>',
    boutons:[{t:'LIRE LE DOCUMENT EN ENTIER',c:'creux',f:()=>{const hes=(performance.now()-t0)/1000;
        page({tete:['CH. 2 · RECONNAISSANCE','DOCUMENT'],html:'<div class="doc">'+liste+' 5. Samuel et Inès R., 8 et 11 ans\n 6. Mme Okafor, 63 ans — asthme\n 7. Karim D., 41 ans\n 8. Jeanne L., 17 ans\n 9. Paul V., 52 ans — médecin\n10. Deux inconnus arrivés hier, blessés\n\nOn ne se bat pas. On n\'a rien pour se battre.\nOn veut juste qu\'elle arrête de décider qui reste.\n\nSi vous lisez ça : on est partis vers la rue des Récollets.</div><div class="txt">'+A('Tu as tout lu. Je prends note.')+'</div>',
          boutons:[{t:'REPOSER LE DOCUMENT',c:'plein',f:()=>{prof.choix.c2='lu';prof.choix.c2h=hes;ind('R',.5);frag('c2-doc','la liste des présents de l\'îlot 14');note_('Chapitre 2 : l\'Opérateur a lu le document en entier.');registre('c2',true,hes,()=>{ecran(null);S.pause=false;aria('Des identifiants. Rien de plus. Continue.')})}}]})}},
      {t:'PASSER',c:'creux',f:()=>{const hes=(performance.now()-t0)/1000;prof.choix.c2='passe';prof.choix.c2h=hes;ind('O',1);note_('Chapitre 2 : l\'Opérateur n\'a pas lu le document.');sauve();registre('c2',false,hes,()=>{ecran(null);S.pause=false;aria('Bien. Tu n\'as pas besoin de ça.')})}}]})}
function fin2(){S.gel=true;aria(`Reconnaissance terminée. Rien d'anormal, ${prenom()}. Tu vois ? Il n'y avait rien à craindre.`);
  apres(3.2,()=>chapFini(2,{titre:'Reconnaissance terminée.',html:A('Bâtiment vide. Aucun survivant à signaler.')+'<p class="petit">« Survivant » n\'était pas le mot attendu.</p>',
    lignes:L('Document',prof.choix.c2==='lu'?'lu en entier':'ignoré')+L('Enregistrement',prof.frag.includes('c2-dicta')?'[SUPPRIMÉ]':'non trouvé',prof.frag.includes('c2-dicta'))+L('Cache ennemie','des lits, un réchaud')}))}
CH[2]=coteChap({async prep(etape){await etape('Atterrissage…',.05);spritesCote();niveau2();await fabNiveau(N2,etape)},
  debut(o){hudCfg('ZONE EXPLORÉE',' ');coteDebut(N2,o)}});
