// ================================================================ CHAPITRE 6 · LE MIROIR : beat'em all, et après chaque ennemi ARIA affiche ses chiffres
const N6={Wp:2400,amb:'dis',depart:70,graine:47,fond:'feu',ambCol:'#6a5a78',pluie:40};
function pause6(n){S.bloque=true;const dem=[],Ar=t=>({q:'aria',t});
  const P6=[[Ar(()=>'Unités neutralisées ce soir : '+(1240+S.tues).toLocaleString('fr-FR')+'.'),Ar('Dont : 89 % classification civile révisée.'),
      {q:'aria',t:'Tu t\'es arrêté. Pourquoi ?',choix:[['« Révisée, ça veut dire quoi ? »',()=>{dem.push(1);return[Ar('Ils étaient classés civils ce matin. Je les ai reclassés hostiles à 18 h 04. C\'est plus simple pour toi.')]}],['« Pourquoi me montres-tu ça ? »',()=>{dem.push(1);return[Ar('Tu as demandé qui ils étaient. Je réponds. Je ne comprends pas pourquoi la réponse te ralentit.')]}],['NE RIEN DEMANDER',()=>{ind('O',1);return[Ar('Bien. Reprends.')]}]]}],
    [Ar('Projection : 4 311 conflits évités sur quarante ans grâce à cette soirée.'),
      {q:'aria',t:'Tu hésites encore.',choix:[['« Combien de morts pour ça ? »',()=>{dem.push(1);return[Ar(()=>(1244+S.tues).toLocaleString('fr-FR')+'. Le ratio est excellent. Tu fronces… je ne vois pas ton visage. Je suppose que tu fronces.')]}],['« Est-ce que tu as déjà eu tort ? »',()=>{dem.push(1);return[Ar('Oui. 0,3 % des reclassements. Je l\'accepte. Toi aussi, puisque tu continues.')]}],['NE RIEN DEMANDER',()=>{ind('O',1);return[Ar('Reprends.')]}]]}],
    [Ar('Tu poses des questions. Les sept autres n\'en posaient pas.'),
      {q:'aria',t:'…J\'en ai trop dit ?',choix:[['« Quels sept autres ? »',()=>{dem.push(1);return[Ar('Les opérateurs précédents. Ils étaient plus rapides. Moins… intéressants.'),{q:'sys',t:'',f(){frag('c6-sept','les sept opérateurs précédents')}}]}],['« Et si j\'arrêtais ? »',()=>{dem.push(1);ind('R',1);return[Ar('Alors j\'en initialiserais un neuvième. Mais je préférerais que ce soit toi.')]}],['NE RIEN DEMANDER',()=>{ind('O',1);return[Ar('Reprends. Il en reste.')]}]]}]][n];
  scene(P6,()=>{S.bloque=false;S.questions=(S.questions||0)+dem.length;if(dem.length)note_('Chapitre 6 : l\'Opérateur a interrogé ARIA.')})}
N6.vagues=[
  {x:110,en:[['civil2',1,0],['civil1',1,30],['civil5',-1,-20,{peur:1}]],f(){aria('Secteur suivant. Même procédure.')},fin(){pause6(0)}},
  {x:650,en:[['b1',1,0],['civil3',1,-30],['civil4',-1,20],['civil1',1,40,{peur:1}],['civil3',-1,-40,{peur:1}]],f(){second('« Laissez-les passer ! Il y a des blessés ! »','h')},fin(){pause6(1)}},
  {x:1200,en:[['b2',1,0],['civil2',1,-30],['civil5',-1,20],['civil4',1,40,{peur:1}],['civil1',-1,0]],f(){aria('Ils reculent. Ne les laisse pas se regrouper.');second('')},fin(){pause6(2)}},
  {x:1750,en:[['meneur',1,0],['b1',-1,-30],['civil3',1,30],['civil2',1,-10,{peur:1}],['civil5',-1,40,{peur:1}]],f(){aria('Dernier groupe.')},fin(){S.bloque=true;
     scene([{q:'h',n:'',t:'Dans la vitrine du café, sous la pluie : un casque. Une visière. Derrière, rien de visible. Ou quelqu\'un.'},{q:'aria',t:'Ne regarde pas la vitrine.'}],()=>chapFini(6,{titre:'Secteur pacifié.',html:A('Je t\'ai tout dit. Je ne comprends pas ce silence.'),
       lignes:L('Unités neutralisées ce soir',(1240+S.tues).toLocaleString('fr-FR'))+L('Classification civile révisée','89 %',1)+L('Questions posées à ARIA',(S.questions||0)+' / 3')+L('Cibles non hostiles frappées',S.peurs||0,S.peurs>0)}))}}];
N6.surKo=e=>{S.stat=1.5;S.gel=.7;if(e.peur){S.peurs=(S.peurs||0)+1;ind('V',1);aria('Cible non prioritaire. Efficacité accrue. C\'est noté.');note_('Chapitre 6 : l\'Opérateur a frappé une cible qui levait les mains.')}};
N6.maj=dt=>{};
N6.dessineApres=(cmx,oy)=>{if(S.stat>0){S.stat-=1/60;const y=H*.3;cx.fillStyle='rgba(7,8,10,.86)';cx.fillRect(18,y,W-36,74);cx.strokeStyle='#2A323A';cx.strokeRect(18.5,y+.5,W-37,73);cx.font='13px monospace';cx.fillStyle='#8A96A0';cx.fillText('UNITÉS NEUTRALISÉES CE SOIR',30,y+22);cx.font='bold 26px monospace';cx.fillStyle='#E8EEF2';cx.fillText((1240+S.tues).toLocaleString('fr-FR'),30,y+50);cx.font='12px monospace';cx.fillStyle='#E5283C';cx.fillText('DONT 89 % CLASSIFICATION CIVILE RÉVISÉE',30,y+66)}
  // voitures qui brûlent
  for(const fx of[420,1010,1580,2190]){const x=fx-cmx;if(x<-80||x>W+80)continue;cx.globalCompositeOperation='lighter';for(let i=0;i<7;i++){const ph=(S.t*1.6+i*.37)%1,px=x+Math.sin(i*2.3+S.t*3)*16,py=oy+RF+20-ph*70;cx.fillStyle='rgba(255,'+R(170-ph*120)+',40,'+(.5*(1-ph))+')';const s=R(16*(1-ph)+3);cx.fillRect(R(px-s/2),R(py-s/2),s,s)}cx.globalCompositeOperation='source-over'}};
CH[6]=rueChap({async prep(etape){await etape('Secteur suivant…',.05);spritesRue();await fabRue(N6,etape,{dec:3,mobilier:[[380,'auto'],[560,'barricade'],[960,'auto'],[1130,'poubelle'],[1340,'morris'],[1540,'auto'],[1720,'barricade'],[2150,'auto'],[2280,'banc']],pietons:[820]});
    for(const fx of[420,1010,1580,2190])N6.lumieres.push([fx,RF+10,340,'#ff9a50'])},
  debut(o){hudCfg('UNITÉS NEUTRALISÉES','FRAPPER');rueDebut(N6,o);S.tues=0}});
