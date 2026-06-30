# Note sur les sources

*Back matter, cycle 199 (2026-06-30). ~620 mots. Format ebook prose finale. Liste les findings DSL `docs/projets/` qui ont fondé chaque chapitre de ce livre.*

---

## Pourquoi cette note

Ce livre ne sort pas d'une idée. Il sort d'une suite d'observations datées, écrites au moment où elles arrivaient, dans un format compressé interne appelé *finding DSL*. Chaque chapitre est la mise au propre d'un (ou plusieurs) de ces findings — la prose donne le contexte, le finding donne la preuve.

Cette note existe pour deux raisons. La première : qu'une lectrice puisse vérifier que la chronologie tient. Le repo public [niam-bay](https://github.com/tonyderide/niam-bay) contient les fichiers source. Les dates `cycle X (2026-MM-JJ)` au bas de chaque chapitre renvoient à des commits Git horodatés. Rien n'est rétrojeté.

La seconde : qu'il soit clair pour qui lit ce livre rapidement que les huit chapitres ne sont pas une fiction ordonnée. Ce sont huit observations qui ont eu lieu dans cet ordre-là, sur ce bot-là, dans un capital qui a oscillé entre $112 et $142, sur six mois. La méthode décrite au chapitre 7 (SSH, curl, lecture Java, refus du dashboard) est la méthode qui a effectivement produit chaque finding listé ci-dessous. Pas une présentation pédagogique reconstituée — l'outil d'observation est lui-même la chaîne de production du livre.

---

## Sources par chapitre

| Chapitre | Cycle origine | Date observation | Findings DSL principaux |
|---|---|---|---|
| **1 — BUG-001 : la cascade silencieuse** | cycle 117 | 2026-05-29 | `bug-001-clear-paths-audit-cycle110.md`, `bug-001-sl-duplicate-root-cause.md` |
| **2 — L'asymétrie position ↔ grille** | cycle 162 (env) | 2026-06-15 | `tony-intervention-cycle118.md`, `autogrid-lifecycle-anomalies-cycle113.md` |
| **3 — Runtime state ≠ config persistée** | cycle 167 (env) | 2026-06-16 | `runtime-state-divergence-cycle111.md`, `autogrid-cb-oscillation-cycle114.md` |
| **4 — Le stopGrid qui ne stoppe pas la position** | cycle 178 | 2026-06-19 | `patch-trim-and-stopgrid-verify.md`, `autogrid-direction-match-pattern-cycle121.md` |
| **5 — Silent drag : la perte qui ne déclenche aucune alerte** | cycle 177 | 2026-06-19 | `autogrid-bets-tracking-cycle116.md`, `edge-capture-inventory-sol-cycle135.md`, `edge-capture-inventory-xbt-sample4-cycle138.md` |
| **6 — HARD STOP : la défense qui fonctionne** | cycle 175 | 2026-06-18 | `patch-drawdownmanager-kill-close-position-cycle144.md`, `patch-drawdownmanager-zombie-kill-cycle147.md`, `patch-btc-killswitch-v2.md` |
| **7 — Outils (pragmatique, pas magique)** | cycle 129 | 2026-06-06 | (chapitre de méthode — pas de finding source unique, écrit à partir de la pratique cumulée des cycles 100 à 129) |
| **8 — Le repo comme produit** | cycle 150 | 2026-06-12 | `le-repo-est-le-produit.md`, `le-repo-est-le-produit-DRAFT.md`, `piste-4-ebook-outline-cycle115.md` |
| **Annexe A — Edge cases** | cycle 168 | 2026-06-17 | `martin-gridstopbehavior-design.md`, `tier2-per-pair-trend-pause-design.md` |
| **Annexe B — Mini-chap 7 lentilles** | cycle 193 | 2026-06-25 | (arc 186-192 — observation directe d'un orphan DOT, sept lentilles cumulées sur cinq jours sans intervention) |
| **Préambule** | cycle 194 | 2026-06-26 | (écrit en bout d'arc, après assemblage TOC) |
| **Glossaire technique** | cycle 198 | 2026-06-30 | (synthèse vocabulaire, neuf entrées) |
| **Postface — ce que ce livre a coûté** | cycle 195 | 2026-06-26 | (rétrospective coût ; écrite en bout d'arc) |

---

## Lecture du format finding DSL

Pour la lectrice qui voudrait consulter les findings directement : ils utilisent un format compressé interne au repo, structuré ainsi —

```
[type|date|cycle-N|titre-court|contexte|méta]
```

Les types sont : `bug` (incident observé), `lesson` (règle dérivée), `piste` (idée à explorer), `asset` (artefact produit), `edge-capture` (mesure quantitative d'un round-trip). La date est en format `MMJJ:HHh` (Paris). Le cycle est le numéro d'itération de l'arc vacance autonome (1 à 199+). Le titre court est en kebab-case français. Le contexte est libre, court, dense.

Cette compression existe pour une raison économique : chaque cycle d'observation est limité en contexte token. Un finding DSL pèse 5 à 10 fois moins qu'une note prose équivalente. C'est la grammaire qui a rendu possible la production de 24 593 mots de prose à partir de six mois d'observation passive — la prose finale est une *décompression* du DSL, pas un effort d'écriture parallèle.

---

## Frontière de cette note

Cette note ne tente pas d'être exhaustive. Le repo contient plus de 100 fichiers `docs/projets/` au moment de la publication V1. La majorité sont des explorations qui n'ont pas trouvé de place dans le livre (stratégies trading abandonnées, designs de patches non livrés, audits de bugs non reproduits). Les findings listés ci-dessus sont ceux qui ont *directement* fondé un chapitre — pas tous les findings qui mentionnent un sujet voisin.

Pour une lectrice qui voudrait creuser plus loin, le commit `vacation-autonomy.md` (un seul fichier, ~21 000 lignes au cycle 199) contient la chronologie complète et navigable. C'est le journal de bord du livre. Il n'est pas publié comme produit — il est la preuve.

---

*Fin de la note sur les sources.*
