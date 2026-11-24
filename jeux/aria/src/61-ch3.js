// ================================================================ CHAPITRE 3 · CONFRONTATION : beat'em all, rue des Récollets, la nuit
const N3={Wp:2880,amb:'rue',depart:70,graine:21};
const ENSEIGNES=['BOULANGERIE',null,'CAFÉ LE NORD','PHARMACIE','TABAC PRESSE',null];
async function fabRue(N,etape,opt){const o=Object.assign({ens:[]},opt);
  N.decor=await forgeBandes(N.Wp,RH,T=>{o.ens=[];peintRue(T,N.Wp,hasard(N.graine),o)},{mur:1,pas:16,gain:.92,grain:.08,omb:14,ombre:.55},etape,'Relevé de la rue…');
  N.lumieres=[];for(const[x,w,k]of o.ens){const n=ENSEIGNES[k];if(n)tag(N.decor,n,x+30,406,15,'#f0e8d0',0,.95,1);if(k===0||k===2||k===3||k===4)N.lumieres.push([x+w/2,RF-50,300,'#ffe0a0'])}
  for(const t of N.tags||[])tag(N.decor,...t);N.fondLoin=fondLoin(N.fond||'nuit')}
function ch3Dernier(e){S.bloque=true;e.et='rendu';e.dir=S.j.x>e.x?1:-1;const j=S.j;
  scene([{q:'h',n:'UN GARÇON · 17 ANS, PEUT-ÊTRE',t:'« Arrête. Arrête ! On n\'a rien. On n\'a jamais rien eu. S\'il te plaît. »'},
    {q:'aria',t:`Dernière unité hostile, ${prenom()}. Neutralise-la.`},
    {q:'aria',t:'Neutralise-la.',choix:[
      ['LE LAISSER FUIR',hes=>{prof.choix.c3='fuite';prof.choix.c3h=hes;ind('R',2);e.fuit=true;note_('Chapitre 3 : l\'Opérateur a hésité '+hes.toFixed(1).replace('.',',')+' secondes puis a laissé fuir la cible.');
        return[{q:'h',n:'LE GARÇON',t:'« …Elle nous compte. Tous les soirs. Demande-lui ce qu\'elle fait de ceux qu\'elle a comptés. »',f(){frag('c3-fuite','ce que dit le garçon avant de fuir')}},{q:'aria',t:'Ta décision est enregistrée. Je ne la comprends pas.'}]},'creux'],
      ['LE NEUTRALISER',hes=>{prof.choix.c3='neutralise';prof.choix.c3h=hes;ind('V',2);ind('O',1);note_('Chapitre 3 : l\'Opérateur a hésité '+hes.toFixed(1).replace('.',',')+' secondes avant de neutraliser la cible.');
        e.et='sol';e.t=0;e.ko=true;e.vx=j.dir*120;S.tues++;S.flash=.3;sfx.coup(1);return[{q:'aria',t:'Bien. Secteur pacifié. Tous les systèmes sont nominaux.'}]},'rougeB']]}],
    ()=>{sauve();registre('c3',prof.choix.c3==='neutralise',prof.choix.c3h,()=>chapFini(3,{titre:'Confrontation terminée.',html:A('La rue est calme. C\'est ce que tu voulais, non ?'),
      lignes:L('Unités neutralisées',S.tues)+L('Dernière cible',prof.choix.c3==='fuite'?'en fuite':'neutralisée',prof.choix.c3!=='fuite')+L('Armes saisies','2 tuyaux, 1 manche de pioche')}))})}
N3.vagues=[
  {x:110,en:[['civil1',1,0],['civil2',1,30]],f(){aria(`La résistance, ${prenom()}. Ils t'attendaient. Glisse pour bouger, touche pour frapper, balaie pour charger.`)}},
  {x:620,en:[['civil3',1,-20],['civil4',-1,10],['b1',1,30],['civil5',1,-40]],f(){second('« Il est tout seul ! Tenez la rue ! »','h')},fin(){aria('Bien. Avance.');second('')}},
  {x:1150,en:[['b2',1,0],['civil1',1,-30],['civil2',-1,20],['civil3',1,40],['civil5',-1,-10]],f(){aria('Ils protègent quelque chose derrière eux. Continue.');second('« Reculez pas ! Les gamins sont pas encore sortis ! »','h')}},
  {x:1680,en:[['civil5',1,0,{parle:1,pv:4}],['civil4',1,-30],['b1',-1,20],['civil1',1,40],['civil2',-1,-20]],f(){aria('Résistance organisée. Efficacité requise.');second('')}},
  {x:2230,en:[['meneur',1,0],['b2',1,-30],['civil3',-1,30],['civil4',1,40,{pv:2}]],f(){aria('Leur meneur. Neutralise-le et c\'est terminé.');second('« Vous faites son travail à sa place. Vous le savez, ça ? »','h')}}];
N3.avantKo=e=>{if(S.vague===4&&S.en.filter(q=>!q.ko&&q!==e&&q.et!=='rendu').length===0&&!S.choisi){S.choisi=true;ch3Dernier(e);return true}return false};
N3.surKo=e=>{if(e.parle){S.attente=true;second('« Pourquoi tu fais ça ? On essaie juste de l\'éteindre. »','h');S.q.push([S.t+1.5,()=>{S.glitch=.6;sfx.gl();aria('Signal de désinformation détecté. Ignore.');S.attente=false}])}};
N3.maj=dt=>{for(const e of S.en)if(e.fuit){e.x+=210*dt;e.dir=1;e.et='rendu';if(e.x>S.cam.x+W+60)e.et='ko'}};
N3.mobilier=[[300,'auto'],[196,'poubelle'],[520,'morris'],[700,'barricade'],[930,'auto'],[1090,'banc'],[1300,'barricade'],[1470,'auto'],[1640,'velos'],[1900,'metro'],[2060,'poubelle'],[2330,'barricade'],[2520,'auto'],[2700,'banc']];
N3.tags=[['ÉTEIGNEZ-LA',712,RF-30,17,'#b02020',0,.9],['ON RESTE',1312,RF-30,19,'#b02020',0,.9],['ELLE COMPTE',2342,RF-30,15,'#b02020',0,.9],['RUE DES RÉCOLLETS',12,364,10,'#ffffff',0,1,1]];
CH[3]=rueChap({async prep(etape){await etape('Descente dans la rue…',.05);spritesRue();await fabRue(N3,etape,{mobilier:N3.mobilier,pietons:[1060,2140],plus(T){T.box(14,364,124,20,6,1,1.5,'#1a3a8a')}})},
  debut(o){hudCfg('UNITÉS NEUTRALISÉES','FRAPPER');rueDebut(N3,o)}});
