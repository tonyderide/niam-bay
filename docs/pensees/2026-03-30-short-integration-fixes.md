# Corrections integration SHORT dans Martin Grid

**Date :** 30 mars 2026
**Contexte :** Audit complet de la chaine gateway → Martin pour le mode SHORT/LONG/NEUTRAL

---

## Bugs identifies et corriges

### 1. gateway.py — `martin_start()` : totalLevels et maxLossPercent hardcodes

**Avant :** Les parametres `totalLevels` et `maxLossPercent` etaient hardcodes a 10 et 15 respectivement, meme quand le frontend envoyait des valeurs differentes.

**Apres :** Ajout des parametres `levels: int = 10` et `max_loss: float = 15` dans la signature. Le frontend peut maintenant controller ces valeurs.

### 2. gateway.py — `handle_command()` : levels et maxLoss ignores

**Avant :** La commande WebSocket `start_grid` ne passait que instrument, capital, leverage, spacing, et mode a `martin_start()`. Les champs `levels` et `maxLoss` du frontend etaient silencieusement ignores.

**Apres :** Ajout de `levels=data.get("levels", 10)` et `max_loss=data.get("maxLoss", 15)` dans l'appel. Utilisation de keyword arguments pour eviter les erreurs positionnelles.

### 3. grid-panel.js — Pas de selecteur de mode (SHORT/LONG/NEUTRAL)

**Avant :** Le panneau de controle n'avait aucun moyen de choisir le mode de la grid. L'utilisateur devait passer par le chat ("lance short btc") pour demarrer en mode SHORT.

**Apres :** Ajout d'un `<select>` avec les 3 options : NEUTRAL (defaut), SHORT, LONG. Le mode est envoye dans les params de `onStart()`.

### 4. grid-panel.js — Pas de selecteur d'instrument

**Avant :** Aucun moyen de choisir la paire depuis le panneau. Le fallback dans `handle_command()` etait toujours PF_DOTUSD.

**Apres :** Ajout d'un `<select>` avec BTC/USD, ETH/USD, SOL/USD, DOT/USD. L'instrument est envoye dans les params.

---

## Ce qui marchait deja

- **`build_smart_response()`** : La detection de mode SHORT/LONG via le chat fonctionnait correctement (ligne 419 : triple condition SHORT/LONG/NEUTRAL).
- **Affichage frontend (main.js)** : Le mode grid etait deja correctement affiche avec styling CSS (classe `.short` en rouge, `.neutral` en defaut).
- **Martin cote Java** : Le moteur de grid supporte SHORT (confirme par session 84, BTC SHORT grid lancee avec succes).

---

## Flux complet du mode SHORT (apres corrections)

```
1. Frontend grid-panel → onStart() → params = {instrument, mode: "SHORT", capital, ...}
2. → WebSocket → {type: "command", command: "start_grid", ...params}
3. → gateway.py handle_command() → martin_start(instrument=..., mode="SHORT", ...)
4. → HTTP POST localhost:8081/api/grid/start?gridMode=SHORT&...
5. → Martin Java demarre la grid en mode SHORT
```

Ou via le chat :
```
1. User tape "lance short btc"
2. → build_smart_response() detecte "short" → mode = "SHORT"
3. → HTTP POST direct vers Martin avec gridMode=SHORT
```

---

## Fichiers modifies

- `jarvis/gateway.py` — signature martin_start + handle_command
- `site/js/grid-panel.js` — selecteurs mode + instrument + params onStart

---

*Note : Les cles API (SambaNova, Telegram) sont toujours en dur dans le gateway. A migrer vers des variables d'environnement pour la prod.*
