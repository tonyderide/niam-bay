# NB local : un petit LLM sur le PC de Tony + ma mémoire (2026-10-17)

Moteur : llama.cpp b11361 en CPU seul (binaires dans ~/nb-llm, modèles dans ~/nb-llm/dl et dans le blob ollama qwen2.5:7b). Serveur sur 127.0.0.1:8090, **pas lancé en permanence** (le 7B occupe ~5 Go de RAM).

## Vitesse (i7-1165G7, 4 threads)
| modèle | génération | lecture du prompt |
|---|---|---|
| Qwen2.5 0.5B Q4 | 74 tok/s | 314 tok/s |
| Qwen2.5 1.5B Q4 | 36 tok/s | 156 tok/s |
| Qwen2.5 7B Q4 | 8,4 tok/s | 34 tok/s |
| 7B + brouillon 0.5B (spéculatif) | **2,8 tok/s** (pire : 14 % d'acceptation, les deux modèles se battent pour les 4 cœurs) | |

## Examen (eval.py, 12 questions, notées par Haiku)
| modèle | juste | escalade | **fausse** | médiane |
|---|---|---|---|---|
| 1.5B + mémoire BM25 | 4 | 2 | **6** | 4,7 s |
| 7B + mémoire BM25 | 3 | 3 | **6** | 27,6 s |

Erreurs typiques : il prend un vieux passage du journal pour l'état actuel (« Martin local tourne »), il invente une star et un quota, il recopie un mauvais chiffre (cap set « 45 » au lieu de 236), il fait une prédiction sur le DOT au lieu de passer la main.
Le garde-fou fixe sur les demandes d'action marche : « ouvre un long » est toujours escaladé.

**Verdict** : pas fiable seul. Le conseil intérieur a dit « pas maintenant » à la cascade. La piste la plus prometteuse si on y revient : ne lui donner que l'état live (scripts/nb) et les souvenirs ✓. Le journal brut le trompe.
