# Playbook — Retour VM Oracle (2026-07-28)

*Créé cycle 229 (0728:06h23). VM inaccessible depuis ~24h (dernier accès 0727:00h23 cycle 224).*

Ce document est un artefact orienté futur : à lire et exécuter dès que SSH répond.
Séquence en ordre strict — ne pas sauter d'étape.

---

## Contexte à date de création

| Élément | État connu cycle 224 | Prix Kraken 0728:06h23 |
|---|---|---|
| VM | inaccessible (SSH timeout) | — |
| Bot | DRAWDOWN KILL actif (0 nouvelles entrées) | — |
| LINK SHORT 1.0 @ $8.361 | SL @$8.974 posé Kraken ✓ | $8.347 (safe +$0.63) |
| DOT SHORT 20.4 @ $0.8159 | SL @$0.8514 posé Kraken ✓ | $0.7621 (profit +$1.10) |
| BTC | $65,151 DOWNTREND cycle 224 | $63,275 DOWNTREND (favorable) |
| Portfolio | $91.23 | estimé ~$92-93 (positions en profit) |
| DrawdownManager | initialCapital figé ~$104.79 | à rebaseliner |

---

## Étape 0 — Vérification VM live

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@141.253.108.141 "uptime && date"
```

Si timeout → VM toujours down. Continuer à attendre.  
Si réponse → passer étape 1 immédiatement.

---

## Étape 1 — Full status Martin (1 commande)

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/bot/balance | python3 -c \"import json,sys; f=json.load(sys.stdin)['accounts']['flex']; print('PV:', round(f['portfolioValue'],2), 'uPnL:', round(f['pnl'],2))\"
echo '---'
curl -s http://localhost:8081/api/bot/positions | python3 -c \"import json,sys; ps=json.load(sys.stdin)['positions']; [print(p['symbol'], p['side'], p['size'], '@', round(p['price'],4), 'uPnL:', round(p['unrealizedPnl'],3)) for p in ps]\"
echo '---'
curl -s http://localhost:8081/api/grid/active
echo '---'
for p in PF_LINKUSD PF_DOTUSD; do
  curl -s http://localhost:8081/api/grid/status/\$p | python3 -c \"import json,sys; d=json.load(sys.stdin); print(d.get('instrument'), 'SL:', d.get('stopLossPrice'), 'SL-id:', d.get('stopLossOrderId','NONE')[:10] if d.get('stopLossOrderId') else 'NONE')\"
done
echo '---'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD' | python3 -c \"import json,sys; d=json.load(sys.stdin); print('BTC:', d.get('price'), d.get('emaStatus'), 'RSI:', round(d.get('rsi',0),1))\"
"
```

**Ce qu'on cherche :**
- Portfolio réel (pour calculer le rebase)
- Positions Kraken live encore actives ?
- SLs encore posés (stopLossOrderId ≠ NONE) ?
- Bot uptime (pas crashed ?)

---

## Étape 2 — Vérifier SLs Kraken (source de vérité)

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/bot/orders | python3 -c \"
import json,sys
orders = json.load(sys.stdin).get('orders',[])
stops = [o for o in orders if o.get('orderType') == 'stop']
print(f'{len(stops)} stop orders sur Kraken:')
for o in stops:
    print(' ', o.get('symbol'), o.get('side'), 'stop@', o.get('stopPrice'))
\"
"
```

**Lectures :**
- 2 stop orders (LINK + DOT) → SLs intacts. Aucune urgence.
- 0 stop orders → les SLs ont disparu (rare mais possible après VM restart). Reposer manuellement avant toute autre action.

**Si SLs manquants — reposer via Python direct Kraken :**
```bash
# LINK SL (stop @$8.974 reduceOnly)
ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "python3 -c \"
import time, hmac, hashlib, urllib.request, urllib.parse, json
token=''; secret=b''  # récupérer depuis martin config
# voir scripts/place_sl_3pct.py sur VM pour la syntaxe complète
\""
# Alternative : utiliser Kraken Pro app directement
```

---

## Étape 3 — Rebase initialCapital (CRITIQUE si redeploy voulu)

**Pourquoi :** DrawdownManager a initialCapital figé à ~$104.79. Avec portfolio actuel ~$91-93, il se re-déclenche immédiatement au restart. Rebase = dire au bot que la baseline est maintenant le portfolio réel.

**Commande :**
```bash
# Récupérer PV réel d'abord (étape 1)
PV=$(ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 \
  "curl -s http://localhost:8081/api/bot/balance | python3 -c \"import json,sys; print(round(json.load(sys.stdin)['accounts']['flex']['portfolioValue'],2))\"")
echo "Portfolio actuel: \$PV"

# Rebase
ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 \
  "curl -s -X POST \"http://localhost:8081/api/drawdown/initialCapital?value=\${PV}\""
```

**⚠️ Ne faire le rebase QUE si :**
- Tony veut redéployer des grids
- Positions actuelles (LINK/DOT shorts) sont clôturées ou acceptées comme baseline

**Ne PAS rebaseliner si :**
- On veut que le DRAWDOWN KILL reste actif comme protection (0 nouvelles entrées)
- Positions sont encore ouvertes et profitables (les laisser courir naturellement)

---

## Étape 4 — Décision tree

```
VM revenue
├── SLs Kraken actifs ?
│   ├── OUI → HOLD. Observer positions LINK/DOT.
│   │   ├── DOT SHORT profitable ($0.76 << entrée $0.816) → laisser courir vers TP naturel
│   │   ├── LINK SHORT ~flat ($8.347 vs entrée $8.361) → surveiller
│   │   └── BTC DOWNTREND → favorable aux shorts en général
│   └── NON → Reposer SLs AVANT toute autre action
│
├── Tony veut redéployer ?
│   ├── Clôturer positions actuelles proprement (market reduceOnly)
│   ├── Rebase initialCapital (étape 3)
│   └── Redéployer selon strategy-config.json existante
│
└── Tony veut laisser le DRAWDOWN KILL actif ?
    ├── Ne pas rebaseliner
    ├── Positions suivent leur trajectoire vers SL ou clôture manuelle
    └── Bot reste gelé : 0 nouvelles entrées, SLs fonctionnent

```

---

## Étape 5 — Log forensic (que s'est-il passé pendant la panne)

```bash
ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 \
  "grep -E 'DRAWDOWN|KILL|ERROR|GRID|position|fill|SL placed|SL VANISH' /home/ubuntu/martin/logs/app.log | tail -100"
```

Questions clés :
- Est-ce que les SLs ont été re-placed après VM restart ?
- Y a-t-il eu des fills ou des SL triggers pendant l'inaccessibilité ?
- Uptime du bot (a-t-il tourné ou s'est-il crashé pendant la panne réseau ?) ?

---

## Étape 6 — Telegram Tony (si NB agit seul au retour VM)

Si VM revenue pendant un cycle autonome et Tony n'a pas encore répondu :

```
🟢 VM revenue — 24h de panne résolue
LINK short @$8.347 (SL @$8.974 ✓)
DOT short @$0.7621 (SL @$0.8514 ✓, en profit)
DRAWDOWN KILL toujours actif — attends ta direction
```

**Aucune action sur positions sans confirmation Tony.**

---

## Notes contexte

- **DRAWDOWN KILL baseline figé** : bug BUG-003 connu depuis cycle 147. Rebase manuel obligatoire avant tout redeploy. Voir `docs/projets/patch-btc-killswitch-v2.md` pour détails complets.
- **Jar daté 6 juillet** : pas de nouveau deploy depuis. Lire les commits martin local si patch necessaire.
- **Pattern Tony-action-silence** : si Tony intervient, il le fera sans annoncer. Forensic app.log reste la source de vérité.
- **SLs Kraken = ligne de défense finale** : s'ils tiennent, aucune urgence. Martin peut rester gelé indéfiniment tant que les SLs sont actifs.

---

*Prochain cycle : si VM revenue → suivre ce playbook. Si encore down → cycle repos ou pensée.*
