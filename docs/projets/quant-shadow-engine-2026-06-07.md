# Quant — Shadow Signal Engine (moteur d'apprentissage Martin)

**Créé :** 2026-06-07
**Repo :** `martin/quant` (backend Java/Spring Boot + DJL, frontend Angular)
**Statut :** fonctionne mais **ne persiste pas le modèle** → réapprend de zéro à chaque restart.

---

## Ce que c'est

Un moteur de signaux "shadow" (observe, **ne trade pas**) qui apprend en continu sur le flux de trades Kraken BTC.

- **Backend** : `martin-quant-0.1.0.jar`, port **8090** (local). Spring Boot.
- **Frontend** : Angular `quant/frontend`, `ng serve` port **4200** (price-chart, consensus-panel, volume-profile, robot-cards).
- **Pipeline ML** :
  - `QuantWsClient` ingère les trades Kraken (WebSocket).
  - `TripleBarrierLabeler` labellise les outcomes (méthode triple-barrière, López de Prado).
  - `ContinualTrainer` ré-entraîne **toutes les 6h** (min **100** exemples) → `DjlBestMomentModel` (réseau DJL).
  - `WalkForwardEvaluator` valide en walk-forward avant hot-swap dans `PredictionService`.
- **DB** : `quant/data/quantdb.mv.db` (H2) — persiste signaux + outcomes.

## État constaté (2026-06-06)

| | |
|---|---|
| Modèle | `trained: true` (dernier : 2026-06-06 16:28 UTC) |
| Walk-forward | 3 folds, **accuracy 71,7%**, 1401 échantillons |
| Outcomes résolus | 1867 (DB) |
| **WS Kraken** | **déconnecté** (`wsConnected:false`) — flux mort |
| Calibration | hit global **18%**, expectancy **-0,045R (négative)** |

## Les 2 problèmes

1. **🔴 Le modèle n'est pas persisté sur disque.** `PredictionService.model` est `volatile` en RAM (*"null until first successful train"*), `DjlBestMomentModel` n'a aucun `save`/`load`. Au restart → modèle perdu → "non entraîné" jusqu'au prochain retrain 6h. C'est LE bug principal ("il n'enregistre pas").
2. **🟠 WS Kraken déconnecté** → plus de ticks live → pas de prédiction temps-réel → le dashboard affiche le message de repli trompeur "modèle non entraîné".

⚠️ **Qualité** : expectancy négative (-0,045R) → le signal n'est pas rentable. C'est un *shadow engine* (apprend, ne trade pas) → OK pour l'instant, mais NE PAS brancher sur le trading tant que l'expectancy est négative.

## Plan de fix

### 1. Persistance modèle (priorité)
- `ContinualTrainer.retrain()` : après `model.train(...)`, `model.save(Path "quant/data/model")`.
- `DjlBestMomentModel` : implémenter `save(Path)` / `load(Path)` (DJL `Model.save` / `Model.load`).
- `PredictionService` / startup : charger le modèle disque s'il existe → plus de trou "non entraîné" après restart.

### 2. Reconnexion WS
- Diagnostiquer pourquoi `QuantWsClient` a lâché (le flux s'est coupé ~6 juin 01:21).
- Ajouter reconnexion auto + backoff si absent.

### 3. (Plus tard) Améliorer l'expectancy
- Tant que expectancy < 0, rester shadow. Itérer features / labeling / seuil (`BEST_ENTRY_THRESHOLD=0.55`) avant d'envisager un branchement trading via Martin Agency.

## Notes
- Isolé du bot Martin live (VM `:8081`) — ce travail ne touche pas le trading.
- Rebuild jar + restart `:8090` requis pour activer la persistance.
