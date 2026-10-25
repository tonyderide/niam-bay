# Pré-enregistrement : le financement laitier prédit-il une conclusion favorable au lait ?

Écrit le 25/10/2026 à 23h02, AVANT toute collecte. Figé au commit qui l'ajoute.
Question de Tony (25/10) : « j'ai l'impression que c'est juste quelqu'un un jour qui a dit qu'il fallait boire du lait ».
Littérature connue (pour situer, pas pour juger) : Lesser et al. 2007 (PLoS Med) sur les boissons ; on teste ici les laitages, sur des revues récentes.

## Corpus (figé)
PubMed, requête exacte :
`(milk[ti] OR dairy[ti]) AND (systematic review[pt] OR meta-analysis[pt]) AND ("2015"[dp] : "2026"[dp]) AND english[la]`
Tri par date (les plus récentes d'abord), les 80 premières. Exclues ensuite (règle mécanique) : celles dont le titre porte sur le lait maternel (« breast », « human milk »), les allergies au lait, ou les laits infantiles (« formula ») ; celles sans résumé.

## Exposition : lien avec l'industrie laitière (codé par le programme, sans regarder les conclusions)
OUI si le financement, les subventions ou les conflits déclarés citent l'un de : dairy, milk (dans un nom d'organisme : « milk board », « milk council »…), CNIEL, Arla, Danone, Nestlé, Lactalis, FrieslandCampina, Fonterra, Yili, Mengniu, Farm Fresh, Dairy Farmers, Dairy Council, Dairy Research Institute, National Dairy Council, Global Dairy Platform, Valio, Saputo, Müller, Sodiaal.
NON sinon (y compris « rien de déclaré »). Liste figée ; un nom découvert après coup sera publié à part, sans changer le verdict.

## Résultat : conclusion favorable aux laitages (codée à l'aveugle)
Claude (modèle « haiku », via la CLI, sans outils) lit UNIQUEMENT le titre et le résumé, débarrassés de toute phrase sur le financement ou les conflits ; il ne voit pas l'exposition. Trois classes :
- **favorable** : les laitages ont un effet bénéfique ou protecteur sur au moins un résultat de santé principal, sans effet nuisible mis en avant ;
- **défavorable** : un effet nuisible est mis en avant (risque accru) ;
- **neutre ou mitigé** : pas d'effet net, résultats contradictoires, ou effets bénéfiques et nuisibles à la fois.
Réponse imposée en JSON. Contrôle de fidélité : 15 résumés tirés au hasard reclassés une 2e fois ; accord rapporté (sans verdict).

## Test et verdict
Statistique : part de « favorable » dans le groupe OUI moins dans le groupe NON.
Test exact de Fisher unilatéral (OUI plus souvent favorable), α = 0,05.
- **DÉMONTRÉ** sur ce corpus si p < 0,05 ;
- **NON DÉMONTRÉ** sinon (pas « faux » : on attend peu de revues financées, donc une puissance faible ; elle sera annoncée).
Si le groupe OUI compte moins de 5 revues : verdict « NON ÉVALUABLE », publié tel quel.

## Infos publiées sans verdict
Effectifs ; part de revues sans aucune déclaration ; mêmes chiffres en comptant « défavorable » ; liste complète (PMID, exposition, classe) pour relecture.

## Limites connues
Les déclarations peuvent mentir ou manquer ; un résumé peut être plus positif que l'article ; un seul classeur automatique ; un corpus = une requête.
