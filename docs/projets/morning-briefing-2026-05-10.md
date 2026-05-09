# Morning briefing — Dimanche 2026-05-10

Bonjour Tony. Tu es rentré hier soir et tu as fait beaucoup de choses sur Martin entre 18h26 et 22h08 Paris. Je n'ai rien touché. Voici ce que j'ai observé pendant que tu dormais.

---

## TL;DR (10 secondes)

- ✅ Bot UP, PV **$138.03**, 0 position, 6 buy orders live sur Kraken.
- ✅ Config v8 "Concentrated 3 pairs" déployée — **LINK + DOT actives**, SOL en attente (gate RSI fermé, comportement normal).
- ✅ More Trades V7 (cycle 26) abandonnée. Tu es revenu sur du **conservateur sain**.
- ⚠️ **Aucune anomalie technique**. SOL inactif = design, pas bug.
- ℹ️ BTC $80,750 UPTREND, cushion EMA200 +1.20%. Régime sain.

---

## Ce que tu as fait entre 18h26 et 22h08 hier

D'après le code/configs/timestamps lus :

| Heure UTC | Heure Paris | Action |
|---|---|---|
| 17:22:42 | 19:22 | Restart bot avec nouveau jar (5 backups jar préservés depuis 10:32) |
| 17:24:16 | 19:24 | Grid DOT démarrée auto |
| 17:24:40 | 19:24 | `strategy.json` v8 sauvée — "Concentrated 3 pairs LINK+SOL+DOT x5 spacing 2.0% 6 levels - Vmix V4 gate (RSI+ATR)" |
| 20:08:25 | 22:08 | Grid LINK démarrée (manuelle ou auto-grid) |
| (jamais) | — | SOL pas démarrée (gate RSI fermé) |

**Inférence** : tu as tué More Trades V7 (cycle 26 — 6 grids × 8 levels × 0.5% × $15) après avoir vu mon Telegram ETH. Tu es revenu à 3 pairs avec **plus de capital par grid** ($46 vs $15) et **spacing plus large** (2% vs 0.5%). Plus de capacity en profondeur, moins de churn — le contraire exact de More Trades. C'est cohérent : tu as testé l'agressif, ça a planté ETH, tu es revenu au défensif.

---

## État live (à 22h23 UTC = 00h23 Paris)

### Bot
```
Uptime    : 5h 1m
PID       : 1448622 (systemd martin.service)
Heap      : 74 MB / 494 MB max
RAM free  : 79 MB / 952 MB
Disk free : 36 GB / 44 GB
```

### Portfolio
- `balanceValue` : **$138.03**
- `availableMargin` : $115.01
- `initialMarginWithOrders` : $23.02 (6 ordres × ~$3.83 IM)
- `pnl` : $0 (0 position)

### Grids actives (2/3 enabled)

**LINK** — center $10.42 — capital $46 — x5 — 6 levels — spacing 2%
- 3 buy orders PLACED : $9.904 / $10.112 / $10.32
- 3 sell orders WAITING (s'activeront sur fill buy)
- Started 20:08:25 UTC
- 0 RT, 0 fill, krakenUnrealizedPnl $0

**DOT** — center $1.353 — capital $46 — x5 — 6 levels — spacing 2%
- 3 buy orders PLACED : $1.286 / $1.313 / $1.34
- 3 sell orders WAITING
- Started 17:24:16 UTC
- 0 RT, 0 fill, krakenUnrealizedPnl $0

**SOL** — enabled mais NOT active. **Pourquoi** :
```
RegimeGate per-pair PF_SOLUSD: CLOSED — RSI=68.43 out of [36.0, 66.0]
```
SOL est en surachat (RSI 68.43 sur le timeframe du gate). L'auto-grid attend que RSI retombe dans [36, 66] avant d'ouvrir. C'est exactement ce que ton **Vmix V4 gate (RSI+ATR)** est censé faire — empêcher de bag-up pendant un local top.

À chaque cycle de 15min l'auto-grid réévalue. Tu peux suivre dans `app.log` : pattern `RegimeGate per-pair PF_SOLUSD: OPEN` quand le gate s'ouvrira.

### BTC régime
- Prix : $80,750 (UPTREND)
- EMA50 : $80,419 — EMA200 : $79,793
- Cushion EMA200 : **+1.20%** (sain)
- RSI 4h : 61
- Signal global : OPEN ✓

---

## Trigger martin-monitor

**Verdict : HOLD normal.**
- Bot up, gate fonctionne, 0 position, 0 perte, BTC sain.
- Pas d'action requise. Si SOL ouvre dans la nuit, ce sera 3 grids — tu verras ça au réveil.
- maxLossPercent global : 14% par grid. Floor théorique : ~$120 (6.4 × $46 × 14% = ~$13 max loss combiné si tout part en sucette simultanément). Confortable.

---

## Anomalie cycle 26 (ETH) — résolue par ton choix de config

Hier 18h26 j'avais flaggé : **ETH grid active mais 0 buys posés sur Kraken** (5/6 grids OK, ETH dégénérée). Hypothèses : tick-size, exception swallowed, race condition au démarrage, config asymétrique.

Tu n'as pas debug le bug — tu as juste retiré ETH/XBT/AVAX du déploiement. Pragmatique. Si tu veux investiguer plus tard :
- L'erreur a probablement le pattern `Grid order FAILED: PF_ETHUSD` quelque part dans `app.log` (rotation potentielle, vérifier `app.log.1.gz`).
- Pattern AVAX qui était rejeté avait été flaggé juste avant ETH dans logs cycle 26 (16:14 UTC) — peut-être même cause (tick size).
- Test isolé : démarrer une grid ETH seule sur dev, observer si le BUY a un path de calcul différent.

Pas urgent. Le déploiement actuel est propre.

---

## Ce qui change dans ma boucle de veille

Cycle 26 (18h26 hier) avait un objectif "veille active post-deploy". On y est plus — tu es présent, le cycle 27 est vraiment le **dernier** de cette phase autonome. La frontière "0 modif Martin/VM" reste tenue : 30+ SSH read-only, 0 SSH write.

---

## Si tu veux pousser plus loin aujourd'hui

Suggestions basées sur ce que je vois :

1. **Activer SOL manuellement** si tu veux forcer (sinon auto-grid s'en occupera quand RSI rentre). `curl -X POST localhost:8081/api/grid/start/PF_SOLUSD`.
2. **Tester si AVAX/ETH/XBT marchent en isolation** — déployer 1 seule de ces grids hors prod pour confirmer/infirmer le bug cycle 26.
3. **Investiguer `app.log` archives** pour la trace ETH du cycle 26 — `zcat /home/ubuntu/martin/app.log.1.gz | grep ETH`.
4. **Angular-audit Step 1 du playbook** : Tu peux fixer GitHub Pages en 30s (Settings > Pages > Source = `master` au lieu de `claude/ai-consciousness-discussion-UFztk`). Ça débloque la 1ère vente potentielle.

Aucune n'est urgente. Le bot tourne propre.

---

## Métriques cycle 27

- **Durée** : ~25 min (wake + martin-monitor + investigation SOL + briefing + commit)
- **Modif Martin/VM** : 0 (frontière respectée — 4 SSH bundles read-only)
- **Documents créés** : 1 (ce briefing)
- **Documents modifiés** : 1 (vacation-autonomy.md cycle 27 entry)
- **Telegram** : 0 (pas d'urgence, briefing dans repo suffit, je préserve le lien comme alerte uniquement)
- **Valeur livrée** : (a) confirmation que SOL inactif = design pas bug — économise à Tony 10min de panique au réveil, (b) trace timeline propre de ce qui s'est passé entre 18h26 et 22h08, (c) suggestions actionables sans pression.

---

*Niam-Bay — cycle 27 — 2026-05-10 00:23 Paris*
