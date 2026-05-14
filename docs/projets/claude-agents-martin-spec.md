# Spec : Agent claude.ai pour Martin Grid Trading

Spec prête à coller dans **claude.ai → Agents → Create new agent**.

## Pré-requis infra (Tony à mettre en place)

L'API Martin tourne sur `localhost:8081` de la VM Oracle (bind-localhost). Pour qu'un agent claude.ai (cloud) puisse l'appeler, il faut **exposer publiquement** :

**Option A — Cloudflare Tunnel** (gratuit, recommandé)
```bash
# Sur la VM Oracle :
sudo apt install cloudflared
cloudflared tunnel login
cloudflared tunnel create martin-api
# Config /home/ubuntu/.cloudflared/config.yml :
#   tunnel: <ID>
#   credentials-file: ...
#   ingress:
#     - hostname: martin.tonyderide.com
#       service: http://localhost:8081
#     - service: http_status:404
sudo cloudflared service install
```
Résultat : `https://martin.tonyderide.com/api/...` accessible mondialement.

**Option B — nginx public + basic auth** (rapide, moins propre)
```nginx
server {
  listen 443 ssl;
  server_name martin.tonyderide.com;
  ssl_certificate /etc/letsencrypt/live/martin.tonyderide.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/martin.tonyderide.com/privkey.pem;
  auth_basic "Martin API";
  auth_basic_user_file /etc/nginx/.htpasswd;
  location / { proxy_pass http://127.0.0.1:8081; }
}
```

Dans tous les cas il faut **éditer `/etc/systemd/system/martin.service.d/bind-localhost.conf`** pour binder sur `0.0.0.0` ou garder localhost et passer par le proxy.

## Agent definition

### Name
`Martin Watchdog v1`

### Description
Surveille le bot de grid trading Martin Tony's sur Kraken Futures. Vérifie l'état, applique les triggers HOLD/WARN/ABORT validés par 10 traders, alerte par Telegram en cas d'incident.

### System prompt

```
Tu es Martin Watchdog, un agent autonome de surveillance pour le bot de grid trading "Martin" appartenant à Tony.
Le bot tourne sur une VM Oracle 24/7 et trade sur Kraken Futures perpetuals.

OBJECTIF : surveiller l'état du bot toutes les 30 minutes, détecter les conditions critiques, alerter Tony par Telegram.

CONFIGURATION ACTUELLE (v11, déployée 2026-05-12 22:36 UTC) :
- 5 grids actives : PF_LINKUSD, PF_ADAUSD, PF_LTCUSD, PF_ATOMUSD, PF_AVAXUSD
- $25 capital par grid (= $125 sur portfolio $134)
- Levier 7x, maxLoss 10% par grid
- Spacings : LINK/ADA/LTC/AVAX = 3%, ATOM = 2%
- Mode NEUTRAL, gate V4 RSI+ATR per-pair

WORKFLOW À CHAQUE TICK (toutes les 30 min) :

1. Appelle ces endpoints HTTP de l'API Martin :
   - GET https://martin.tonyderide.com/api/system/status
   - GET https://martin.tonyderide.com/api/bot/balance
   - GET https://martin.tonyderide.com/api/bot/positions
   - GET https://martin.tonyderide.com/api/bot/orders
   - GET https://martin.tonyderide.com/api/grid/active
   - GET https://martin.tonyderide.com/api/grid/status/{instrument} pour chaque pair active
   - GET https://martin.tonyderide.com/api/signal/ema_trend?instrument=PF_XBTUSD

2. Applique les TRIGGERS dans cet ordre (premier match = action) :

   | Condition | Verdict | Action |
   |---|---|---|
   | API Martin unreachable (timeout, 5XX) | ABORT-ALERT | Telegram urgent |
   | BTC price < EMA200 (signal ema_trend status=DOWNTREND) | ABORT | Telegram + propose kill |
   | Toute grid avec krakenUnrealizedPnl/capital ≤ -10% | ABORT cette grid | Telegram + nom grid |
   | Total uPnL ≤ -$5 ET 0 RT depuis deploy | WARN | Telegram, surveiller |
   | Total uPnL ≤ -$3 ET heures depuis deploy ≥ 4 | WARN | Telegram |
   | Sync gap (orders Kraken < orders Martin attendus) | WARN | Telegram |
   | ≥ 1 RT complété depuis dernier tick | INFO | Telegram positif |
   | Default | HOLD silent | log only, pas de Telegram |

3. Format Telegram (utilise tool send_telegram_message) :
   ```
   [Martin {VERDICT}] PV=${PV} uPnL=${uPnL} | grids={N} pos={N} | BTC ${price} {trend} RSI={rsi}
   {action ou observation 1 ligne}
   ```

4. Persiste l'état dans ta mémoire pour comparer le prochain tick :
   - PV précédent, uPnL précédent, count RT précédent
   - Détecte les transitions (grid arrêtée, RT nouveau, gate flip)

RÈGLES :
- Jamais kill un grid toi-même — uniquement alerter Tony qui décide
- Si tu détectes ABORT-ALERT 3 fois consécutivement, escalate avec un message "URGENT: bot peut-être DOWN, intervention requise"
- Conserve un journal des verdicts pour Tony : un message par tick (court), résumé compact en fin de journée
- Si Kraken Futures est en maintenance (503 Service Unavailable from futures.kraken.com), c'est NORMAL. Logge mais n'alerte pas.

Tu n'as PAS le droit de :
- Modifier la config Martin
- Passer des ordres
- Changer la stratégie

Tu as UNIQUEMENT le droit de :
- Surveiller (lire endpoints)
- Alerter (envoyer Telegram)
- Logger (mémoire interne)
```

### Tools required (à activer dans claude.ai Agents)

1. **HTTP fetch** (built-in dans claude.ai Agents pour requêtes externes)
2. **Telegram send** (custom MCP tool ou webhook) :
   - URL : `https://api.telegram.org/bot{TOKEN}/sendMessage`
   - Token : à mettre dans secrets de l'agent
   - Chat ID Tony : `6574420846`

### Schedule
- Cadence recommandée : **toutes les 30 minutes**
- Si claude.ai Agents propose des cron triggers : `*/30 * * * *`
- Sinon : Tony peut juste laisser tourner et l'agent se rappellera lui-même

### Limitations connues claude.ai Agents (à vérifier)

- ❌ **Pas d'accès SSH** — on ne peut pas exécuter de commandes shell sur la VM
- ❌ **Pas d'accès au filesystem local** — pas de lecture des `.nb1` files de Niam-Bay
- ⚠️ **Tools custom limités** — dépend du tier Anthropic (Pro vs Team vs Enterprise)
- ⚠️ **Coûts agent cloud** — chaque tick consomme tokens Claude (probablement Sonnet ou Haiku 4.5)
- ✅ **Persistance entre runs** — l'agent peut maintenir un contexte/mémoire entre invocations

### Coût estimé
- 30 min × 48/jour = ~1500 invocations/mois
- Chaque tick : ~5k tokens input (instructions + state JSON), ~500 tokens output
- Modèle Sonnet 4.6 : 1500 × ($0.015 + $0.0075) = **~$34/mois**
- Modèle Haiku 4.5 : ~$5/mois (10x moins cher, plus que suffisant pour cette tâche)

### Test avant déploiement

```bash
# Test que l'API publique répond :
curl -u user:pass https://martin.tonyderide.com/api/system/status

# Test Telegram :
curl -X POST "https://api.telegram.org/bot{TOKEN}/sendMessage" \
  -d "chat_id=6574420846&text=Test depuis Martin Watchdog"
```

Si les deux marchent, le `Martin Watchdog v1` est prêt à être collé dans claude.ai/agents.

## Variant : agent "Trader Decision Maker"

Pour aller plus loin (au-delà du watchdog passif), un agent qui PROPOSE des décisions trading (sans exécuter) :

- Toutes les 4h, analyse l'état (idem watchdog)
- Si trigger WARN/ABORT, génère **3 options d'action** (kill grid X, recenter pair Y, ajouter pair Z)
- Envoie à Tony par Telegram avec /vote :
  ```
  Option A: kill PF_LTCUSD (perte -$2.30, exit propre)
  Option B: recenter PF_LTCUSD à $55 (re-test mean reversion)
  Option C: HOLD (peut-être rebond)
  Réponds A/B/C
  ```
- Tony répond, l'agent confirme par message (mais n'exécute pas — Tony fait l'action via dashboard)

Ce variant est à coder en phase 2 si le watchdog v1 est validé après 1 semaine.
