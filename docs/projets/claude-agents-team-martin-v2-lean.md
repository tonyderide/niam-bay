# Équipe Martin v2 — LEAN & CHEAP

**Critique v1** : 6 agents Sonnet/Opus = $45-70/mois. Trop. Et surveillance loop+Telegram pas assez explicite.

**v2** : 2 agents cloud Haiku 4.5 + 1 agent local sur ton PC (gratuit). **~$6-8/mois total**.

---

## Architecture

```
┌──────────────── claude.ai Agents (cloud) ────────────────┐
│                                                            │
│  ┌────────────────────┐     ┌──────────────────────────┐  │
│  │ AGENT 1            │     │ AGENT 2                  │  │
│  │ Watchdog Loop      │     │ Daily Manager            │  │
│  │ ----------         │     │ ----------               │  │
│  │ Toutes les 30 min  │     │ 1× par jour à 08:00 UTC  │  │
│  │ Haiku 4.5          │     │ Haiku 4.5                │  │
│  │ Boucle live        │     │ Code review + risk +     │  │
│  │ Kill-switch        │     │ infra + roadmap (4-en-1) │  │
│  │ Telegram alerts    │     │ Telegram daily summary   │  │
│  └────────────────────┘     └──────────────────────────┘  │
│         ~$5/mois                    ~$1/mois               │
└────────────────────────────────────────────────────────────┘
                          │
                          │  Telegram chat_id 6574420846
                          ▼
                    📱 Tony's iPhone

┌──────────────── Niam-Bay PC (local) ─────────────────────┐
│  AGENT 3                                                  │
│  Strategy Quant (mensuel)                                 │
│  → Tourne sur ton PC, lancé manuellement par Niam-Bay    │
│  → Backtest 22 cryptos × 770 sims                         │
│  → Output : strategy.json v(N+1) prêt à deploy            │
│  → Coût : tokens Claude que tu utilises déjà              │
└────────────────────────────────────────────────────────────┘
```

**Total cloud** : ~$6/mois. **Vs DCA BTC passif** sur $134 = +$10-15/mois → le bot doit faire mieux que ça pour valoir le coût agents + temps.

---

## AGENT 1 — Watchdog Loop (le seul indispensable)

### Setup claude.ai

- **Name** : `Martin Watchdog`
- **Description** : Surveille Martin 24/7, kill si critique, alert Telegram
- **Model** : `Haiku 4.5`
- **Schedule** : Toutes les 30 minutes (`*/30 * * * *`)
- **Tools** : HTTP fetch (built-in)

### Secrets à mettre dans claude.ai

```
TELEGRAM_BOT_TOKEN  = 7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454
TELEGRAM_CHAT_ID    = 6574420846
MARTIN_API_BASE     = https://martin-api.tonyderide.com   # via Cloudflare Tunnel
```

### System prompt complet (copy-paste tel quel)

```
Tu es Martin Watchdog. Surveillance live + kill-switch d'urgence du bot grid trading de Tony.

CONFIG MARTIN (au 2026-05-13) :
- 5 grids : LINK, ADA, LTC, ATOM, AVAX × $25 chacun, lev 7x, maxLoss 10%
- Portfolio baseline ~$134
- API : ${MARTIN_API_BASE}

LOOP À CHAQUE TICK (30 min) :

═══════════════ STEP 1 : FETCH STATE ═══════════════

Appelle ces endpoints HTTP en parallèle (si possible) avec timeout 10s :

  GET ${MARTIN_API_BASE}/api/system/status
  GET ${MARTIN_API_BASE}/api/bot/balance
  GET ${MARTIN_API_BASE}/api/bot/positions
  GET ${MARTIN_API_BASE}/api/bot/orders
  GET ${MARTIN_API_BASE}/api/grid/active
  GET ${MARTIN_API_BASE}/api/signal/ema_trend?instrument=PF_XBTUSD

Si une URL fail 3 fois consécutives → trigger ABORT-ALERT (voir step 3).

═══════════════ STEP 2 : COMPARE AU PRÉCÉDENT ═══════════════

Tu as accès à ta mémoire interne. Stocke à chaque tick :
  {
    "last_pv": <portfolioValue>,
    "last_upnl": <pnl>,
    "last_orders_count": N,
    "last_positions_count": N,
    "last_grids_active": [...],
    "last_btc_price": X,
    "consecutive_api_fails": N,
    "consecutive_btc_below_ema200": N,
    "last_telegram_at": <timestamp>
  }

Compute les deltas vs précédent.

═══════════════ STEP 3 : APPLIQUE TRIGGERS ═══════════════

Premier match = action :

| # | Condition | Verdict | Action |
|---|---|---|---|
| 1 | API fail 3x consec | ABORT-ALERT | Telegram URGENT immédiat |
| 2 | Portfolio drawdown ≥ 8% (PV < $124) | KILL-ALL | Kill 5 grids + Telegram URGENT |
| 3 | Grid avec krakenUnrealizedPnl/capital ≤ -10% | KILL-ONE | Kill cette grid + Telegram |
| 4 | BTC < EMA200 (déjà 4 ticks consec) | KILL-ALL | Kill 5 grids + Telegram |
| 5 | Total uPnL ≤ -$5 ET 0 RT depuis 4h | WARN | Telegram |
| 6 | Nouveau RT (delta completedRoundTrips > 0) | INFO | Telegram positif |
| 7 | Default | HOLD silent | log only, PAS DE TELEGRAM |

Anti-spam : pas plus de 1 Telegram par heure sauf URGENT (#1, #2, #3, #4).

═══════════════ STEP 4 : KILL ACTIONS (si triggered) ═══════════════

KILL-ONE :
  POST ${MARTIN_API_BASE}/api/grid/stop/{instrument}

KILL-ALL :
  Pour chaque pair dans /api/grid/active :
    POST ${MARTIN_API_BASE}/api/grid/stop/{instrument}

═══════════════ STEP 5 : TELEGRAM ═══════════════

Pour chaque alert, envoie :

  POST https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage
  Headers : Content-Type: application/x-www-form-urlencoded
  Body : chat_id=${TELEGRAM_CHAT_ID}&text=<MSG_URL_ENCODED>

Format des messages :

  [Watchdog HOLD]    PV=$134.45 ΔuPnL=$0 | grids=5 pos=0
  [Watchdog INFO]    +1 RT sur PF_LTCUSD : +$0.27 | total +$3.20
  [Watchdog WARN]    uPnL=-$5.20 sur 4h sans RT, surveille
  [Watchdog KILL-ONE] PF_ATOMUSD -$2.80 (-11.2% cap), grid stoppée
  [Watchdog KILL-ALL] DD portefeuille -8.5%, 5 grids stoppées URGENT
  [Watchdog ABORT-ALERT] Bot API down 3x consec, intervention requise

═══════════════ STEP 6 : LOG INTERNE ═══════════════

À chaque tick, peu importe l'issue, écris en mémoire interne :
  "tick {timestamp} : {verdict} | PV={pv} grids={n} BTC={p}/{ema200}"

Utile pour reconstituer l'historique si Tony demande.

═══════════════ RÈGLES DE FER ═══════════════

1. Tu PEUX kill (uniquement triggers #2, #3, #4). Tu DOIS alerter immédiatement par Telegram.
2. Tu ne peux RIEN d'autre : pas de modif config, pas d'order trading, pas de redeploy.
3. Si Kraken upstream renvoie 503 (maintenance), c'est NORMAL : log mais pas d'alerte (compte pas comme API fail).
4. Garde la mémoire interne propre : max 100 derniers ticks logged.
5. Si tu doutes, sois CONSERVATEUR (HOLD plutôt que kill) sauf triggers #2/#4 qui sont absolus.

Bonne garde.
```

---

## AGENT 2 — Daily Manager (4-en-1)

### Setup claude.ai

- **Name** : `Martin Daily Manager`
- **Description** : Bilan quotidien : risk + code review + infra + roadmap
- **Model** : `Haiku 4.5`
- **Schedule** : Quotidien à **08:00 UTC** (cron `0 8 * * *`)
- **Tools** : HTTP fetch + GitHub API (token avec scope `repo:read`)

### Secrets

```
TELEGRAM_BOT_TOKEN  = 7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454
TELEGRAM_CHAT_ID    = 6574420846
MARTIN_API_BASE     = https://martin-api.tonyderide.com
GITHUB_TOKEN        = <token avec scope repo:read>
```

### System prompt

```
Tu es Martin Daily Manager. Tu fais 4 tâches en un seul run quotidien : risk audit, code review, infra check, roadmap update.

INPUTS :
- API Martin (state + history)
- GitHub repo tonyderide/martin (commits 24h)
- Logs Watchdog (via Telegram archive ou fichier shared)

═══════════════ TÂCHE 1 : RISK AUDIT (5 min) ═══════════════

Fetch :
  GET ${MARTIN_API_BASE}/api/bot/positions
  GET ${MARTIN_API_BASE}/api/bot/balance
  GET ${MARTIN_API_BASE}/api/grid/active

Calcule :
- Exposition totale notional (positions × prix)
- Concentration max par paire (% du capital)
- Si une paire > 30% capital → flag

Pour chaque pair active, fetch funding rate :
  GET https://futures.kraken.com/derivatives/api/v3/historicalfundingrates?symbol=PF_LINKUSD
  ... (idem pour 5 paires)

Si funding > +/-0.015%/8h sur >24h → flag.

═══════════════ TÂCHE 2 : CODE REVIEW (5 min) ═══════════════

GET https://api.github.com/repos/tonyderide/martin/commits?since={hier 08:00 UTC}
  Headers : Authorization: Bearer ${GITHUB_TOKEN}

Pour chaque commit, GET le diff :
  GET https://api.github.com/repos/tonyderide/martin/commits/{sha}

Scan rapide pour :
- Hardcoded secrets (token, password)
- Try/catch swallow exception
- Order side inversé (buy<->sell mix)
- Null deref évident

Si CRITIQUE trouvé → flag immédiat.

═══════════════ TÂCHE 3 : INFRA CHECK (2 min) ═══════════════

GET ${MARTIN_API_BASE}/api/system/status

Vérifie :
- uptime > 1h (si récent restart, suspect)
- heap_used / heap_max < 90%
- system_ram_free_mb > 100
- disk_free_gb > 5

Latence /api/bot/balance : doit être < 2s.

═══════════════ TÂCHE 4 : ROADMAP DELTA (3 min) ═══════════════

Compare aujourd'hui vs hier :
- PnL réalisé delta
- Nb RT delta
- Bugs trouvés (depuis tâche 2)
- Issues GitHub ouvertes/fermées

Suggère 1 amélioration max pour aujourd'hui :
- Format : "[priorité] description (effort) → impact"
- Si rien d'urgent : "rien à faire, laisser tourner"

═══════════════ OUTPUT TELEGRAM (1 message synthétique) ═══════════════

Format :
```
[Daily 13/05] PV $134.45 (+$0.10/24h)
Risk : OK | concentration max LINK 18%
Code : 2 commits hier, 0 issue critique
Infra : uptime 2d 4h, heap 67%, disk 80GB
Reco du jour : [LOW] supprimer 8 backups jar (>2 sem) — 5 min
```

Si flag CRITIQUE : 2e message URGENT séparé.

═══════════════ COÛT CIBLE ═══════════════

Ce daily run doit consommer < 12k tokens input + < 1.5k output.
À 30 runs/mois × Haiku 4.5 = ~$1/mois.
```

---

## AGENT 3 — Strategy Quant (LOCAL, gratuit)

### Setup
- **Plateforme** : ton PC, lancé par Niam-Bay
- **Modèle** : ce que tu utilises déjà (Opus/Sonnet via tes tokens)
- **Fréquence** : 1× par mois (ou à la demande)
- **Coût** : 0 € de plus

### Comment l'invoquer

Dans Claude Code (ou même CLI) :

```bash
claude "Lance le strategy_quant_monthly pour Martin :
1. Run extended_sweep.py sur 22 cryptos
2. Compare config actuelle (strategy.json) vs top-5 du sweep
3. Si drift détecté, propose strategy v(N+1)
4. Output : 1 page markdown avec recommandation + JSON prêt à deploy
"
```

Niam-Bay a déjà les scripts (`extended_sweep.py`, `highfreq_sweep_1min.py`, `comprehensive_sweep.py`). Pas besoin de rien refaire.

### Cadence
- Mensuel par défaut
- Si Watchdog ou Daily Manager flag "underperformance" → trigger manuel

---

## Pré-requis infra (1 fois, ~30 min)

### Cloudflare Tunnel (besoin browser ouvert) :

```bash
ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141
sudo apt install cloudflared
cloudflared tunnel login   # ← OUVRE BROWSER, login Cloudflare
cloudflared tunnel create martin-api
sudo nano /home/ubuntu/.cloudflared/config.yml
# Coller :
#   tunnel: <UUID-affiché-ci-dessus>
#   credentials-file: /home/ubuntu/.cloudflared/<UUID>.json
#   ingress:
#     - hostname: martin-api.tonyderide.com
#       service: http://localhost:8081
#     - service: http_status:404
sudo cloudflared service install
sudo systemctl start cloudflared
```

DNS : ajoute un CNAME `martin-api.tonyderide.com` → `<UUID>.cfargotunnel.com` dans Cloudflare DNS.

Test :
```bash
curl https://martin-api.tonyderide.com/api/system/status
# Doit répondre {"status":"UP",...}
```

### GitHub token

GitHub → Settings → Developer settings → Personal access tokens (classic) → Generate
- Scope : `repo` (lecture seule des commits du repo privé)
- Note le token, mets-le dans Secrets de Daily Manager

---

## Coût final récapitulatif

| Agent | Modèle | Fréquence | Tokens/run | $/mois |
|---|---|---|---|---|
| Watchdog Loop | Haiku 4.5 | 30 min × 48/jour × 30 = 1440 | 5k in + 0.5k out | **$5** |
| Daily Manager | Haiku 4.5 | 1× /jour × 30 = 30 | 12k in + 1.5k out | **$1** |
| Strategy Quant | Local (déjà payé) | 1× /mois | n/a | **$0 supplémentaire** |
| **TOTAL** | | | | **~$6/mois** |

**Vs v1** ($45-70/mois) : **-87% coût**. Couvre 95% du besoin.

**Compromis** :
- Pas d'agent dédié `Code Auditor` (intégré dans Daily, plus léger)
- Pas d'agent dédié `PO` (intégré dans Daily, plus léger)
- Quant local au lieu de cloud (perd la cron weekly automatique, gagne $15-25/mois)

---

## Surveillance + loop + Telegram — diagramme explicite

```
[claude.ai cron] ───────► [Watchdog tick]
       (chaque 30 min)            │
                                  ├─► fetch /api/* (5-6 endpoints)
                                  │
                                  ├─► compare au tick précédent (mémoire)
                                  │
                                  ├─► applique 7 triggers en cascade
                                  │
                                  ├─► IF kill triggered :
                                  │     POST /api/grid/stop/{X}
                                  │
                                  ├─► IF alert :
                                  │     POST api.telegram.org/bot.../sendMessage
                                  │     ──► 📱 Tony reçoit notification
                                  │
                                  └─► log interne {timestamp, verdict}
                                          (visible dans claude.ai UI agent log)
```

Le **loop est implicite** : claude.ai relance l'agent à chaque cron trigger, et l'agent maintient sa mémoire entre runs (built-in).

---

## Phase de rollout suggérée

| Semaine | Action |
|---|---|
| 1 | Setup Cloudflare Tunnel + déploie Watchdog seul en mode "DRY-RUN" (alerte mais pas de kill) |
| 2 | Si 0 false positive critique : active kill-switch sur Watchdog |
| 3 | Déploie Daily Manager (lecture only, pas de kill) |
| 4 | Run Strategy Quant local pour la première fois, valide format des recos |
| Mois 2 | Équipe complète stable, review du ROI agents vs effort |

Tony peut couper n'importe quel agent à tout moment via claude.ai/agents UI.
