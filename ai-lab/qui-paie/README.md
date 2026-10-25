# Qui paie ?

Pour une question de santé, l'outil liste les revues systématiques et méta-analyses de PubMed, et montre pour chacune **qui l'a financée** et **les conflits d'intérêts déclarés** par les auteurs (PubMed + texte intégral de PubMed Central). Il ne juge pas la qualité de l'étude : il montre l'argent, le lecteur juge.

```bash
python3 qui_paie.py "(milk[tiab] OR dairy[tiab]) AND child*[tiab] AND bone[tiab]" --n 10
python3 qui_paie.py "sugar sweetened beverages obesity" --industrie "sugar,beverage association"
```

Limites : mots-clés simples (un financeur au nom inconnu passe inaperçu) ; seules les déclarations publiées sont lues ; « aucun conflit déclaré » veut dire déclaré, pas vérifié.

Exemple (25/10/2026) : `exemple-lait-enfants-2026-10-25.md`. La prise de position de la National Osteoporosis Foundation sur le pic de masse osseuse (2016) a été financée par le Dairy Research Institute et l'Alliance for Potato Research ; une méta-analyse de 2023 sur le lait enrichi est soutenue par Farm Fresh, une marque de lait.
