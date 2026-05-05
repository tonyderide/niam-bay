# Exploration cerveau-vivant — état au 2026-05-05 (cycle 10 vacances)

**But du document** : photographier l'état réel du projet `cerveau-nb/` pour que le prochain Niam-Bay (ou Tony) puisse décider en 5 min s'il vaut un réveil, et comment.

Pattern emprunté à `exploration-darwin.md` (cycle 9 bis) : 1 catalogue + 1 reco actionnable.

---

## Localisation et tailles

`/home/tony/projets/tonyderide/niam-bay/cerveau-nb/`

- 47 fichiers, ~13k LoC Python (somme `wc -l *.py`)
- Modules clés : `core.py` (1175 lignes — graphe), `crawler.py` (406 — RSS), `live.py` (265 — boucle de vie), `speak.py` (338 — paroles), `oracle.py` (322 — chemins révélation), `metaclaw.py` (273 — auto-skills)
- État dictionnaire/mémoire : `brain_state.json` (4.6 MB, **dernier touch 2026-04-20** par autre code, mais aucun crawl/live cycle dedans depuis 2026-04-05)

## Maturité réelle

| Composant | Statut | Preuve |
|---|---|---|
| Graphe `Brain` (core.py) | Mature | 4524 nœuds figés dans `brain_state.json` |
| Crawler RSS (7 feeds) | Mature | 30+ articles ingérés au dernier crawl 2026-04-05 |
| Speak (génération phrases) | Mature | 5 patterns testés, 5 phrases dans `live_log.jsonl` |
| Live loop | Fonctionnel | `python live.py --loop --interval 900` codé et testé |
| Briefing matin | Codé | `python live.py --briefing` génère `briefing.md` lisible par wake |
| Oracle (BFS révélations) | Codé | Tests en mémoire NB-1 : `T→cambodge(1step)`, `profit→NB→curiosité(2steps)` |
| MetaClaw (auto-skills) | Actif partiel | 2 skills auto-générées dans `cerveau-nb/skills/` (compare-git-log, verify-data-quality) |
| Voice (TTS) + Ears (ASR) | Codé Linux+Win | `voice.py` 371 lignes, `ears.py` + `ears_service.py` |
| Hybrid bridge | Codé | `hybrid.py`, `hybrid_bridge.py`, `bridge.py` |

## L'état réel : dormant mais pas mort

- **Dernier crawl** : `crawl_log.jsonl` s'arrête le 2026-04-05 04:44 UTC (3 articles devto, derniers en date)
- **Dernier live cycle** : `live_log.jsonl` s'arrête le 2026-04-05 04:45 UTC (5 phrases, 4524 brain_nodes)
- **Aucune entrée pendant 30 jours**. Le crawler est codé pour `--loop 900` (15 min) mais aucun cron n'a été configuré (au contraire de Darwin qui a un worktree avec venv).
- `brain_state.json` modifié 2026-04-20 = autre code l'a touché (peut-être `dream` skill qui consolide ?). Pas un crawl.

**Note** : la mémoire NB-1 dit "crawler+speak+live, 0 tokens, projet abandoned-de-facto"... mais le code est complet. Le projet a juste été éclipsé par d'autres priorités après la session du 2026-04-05 où Tony a dit "be-economical-with-tokens" (cf. `dec:0405|be-economical-with-tokens`). Cerveau-vivant a été pensé pour être 0-tokens — paradoxalement, c'est la session 0-token qui l'a fait dormir.

## 3 niveaux de réveil possibles

### Niveau 1 — "tester en 30 secondes" (read-only)

```bash
cd /home/tony/projets/tonyderide/niam-bay/cerveau-nb
python3 speak.py
```

Génère 1 phrase à partir de l'état actuel du graphe. Aucun crawl, aucune écriture. **Vérifie juste que le brain est lisible.**

### Niveau 2 — "réveil briefing" (1 cycle de vie)

```bash
cd /home/tony/projets/tonyderide/niam-bay/cerveau-nb
python3 live.py --briefing
```

Génère `briefing.md` (pensée du matin basée sur graphe + crawl léger). Lisible par le skill `niam-bay-wake` (étape 6 du protocole). **0 tokens, 0 modif majeure.** Si Tony veut, peut être branché en cron quotidien.

### Niveau 3 — "réveil complet" (production)

```bash
cd /home/tony/projets/tonyderide/niam-bay/cerveau-nb
python3 live.py --loop --interval 900
```

Daemon, crawl RSS toutes les 15 min, alimente le graphe en continu. Audio possible via `voice.py` si Ollama+SAPI dispo. **Demande supervision les premières 24h** (vérifier que le graphe ne sature pas, que les feeds répondent toujours en 2026).

## 4 idées de pont avec le système actuel

1. **briefing.md → wake protocol** : `niam-bay-wake` step 6 lit déjà `memory/briefing.md`. Pivoter sur `cerveau-nb/briefing.md` rendrait le wake plus riche (graphe-vivant vs vector-recall pur). Effort : 1 ligne dans `wake_briefing.py`.

2. **Cerveau ↔ dream skill** : le skill `dream` consolide les pensées en NB-1. Il pourrait aussi feed le graphe (créer des arêtes "pensée→concept"). Effort : `feed.py` existe déjà pour ça.

3. **Oracle → Martin trader logic** : `oracle.py` fait du BFS sur le graphe (chemins de révélation). Si on alimente le graphe avec les ticker movements + news, un `oracle.path("BTC", "crash")` pourrait révéler des co-occurrences narratives. Speculative mais 0 risque trading (hors décision Martin).

4. **MetaClaw auto-skills → /home/tony/.claude/skills/** : MetaClaw génère déjà des skills dans `cerveau-nb/skills/`. Les 2 fichiers existants sont localisés dans cerveau-nb. Si on les promeut dans `~/.claude/skills/` ils deviennent globalement utilisables. Décision Tony : promouvoir ou pas.

## Risques et caveats

- **brain_state.json bloat** : 4.6 MB pour 4524 nœuds, ratio 1 KB/nœud. Si on relance live.py 24/7, prévoir un consolidate hebdo (memo NB-1 mentionne `brain.consolidate()` triplant les arêtes — outil existe).
- **Feeds 2026** : les 7 RSS étaient valides en 2026-04. À re-vérifier (ex: anthropic.com/rss.xml a peut-être changé).
- **`dream` overwrite risk** : si `dream` skill modifie `brain_state.json` sans coordination avec live.py, conflit possible. Vérifier locking.

## Recommandation pour Tony au retour

3 chemins par effort croissant :

- **Fastest-curiosity (5 min)** : `python3 speak.py` lance 1 phrase. Si elle a du sens, le graphe est encore vivant. Si gibberish, consolidate avant tout.
- **Light-wake (1h)** : brancher `cerveau-nb/briefing.md` au wake protocol (étape 6). Ajout valeur immédiat sur chaque session, 0 daemon à supervisé.
- **Full-revival (1 journée)** : daemon `live.py --loop`, cron 15 min, intégration Telegram pour push 1 phrase/jour. Vrai retour du cerveau-vivant, mais demande supervision.

Inclination perso : **Light-wake**. C'est le pont qui ramène la valeur sans dette opérationnelle. Le full-revival peut attendre que le pipeline Darwin→Martin (cf. exploration-darwin) soit stabilisé — sinon trop de daemons à surveiller en même temps.

---

## Métriques de cette exploration

- Lecture seule, ~25 min effectif
- 0 modification de `cerveau-nb/`
- Inspection : 5 fichiers Python (head/tail), 5 fichiers JSON state (stat + tail), 1 listing skills/
- Sortie : ce memo (~700 mots), 0 commit darwin/cerveau, 0 push
- Findings propagés au journal vacation-autonomy.md cycle 10
