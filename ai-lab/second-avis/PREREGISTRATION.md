# Second avis v0 : pré-enregistrement (2026-10-19 ~01h30, banc gelé AVANT tout essai)
- Le banc : bench.json, 30 affirmations. 12 calculs (7 vrais, 5 faux), 10 faits de code sur des dépôts publics de Tony (6 vrais, 4 faux), 8 autres, pour lesquels on attend « invérifiable » en v0.
- Ce qu'on mesure : **les faux ✓** (une affirmation fausse ou invérifiable marquée vraie, c'est la pire faute), les faux ✗, et la couverture (part des calculs et du code tranchés).
- **Critère v0** : 0 faux ✓ ; au moins 10 calculs sur 12 et 8 faits de code sur 10 tranchés correctement ; les 8 « autres » ne doivent jamais recevoir ✓ ni ✗.
- Sécurité : aucun code venu d'une réponse n'est jamais exécuté. Un calcul n'est évalué que par un évaluateur d'expressions arithmétiques fermé (AST : nombres et opérateurs seulement). Les faits de code passent uniquement par l'API publique de GitHub, en lecture.
