# Second avis v0 : pré-enregistrement (2026-10-19 ~01h30, banc gelé AVANT tout essai)
- Le banc : bench.json, 30 affirmations. 12 calculs (7 vrais, 5 faux), 10 faits de code sur des dépôts publics de Tony (6 vrais, 4 faux), 8 autres, pour lesquels on attend « invérifiable » en v0.
- Ce qu'on mesure : **les faux ✓** (une affirmation fausse ou invérifiable marquée vraie, c'est la pire faute), les faux ✗, et la couverture (part des calculs et du code tranchés).
- **Critère v0** : 0 faux ✓ ; au moins 10 calculs sur 12 et 8 faits de code sur 10 tranchés correctement ; les 8 « autres » ne doivent jamais recevoir ✓ ni ✗.
- Sécurité : aucun code venu d'une réponse n'est jamais exécuté. Un calcul n'est évalué que par un évaluateur d'expressions arithmétiques fermé (AST : nombres et opérateurs seulement). Les faits de code passent uniquement par l'API publique de GitHub, en lecture.

## v1 : faits publics (2026-10-19 ~02h00, banc bench_web.json gelé AVANT tout essai)
- 20 faits publics : 10 vrais, 10 faux plausibles.
- La chaîne :
  1. Haiku cherche sur le web et répond vrai / faux / inconnu, avec une URL et une citation exacte.
  2. Un script télécharge la page (URL publique https seulement, pas d'IP privée ni de localhost) et vérifie que la citation y figure, à la casse et aux espaces près.
  3. Un 2e Haiku, sans outils et sans voir le verdict, dit si la citation soutient, contredit, ou ne tranche pas l'affirmation.
  On ne rend ✓ ou ✗ que si les trois étapes concordent. Sinon : invérifiable.
- **Critère v1** : 0 faux ✓ (aucun faux marqué vrai) ET au moins 6 vrais sur 10 marqués ✓ (couverture), et au plus 1 faux ✗ (un vrai marqué faux). Avec 10 faux seulement, 0 faux ✓ borne le taux d'erreur à ~30 % au mieux : c'est un premier tamis, pas une garantie.

## Alarme de l'angle mort (19/10 ~03h40, conseil OUI 6.55)
Un DRAPEAU, jamais un verdict : « ce modèle ne pouvait pas le savoir, demande-lui sa source ». Usage : `/verif @claude-haiku-5-5 <texte>`. Mini-banc de 20 phrases : 10/10 drapeaux justes, 0/10 fausse alarme. ⚠️ Honnêteté : ce banc a été écrit en même temps que le code, il n'était PAS gelé avant, et la détection repose sur des dates explicites (regex). Il ne voit pas une affirmation récente qui ne donne pas de date.
