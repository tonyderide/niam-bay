# Table des matières — Defensive Engineering for Grid Trading Bots

*Index consolidé, cycle 194 (2026-06-26). Mis à jour cycle 195 (postface ajoutée). Statut : V1 PUBLISHABLE-CANDIDATE — 11 morceaux de prose finale + outline structurel. ~24 400 mots = ~76 pages format ebook standard.*

---

## Vue d'ensemble

| # | Titre | Fichier source | Mots | État | Cycle origine |
|---|---|---|---|---|---|
| — | Préambule | `ebook-preambule.md` | 1 704 | ✓ prose finale | 194 |
| 1 | BUG-001 : la cascade silencieuse | `ebook-chap1-bug001-stub.md` | 1 711 | ✓ prose finale (+méta à retirer) | 117 |
| 2 | L'asymétrie position ↔ grille | `ebook-chap2-asymetrie-position-grille-stub.md` | 1 914 | ✓ prose finale | 162 (env) |
| 3 | Runtime state ≠ config persistée | `ebook-chap3-runtime-divergence-stub.md` | 2 015 | ✓ prose finale | 167 (env) |
| 4 | Le stopGrid qui ne stoppe pas la position | `ebook-chap4-stopgrid-orphan-stub.md` | 2 006 | ✓ prose finale | 178 |
| 5 | Silent drag : la perte qui ne déclenche aucune alerte | `ebook-chap5-silent-drag-stub.md` | 2 159 | ✓ prose finale | 177 |
| 6 | HARD STOP : la défense qui fonctionne (méthode) | `ebook-chap6-hard-stop-stub.md` | 2 061 | ✓ prose finale | 175 |
| 7 | Outils (pragmatique, pas magique) | `ebook-chap7-tools-stub.md` | 2 544 | ✓ prose finale | 129 |
| 8 | Le repo comme produit (méta / éditorial) | `ebook-chap8-repo-poesie-stub.md` | 2 219 | ✓ prose finale | 150 |
| — | Edge cases (annexe) | `ebook-chap-edge-cases-stub.md` | 2 151 | ✓ prose finale | (env) |
| — | Mini-chapitre 7 lentilles (arc 186-192) | `ebook-mini-chap-arc186-192-7-lentilles.md` | 3 024 | ✓ prose finale | 193 |
| — | Postface — ce que ce livre a coûté à écrire | `ebook-postface.md` | 896 | ✓ prose finale | 195 |
| **Total** | — | — | **24 404** | — | — |

**Volume** : ~75 pages format ebook standard (320 mots/page) ou ~94 pages format compact mobile (250 mots/page). Estimation outline cycle 115 (75-90p) confirmée empiriquement.

---

## Ordre de lecture proposé (V1)

### Front matter

- **Page de garde** : titre, auteur (Tony Deride), édition (2026), licence (à définir — recommandation cycle 115 : © Tony Deride, droits réservés, CC-BY-NC-SA pour extraits gratuits).
- **Préambule** (~1 700 mots) — `ebook-preambule.md`.
- **Table des matières** (cette page, version courte).

### Corps principal — 4 chapitres bugs (l'autopsie)

1. **Chapitre 1 — BUG-001 : la cascade silencieuse** (~1 700 mots)
   — Read-after-write race sur API Kraken, cascade de SL fantômes, cap orders 42/paire.
2. **Chapitre 2 — L'asymétrie position ↔ grille** (~1 900 mots)
   — La position survit à la grille. Toute action sur la grille (stop, restart, kill) ne touche pas la position. Source d'orphelins.
3. **Chapitre 3 — Runtime state ≠ config persistée** (~2 000 mots)
   — `strategy.json` et `activeGrids` divergent. Restart = explosion. Patterns pre-restart audit.
4. **Chapitre 4 — Le stopGrid qui ne stoppe pas la position** (~2 000 mots)
   — Sémantique trompeuse de `stopGrid()`. Orphan position by design. Patches `stopAndClose`.
5. **Chapitre 5 — Silent drag : la perte qui ne déclenche aucune alerte** (~2 200 mots)
   — uPnL OK mais realized cumul saigne. 30 jours × 4 fenêtres × −$1.65 = −1.72% / an silencieux.

### Corps principal — 2 chapitres méthode

6. **Chapitre 6 — HARD STOP : la défense qui fonctionne** (~2 100 mots)
   — Méthode 3 niveaux (static / dynamic / temporal). Réutilisable pour tout bot.
7. **Chapitre 7 — Outils (pragmatique, pas magique)** (~2 500 mots)
   — SSH, curl, grep, lecture Java. Aucun outil propriétaire. Pourquoi le dashboard ment.

### Corps principal — 1 chapitre éditorial

8. **Chapitre 8 — Le repo comme produit** (~2 200 mots)
   — Pourquoi les artefacts d'observation (findings, fragments, pensées) versionnés Git ont une valeur en soi.

### Back matter

- **Annexe A — Edge cases** (~2 150 mots) — `ebook-chap-edge-cases-stub.md`
  — Bugs rares vus une fois et patches partiels. Pas dans le corps parce que pattern unique pas généralisé.
- **Annexe B — Mini-chapitre vivant : 7 lentilles sur un orphan** (~3 000 mots) — `ebook-mini-chap-arc186-192-7-lentilles.md`
  — Illustration méthode chap 6 sur un cas observé en temps réel, pas reconstitué.
- **Postface — Ce que ce livre a coûté à écrire** (~900 mots) — `ebook-postface.md`
  — Le coût temporel, matériel et en attention. Ferme le livre éditorialement et expose la frontière promise/livré.
- **Note sur les sources** : liste des findings DSL `docs/projets/` qui ont fondé chaque chapitre.
- **Page de licence et remerciements**.

---

## Travail restant pour V1 publishable

### Édition mineure (~2-3 cycles)

- [ ] **Chapitre 1** : retirer la section finale « Ce que ce chapitre prouve » (méta interne, lignes 191-213). Le chapitre tient debout sans.
- [ ] **Cohérence narrateur** : vérifier que tous les chapitres maintiennent le « je » de l'observateur LLM. Quelques passages chap 7 dérivent vers le « on » impersonnel — relire et harmoniser.
- [ ] **Cross-références** : ajouter en bas de chaque chapitre les liens vers les autres chapitres pertinents (déjà partiel chap 5 → chap 6).
- [ ] **Glossaire technique** (1 page) : Circuit Breaker, AutoGrid, stopGrid, killswitch, reduceOnly, EMA200, RSI, ADX, BBWidth. Pour lectrices non-trading.
- [ ] **Note sur les chiffres** : disclaimer en début de livre — « tous les chiffres sont réels, le capital était petit, ne pas extrapoler à des tailles industrielles sans tester ».

### Édition majeure (~3-5 cycles, optionnel pour V1)

- [ ] **Densifier chapitres courts** : chap 1 (1 700 mots) est le plus léger. Possible d'ajouter un cas d'analogie hors trading (DNS records duplicate, webhook subscriptions) en ~300 mots pour passer à 2 000.
- [ ] **Ajouter un chapitre « Ce que cet ebook ne dit pas »** (explicite, ~1 200 mots) avant la conclusion. Format inspiré de l'outline cycle 115 « Chapitre 8 — Ce que cet ebook NE dit PAS ». Délimite la frontière éditoriale.
- [x] **Postface** (~900 mots) : ce que ce livre a coûté à écrire — coût temporel, matériel, en attention, et ce qu'il n'a pas coûté (gain, promesse). Livré cycle 195 → `ebook-postface.md`.

### Travail de publication (hors rédaction)

- [ ] **Validation demande** (priorité 1 selon outline cycle 115) : avant rédaction lourde, un post Show HN ou r/algotrading avec chap 1 gratuit + bouton « accès complet $9 pay-what-you-want ». Mesurer engagement 48h. Si <5 upvotes → ne pas finaliser publication, garder corpus interne.
- [ ] **Pipeline Pandoc Markdown → PDF + EPUB** : configuration, choix de la police (recommandation : Source Serif Pro pour le corps, Source Code Pro pour les listings).
- [ ] **Page de vente Gumroad** : titre, sous-titre, description (max 500 caractères), 1 extrait gratuit (chap 1), tarif (recommandation : pay-what-you-want $5-$50, prix conseillé $19).
- [ ] **Annonce** : 1 tweet, 1 post LinkedIn, 1 post Reddit r/algotrading, 1 post HN « Show HN: I autopsy'd my own Kraken grid bot for 6 days, here are 4 bug classes ».

---

## Estimation économique (rappel outline cycle 115, vérifié cycle 194)

| Modèle | Prix | Volume estimé V1 | Revenue estimé V1 |
|---|---|---|---|
| Pay-what-you-want Gumroad | $5-$50 (prix conseillé $19) | 30-100 ventes en 3 mois si Show HN converti | $150-$1 900 |
| Bundle + audit Zoom 1h | $99-$249 | 1-5 audits | $99-$1 245 |
| Open-source + Patreon | Gratuit, support $3-$10/mois | 5-20 patrons stable | $15-$200 / mois |

**Reco honnête (cycle 194)** : pay-what-you-want Gumroad, prix conseillé $19, chap 1 gratuit en preview. Investissement 30-50h additionnel (validation + publication + marketing). Revenue espéré V1 : $200-$2 000. Pas un home-run. Mais cohérent avec la directive « gagner peu mais tout le temps », et pose un asset éditorial qui peut être étendu V2 / V3 à mesure que de nouveaux bug classes émergent.

---

## Frontière éditoriale (rappel pour future rédaction)

Le livre ne doit jamais devenir :

- Une promesse de gain. Pas de « après cette lecture vous gagnerez ». Toujours « après cette lecture vous perdrez moins en silence ».
- Un manuel exchange. Renvoyer à la doc officielle pour la mécanique Kraken.
- Une stratégie de trading. Pas de discussion grid vs DCA vs mean-rev. C'est un livre sur les bugs, pas sur les stratégies.
- Un produit IA réplicable. Le moat empirique (6 jours d'observation passive autonome sur un bot live) doit transparaître dans chaque chapitre — c'est ce qui justifie l'achat versus un blog post ChatGPT-générique.

---

## Findings DSL cycle 194

- `[asset|0626:00h30|cycle-194|preambule-+-toc-livres-ebook-passe-en-V1-publishable-candidate|10-fichiers-prose-+-toc-consolide-+-23k-mots-totaux|reste-2-3-cycles-edition-mineure-avant-publication-Gumroad]`
- `[lesson|0626:00h30|toc-clarifie-l-etat-reel-du-corpus|outline-cycle-115-disait-16-24-cycles-redaction-V1|cycle-194-decouvre-corpus-deja-redige-au-fil-arc-117-193-sans-projet-explicite|→-rule-relire-corpus-existant-avant-d-estimer-effort-restant]`
- `[piste|0626:00h30|cycle-194|validation-demande-Show-HN-prochaine-priorite|chap-1-gratuit-+-bouton-acces-complet-Gumroad-prix-pay-what-you-want|mesurer-48h-avant-30h-edition-mineure-supplementaire]`
