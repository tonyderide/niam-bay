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
