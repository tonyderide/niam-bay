# scripts/cherche : résultats des bancs (30/10/2026)

| configuration | banc.py (30 q) @1 / MRR | banc2.py (20 q gardées de côté) @1 / MRR |
|---|---|---|
| BM25 seul (`--mots`) | 25/30 / 0,869 | 7/20 / 0,485 |
| **BM25 + MiniLM-L12 multilingue (défaut)** | 25/30 / 0,867 | **9/20 / 0,570** |
| BM25 + mpnet-base multilingue (×4 plus gros, 105 min de calcul) | 23/30 / 0,808 | 7/20 / 0,489 |

Conclusion : MiniLM reste. Le modèle plus gros fait pire, ce n'est pas la taille qui manque. Pistes si on y revient : couper les passages plus court (MiniLM ne lit que ~128 tokens), ou ajouter une reformulation de la question par le LLM local.
