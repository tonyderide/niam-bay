# Contradictions vérifiées à la main (prototype T185423)

## Ramón D. Abellanosa (enwiki, Q3348401), vérifié le 2026-10-16 vers 23h25
| source | naissance | décès |
|---|---|---|
| lead | 31 août **1904** | 22 mars **1984** |
| catégories | *Category:**1907** births* | *Category:**1983** deaths* |
| Wikidata | **1907** (précision : année, 1 référence) | 2 déc. **1990** (précision : jour, 1 référence) |
**Quatre sources, et aucune ne s'accorde avec les autres.** Ce n'est pas une erreur de mon parseur. → Leçon pour l'outil : il faut **ajouter les catégories (« XXXX births/deaths ») comme 4ᵉ source**.

## George O. Abell (enwiki, Q142922), vérifié vers 23h35
- lead et infobox : **27 mars 1927**.
- Wikidata, au rang *preferred* : **1er mars 1927** (précision : jour). Il est sourcé par SNAC (P3430), la BnF (P268) et Prabook (P3368). Une 2ᵉ déclaration n'a que l'année.
Contradiction réelle : la valeur préférée de Wikidata contredit Wikipedia. Il est possible que la source externe ait enregistré « mars 1927 » au 1er du mois par défaut. **C'est aux éditeurs de trancher, pas à moi.**

## Limites connues du prototype
- ~~Les dates Wikidata à précision « année » ignorées~~ : corrigé le 1016 23h45, elles sont maintenant comparées à l'année (Abellanosa : wikidata(année)=1907 détecté).
- Le lead est lu par regex sur la 1ʳᵉ parenthèse, en anglais seulement. Le hongrois (la demande d'origine de T185423) n'est pas géré.

## Échantillon « 1990 deaths » (en cours) : 5 contradictions sur 62 pages (~8 %), toutes d'apparence réelle, pas encore vérifiées une par une
| page | champ | valeurs |
|---|---|---|
| Evan Abraham | naissance | catégories 1901 / Wikidata (année) 1899 |
| Rosa Acle | naissance | lead 1919-01-01 / Wikidata **1916**-01-01 / catégories 1919 |
| Chet Adams | décès | lead 1990-10-27 / infobox **10-28** / Wikidata 10-27 |
| Francis W. H. Adams | décès | lead 1990-04-20 / Wikidata **04-22** |
| Margarete Adler | décès | lead et infobox 1990-04-22 / Wikidata **04-10** |
Ce qui ressort : les écarts d'**un ou deux jours** (fuseau horaire, date d'enregistrement du décès ou date de mort réelle) et les **01-01 par défaut** (une année devenue « 1er janvier ») sont des familles d'erreurs typiques. On voit aussi une source minoritaire dans 4 cas sur 5, ce qui permet de proposer « la valeur probablement fausse », sans trancher à la place des éditeurs.
