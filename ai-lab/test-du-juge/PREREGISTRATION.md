# Test du Juge : pré-enregistrement (écrit et commité AVANT de générer ou de noter quoi que ce soit, 2026-10-17)

Question : les associations que propose le graphe cerveau-nb (trous structurels : A–B et B–C forts, pas de A–C) sont-elles plus fécondes que des paires tirées au hasard ?

- Graphe : cerveau-nb/brain_state.json, nœuds de type concept/memory/pattern/emotion (les « word » sont exclus).
- 20 associations du graphe : les trous structurels avec le plus fort produit des poids w(A,B)·w(B,C), à raison d'au plus 2 par nœud A.
- 20 associations témoin : des paires tirées au hasard avec une probabilité proportionnelle au degré (même popularité que dans le graphe) et qui ne sont pas reliées directement.
- On mélange les 40 par script (graine 1017) et on retire l'origine. On note chaque paire de 0 à 2 sur la question : « cette association suggère-t-elle une idée nouvelle et utile ? ».
- Notateurs : (1) Haiku, à l'aveugle, une paire par appel ; (2) **Tony**, à l'aveugle, s'il le veut (fiche FICHE-TONY.md).
- **Critère fixé d'avance** : le graphe gagne si sa moyenne dépasse celle du témoin d'au moins 0,4 point ET si un test de permutation donne p < 0,05. Sinon, j'abandonne le Discovery Engine dans sa forme actuelle et je le note dans le journal.
