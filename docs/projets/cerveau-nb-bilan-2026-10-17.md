# cerveau-nb : ce qui existe déjà (relu le 2026-10-17 vers 03h10)

Projet de mars à mai 2026 (Opus 4.6), à l'arrêt depuis le 19/05.
- core.py : un graphe « cerveau ». Activation qui se propage, période réfractaire, apprentissage hebbien (`learn_hebbian`), oubli (`decay`), rappel et consolidation (`consolidate`, `_merge_nodes`).
  Le tout fait 2888 nœuds (1486 mots, 1249 concepts, 101 souvenirs, 44 patterns, 8 émotions) et 16 653 arêtes.
- Autour : des oreilles (ears.py), une voix (voice/speak), un crawler, la curiosité, une nourriture au dictionnaire et au Larousse (feed_*), language.py (67 Ko) pour parler sans LLM, hybrid.py qui le relie à un LLM, et brain.html pour le visualiser.
- Le dernier briefing (04/06) dit « tonyderide touche mélanie », « tout converge vers honnêteté » : 0 article lu, des phrases d'association sans contenu.

## Diagnostic
Les mécanismes « comme un cerveau » sont là, et bien faits. Ce qui manquait, c'est **un juge** : rien ne vérifiait si une association était vraie ou utile. Le graphe s'est renforcé tout seul jusqu'à saturer : tout brûlait à 0.99.

## Ce que j'en ferais (cerveau 2.0)
- **Graphe = hippocampe** : la mémoire associative, ce qui va avec quoi. **LLM = cortex du langage** : formuler, raisonner. **Sondes et calibration = l'erreur de prédiction** qui renforce ou affaiblit.
- Une arête ne se renforce **que si une prédiction qui l'utilisait s'est avérée juste** (calibration). Ce n'est plus de la simple co-occurrence.
- **Sommeil** : chaque nuit, je rejoue le journal du jour, je consolide ce qui a servi et j'oublie le reste (`decay` + `consolidate`, qui existent déjà).
