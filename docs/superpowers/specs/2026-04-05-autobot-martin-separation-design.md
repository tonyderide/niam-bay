# Design: Fix nuit + Separation Martin/Autobot

**Date**: 2026-04-05
**Status**: Approved
**Author**: Niam-Bay + Tony

## Context

Two trading apps on the same Oracle VM step on each other's toes. The auto-grid scheduler ignores trading hours and spams TP/SL orders at night, eventually killing all grids. The Angular frontend is dead weight — the niam-dashboard v2 is the real UI.

## Decisions

- **Night behavior (B)**: Auto-grid observes but takes no action between 02:00-08:00 UTC
- **Decoupling (B)**: Two distinct services — Martin (engine) and Autobot (brain + interface)
- **Frontend (A)**: Autobot's niam-dashboard v2 serves at root `/`. Angular frontend deleted.

---

## 1. Fix nuit — AutoGridScheduler respects trading hours

### Behavior

The scheduler runs every 15 min, 24/7. Between 02:00 and 08:00 UTC ("night mode"):
- Checks regime + signal (observation continues)
- Logs results normally with `[NIGHT]` prefix
- **Does NOT place any orders** (no TP/SL via `placeCloseOnlyProtection`)
- **Does NOT stop any grid**
- **Does NOT start any grid**
- `maxLossPercent` (15%) per grid remains the only safety net at night

### Implementation

Add `isWithinTradingHours()` to `AutoGridScheduler.java`:

```java
private boolean isWithinTradingHours() {
    int hour = java.time.ZonedDateTime.now(java.time.ZoneOffset.UTC).getHour();
    // Trading hours: 08:00 - 02:00 UTC (next day)
    // Night = 02:00 - 08:00 UTC
    return hour >= 8 || hour < 2;
}
```

In `checkSignals()`, the night gate goes AFTER the drawdown check (drawdown protection runs 24/7 — a KILL at night must still stop a hemorrhaging grid) and AFTER signal/regime reads, but BEFORE any grid start/stop/TP-SL logic:

```java
// 1. Drawdown check — ALWAYS runs, even at night
if (gridActive && gridState.getTotalProfit() != null) {
    // ... drawdown logic unchanged ...
}

// 2. Signal + regime checks — ALWAYS runs (observation)
SignalResult signal = signalService.checkEMATrend(instrument);
RegimeResult regime = signalService.checkRegime(instrument);

// 3. Night gate — observe only, no action
if (!isWithinTradingHours()) {
    log.info("[NIGHT] {} regime={} signal={} — observe only, no action",
             instrument, regime.getRegime(), signal.getSignal());
    continue;
}

// 4. Action logic (start/stop grids, place TP/SL) — daytime only
```

### Files changed

- `martin/src/main/java/com/martin/signal/AutoGridScheduler.java`

---

## 2. VM directory structure — target state

### Martin (trading engine only)

```
~/martin/
├── backend.jar              # Java Spring Boot, port 8081
├── backend/                 # Java source (Maven project)
├── data/                    # H2 database
├── app.log                  # Martin-only logs
├── strategy-config.json     # Grid configs
└── .env                     # Kraken API keys
```

### Autobot (brain + interface)

```
~/autobot/
├── frontend/
│   └── index.html           # niam-dashboard v2 (cinema dark + glassmorphism)
├── gateway.py               # FastAPI + WebSocket + DeepSeek chat, port 8443
├── api.py                   # Summary API (renamed martin-api.py), port 8083
├── sentinel.py              # 24/7 watchdog
├── telegram_bot.py          # Telegram alerts
├── deploy-strategy.py       # Grid deployment orchestrator
├── post-start.sh            # Auto-deploy after VM reboot
├── .env                     # Autobot-specific config (MARTIN_API, tokens)
└── logs/
    ├── gateway.log
    ├── sentinel.log
    └── telegram.log
```

### Migration steps (VM)

1. Create `~/autobot/` directory structure
2. Move files from scattered locations:
   - `~/niam-dashboard/index.html` → `~/autobot/frontend/index.html`
   - `~/martin/gateway.py` → `~/autobot/gateway.py`
   - `~/martin-api.py` → `~/autobot/api.py`
   - `~/sentinel.py` → `~/autobot/sentinel.py` (currently at home root, PID 692787)
   - `~/martin/telegram_bot.py` → `~/autobot/telegram_bot.py`
   - `~/martin/deploy-strategy.py` → `~/autobot/deploy-strategy.py`
   - `~/martin/post-start.sh` → `~/autobot/post-start.sh`
   - `~/martin/dashboard.py` → delete (dead code, log is empty)
3. Update `MARTIN_API` references in Python files to use env var:
   - `gateway.py` — already uses `os.getenv("MARTIN_API", "http://localhost:8081")` ✓
   - `deploy-strategy.py` — hardcodes `MARTIN_URL = "http://localhost:8081"` → fix
   - `telegram_bot.py` — hardcodes `MARTIN = "http://localhost:8081"` → fix
   - `api.py` — hardcodes `http://localhost:8081` in `fetch_json()` calls → fix
   - `sentinel.py` — verify and fix if hardcoded
4. Update `post-start.sh` paths: `cd ~/autobot && python3 deploy-strategy.py`
5. Update `martin.service` ExecStartPost (if any) to point to `~/autobot/post-start.sh`
6. Create `~/autobot/.env`:
   ```
   MARTIN_API=http://localhost:8081
   SAMBANOVA_KEY=<from gateway.py>
   TELEGRAM_TOKEN=<from telegram_bot.py>
   TELEGRAM_CHAT=<from telegram_bot.py>
   ```
7. Delete old locations after verification

---

## 3. Repo local — target structure

```
niam-bay/
├── martin/                  # Java source (was martin-vm-snapshot/)
│   ├── src/
│   ├── pom.xml
│   └── strategy-config.json
├── autobot/                 # Python + frontend (NEW)
│   ├── frontend/
│   │   └── index.html
│   ├── gateway.py
│   ├── api.py
│   ├── sentinel.py
│   ├── telegram_bot.py
│   ├── deploy-strategy.py
│   └── post-start.sh
├── archive/
│   ├── martin-dashboard/    # Old HTML dashboard (moved)
│   ├── martin-vm-snapshot/  # Old name (moved to martin/)
│   └── martin-backend/      # Old Java stub (already dead)
└── trading/                 # Backtesting (unchanged)
```

### Migration steps (repo)

1. `martin-vm-snapshot/` → `martin/` (rename)
2. Create `autobot/` with files from VM snapshot + `niam-dashboard/`
3. `martin-dashboard/` → `archive/martin-dashboard/`
4. `martin-backend/` → `archive/martin-backend/`
5. Update `scripts/commands.sh` paths
6. Update `CLAUDE.md` structure diagram

---

## 4. Nginx — autobot at root

### Target config (port 80)

```nginx
server {
    listen 80;
    server_name _;

    # Autobot frontend at root
    root /home/ubuntu/autobot/frontend;
    index index.html;

    # Martin API (direct)
    location /api/ {
        proxy_pass http://127.0.0.1:8081/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
    }

    # Autobot summary API (api.py serves /api/martin and /api/martin/transactions)
    location /api/martin/ {
        proxy_pass http://127.0.0.1:8083/api/martin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location = /api/martin {
        proxy_pass http://127.0.0.1:8083/api/martin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Autobot gateway
    location /gw/ {
        proxy_pass http://127.0.0.1:8443/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Autobot WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Cerveau NB (unchanged)
    location = /brain.html {
        alias /home/ubuntu/cerveau-nb/brain.html;
    }
    location /brain-api/ {
        proxy_pass http://127.0.0.1:8082/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_read_timeout 30s;
        proxy_buffering off;
    }

    # Jarvis PWA (unchanged)
    location /jarvis {
        alias /home/ubuntu/jarvis-dist;
        index index.html;
        try_files $uri $uri/ /jarvis/index.html;
    }

    # Kraken proxy (unchanged)
    location /kraken-api/ {
        proxy_pass https://futures.kraken.com/derivatives/api/v3/;
        proxy_http_version 1.1;
        proxy_set_header Host futures.kraken.com;
        proxy_ssl_server_name on;
    }

    # Crypto API (unchanged)
    location /crypto-api/ {
        proxy_pass http://127.0.0.1:8085/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }

    # LLM proxy (unchanged)
    location /v1/ {
        proxy_pass http://127.0.0.1:8084;
        proxy_set_header Host $host;
    }
    location /llm-proxy/ {
        proxy_pass http://127.0.0.1:8084/;
        proxy_set_header Host $host;
    }

    # Fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Deleted routes
- `/dashboard/` (was niam-dashboard, now at root)
- `/trading/` (was trading-dashboard, dead)
- Angular `try_files` at root (replaced by autobot)

---

## 5. Systemd services

### Renamed

| Old | New | What |
|-----|-----|------|
| `martin.service` | `martin.service` (unchanged) | Java backend |
| `niam-gateway.service` | `autobot-gateway.service` | gateway.py |
| `martin-api.service` | `autobot-api.service` | api.py (summary) |
| `sentinel.service` | `autobot-sentinel.service` | sentinel.py |

### Service files — ExecStart lines

```ini
# autobot-gateway.service
[Service]
WorkingDirectory=/home/ubuntu/autobot
ExecStart=/usr/bin/python3 /home/ubuntu/autobot/gateway.py

# autobot-api.service
[Service]
WorkingDirectory=/home/ubuntu/autobot
ExecStart=/usr/bin/python3 /home/ubuntu/autobot/api.py

# autobot-sentinel.service
[Service]
WorkingDirectory=/home/ubuntu/autobot
ExecStart=/usr/bin/python3 /home/ubuntu/autobot/sentinel.py
```

After editing service files: `sudo systemctl daemon-reload` then restart each service.

### Unchanged services
- `martin.service` — Java backend, no changes
- Cerveau NB, cryptolens, llm-proxy, alexa — untouched

---

## 6. Cleanup — what gets deleted

### VM
- `~/martin/frontend/` (Angular app + 550 node_modules dirs)
- `~/trading-dashboard/`
- `~/martin-dashboard/` (after copy to autobot)
- `~/martin/gateway.py` (after move to autobot)
- `~/martin/dashboard.py` (dead code)
- `~/martin-api.py` (after move to autobot)

### Repo
- `martin-dashboard/` → `archive/`
- `martin-backend/` → `archive/`
- `martin-vm-snapshot/` → renamed to `martin/`

---

## 7. Risk mitigation

- **Backup before anything**: `tar czf ~/backup-pre-autobot.tar.gz ~/martin ~/niam-dashboard ~/martin-api.py ~/sentinel.py /etc/systemd/system/niam-gateway.service /etc/systemd/system/martin-api.service /etc/systemd/system/sentinel.service /etc/nginx/sites-enabled/default 2>/dev/null`
- **Martin never stops**: all file moves happen while martin.service runs
- **Test after each step**: curl health checks between moves
- **Rollback**: backup tar can restore everything
