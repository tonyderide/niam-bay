# Autobot/Martin Separation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix night TP/SL spam in AutoGridScheduler, then cleanly separate Martin (Java engine) from Autobot (Python brain + dashboard) on VM and in repo.

**Architecture:** Martin stays as the pure trading engine (Java, port 8081). Autobot becomes the intelligence layer: dashboard v2, gateway, sentinel, telegram, deploy scripts. All Python scripts use `MARTIN_API` env var instead of hardcoded URLs.

**Tech Stack:** Java 21 / Spring Boot (Martin), Python 3 stdlib (Autobot), nginx, systemd

**Spec:** `docs/superpowers/specs/2026-04-05-autobot-martin-separation-design.md`

---

## Task 1: Fix night mode in AutoGridScheduler

**Files:**
- Modify: `martin-vm-snapshot/src/main/java/com/martin/signal/AutoGridScheduler.java`

- [ ] **Step 1: Add `isWithinTradingHours()` method**

Add after line 45 (after field declarations, before `checkSignals()`):

```java
/**
 * Trading hours: 08:00 - 02:00 UTC. Night (02:00-08:00 UTC) = observe only.
 */
private boolean isWithinTradingHours() {
    int hour = java.time.ZonedDateTime.now(java.time.ZoneOffset.UTC).getHour();
    return hour >= 8 || hour < 2;
}
```

- [ ] **Step 2: Add night gate in `checkSignals()` loop**

In the for-loop body, AFTER the drawdown check block (line 87) and AFTER signal+regime reads (line 100), insert the night gate BEFORE any action logic (line 93 current CIRCUIT BREAKER):

The new structure of the loop body becomes:

```java
try {
    GridState gridState = gridTradingService.getState(instrument);
    boolean gridActive = gridState != null && gridState.isActive();

    // 1. Drawdown check — ALWAYS runs, even at night
    if (gridActive && gridState.getTotalProfit() != null) {
        double equity = config.getCapital() + gridState.getTotalProfit().doubleValue();
        DrawdownManager.DrawdownAction ddAction = drawdownManager.checkDrawdown(instrument, equity);

        if (ddAction == DrawdownManager.DrawdownAction.KILL
                || ddAction == DrawdownManager.DrawdownAction.PAUSE_WEEK
                || ddAction == DrawdownManager.DrawdownAction.PAUSE_48H) {
            gridTradingService.stopGrid(instrument);
            log.error("DRAWDOWN: Stopped grid for {} action={}", instrument, ddAction);
            continue;
        }

        if (ddAction == DrawdownManager.DrawdownAction.REDUCE) {
            int currentLevels = gridState.getLevels().size();
            if (currentLevels > 2) {
                log.warn("DRAWDOWN REDUCE: Restarting {} with 2 levels (was {})", instrument, currentLevels);
                gridTradingService.stopGrid(instrument);
                GridMode mode = GridMode.valueOf(config.getGridMode() != null ? config.getGridMode().toUpperCase() : "NEUTRAL");
                gridTradingService.startGrid(instrument, config.getCapital(), config.getLeverage(),
                        config.isDemo(), config.getGridSpacingPct() / 100.0, 2, config.getMaxLossPercent(), mode);
            }
        }
    }

    // 2. Signal + regime checks — ALWAYS run (observation)
    SignalResult signal = signalService.checkEMATrend(instrument);
    lastSignals.put(instrument, signal);

    RegimeResult regime = signalService.checkRegime(instrument);
    lastRegimes.put(instrument, regime);

    // 3. Night gate — observe only, no action
    if (!isWithinTradingHours()) {
        log.info("[NIGHT] {} regime={} signal={} gridActive={} — observe only, no action",
                instrument, regime.getRegime(), signal.getSignal(), gridActive);
        continue;
    }

    // 4. CIRCUIT BREAKER — daytime only
    if (signal.getSignal() == SignalResult.Signal.DANGER && gridActive) {
        gridTradingService.stopGrid(instrument);
        log.warn("CIRCUIT BREAKER: Stopped grid for {} DANGER", instrument);
        continue;
    }

    // 5. RANGING = open grid
    if (regime.isTradeable() && !gridActive) {
        if (signal.getSignal() != SignalResult.Signal.DANGER) {
            GridMode mode = GridMode.valueOf(config.getGridMode() != null ? config.getGridMode().toUpperCase() : "NEUTRAL");
            drawdownManager.resetPeak(instrument, config.getCapital());
            gridTradingService.startGrid(instrument, config.getCapital(), config.getLeverage(),
                    config.isDemo(), config.getGridSpacingPct() / 100.0,
                    config.getTotalLevels(), config.getMaxLossPercent(), mode);
            log.info("AUTO-GRID: Opened grid for {} RANGING (ADX={}, BBW={}) signal={}",
                    instrument, String.format("%.2f", regime.getAdx()),
                    String.format("%.2f", regime.getBbWidth()), signal.getSignal());
        }
    }

    // 6. TRENDING = close-only or stop
    if (!regime.isTradeable() && gridActive) {
        boolean hasPositions = gridTradingService.hasOpenPositionsOnKraken(instrument, config.isDemo());
        if (hasPositions) {
            gridState.setCloseOnly(true);
            placeCloseOnlyProtection(instrument, config, signal);
            log.warn("REGIME SWITCH CLOSE-ONLY for {} + TP/SL placed", instrument);
        } else {
            gridTradingService.stopGrid(instrument);
            log.warn("REGIME SWITCH: Stopped grid for {} no positions", instrument);
        }
    }

    if (gridActive && gridState != null && gridState.isCloseOnly()) {
        boolean still = gridTradingService.hasOpenPositionsOnKraken(instrument, config.isDemo());
        if (!still) {
            gridTradingService.stopGrid(instrument);
            log.info("CLOSE-ONLY completed for {} positions closed", instrument);
        }
    }

    log.info("Auto-grid decision for {}: regime={}, tradeable={}, signal={}, gridActive={}",
            instrument, regime.getRegime(), regime.isTradeable(), signal.getSignal(), gridActive);

} catch (Exception e) {
    log.error("Auto-grid check failed for {}: {}", instrument, e.getMessage(), e);
}
```

- [ ] **Step 3: Build and deploy to VM**

**NOTE: This is the ONLY planned Martin downtime (~30s) in the entire migration.**

```bash
# On VM via SSH:
# Pre-check: verify grids and positions
curl -s http://localhost:8081/api/grid/active
curl -s http://localhost:8081/api/bot/positions

# Build, backup, deploy
cd ~/martin/backend && mvn package -DskipTests -q
cp ~/martin/backend.jar ~/martin/backend.jar.bak-pre-night-fix
cp ~/martin/backend/target/*.jar ~/martin/backend.jar
sudo systemctl restart martin.service
sleep 25
curl -s http://localhost:8081/api/system/status
# Expected: {"status":"UP",...}
```

- [ ] **Step 4: Redeploy grids after restart**

```bash
python3 ~/martin/deploy-strategy.py
# Expected: 4/4 grids started, auto-grid enabled
```

- [ ] **Step 5: Verify night mode logs**

```bash
# Check that the scheduler is running with the new code
tail -5 ~/martin/app.log | grep -E 'Auto-grid|NIGHT'
# If current hour is 02-08 UTC, should see [NIGHT] prefix
# If current hour is 08-02 UTC, should see normal Auto-grid decision logs
```

- [ ] **Step 6: Commit repo changes**

```bash
cd C:/Users/tony_/Documents/niam-bay
git add martin-vm-snapshot/src/main/java/com/martin/signal/AutoGridScheduler.java
git commit -m "fix: night mode — AutoGridScheduler observe-only between 02:00-08:00 UTC"
```

---

## Task 2: VM backup before migration

- [ ] **Step 1: Create full backup on VM**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "tar czf ~/backup-pre-autobot.tar.gz ~/martin ~/niam-dashboard ~/martin-api.py ~/sentinel.py /etc/systemd/system/niam-gateway.service /etc/systemd/system/martin-api.service /etc/systemd/system/sentinel.service /etc/nginx/sites-enabled/default 2>/dev/null && ls -lh ~/backup-pre-autobot.tar.gz"
```

- [ ] **Step 2: Verify backup**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "tar tzf ~/backup-pre-autobot.tar.gz | head -20"
# Expected: list of files from martin/, niam-dashboard/, etc.
```

---

## Task 3: Create autobot directory on VM

- [ ] **Step 1: Create directory structure**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "mkdir -p ~/autobot/frontend ~/autobot/logs"
```

- [ ] **Step 2: Copy files to autobot**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "cp ~/niam-dashboard/index.html ~/autobot/frontend/index.html && \
   cp ~/martin/gateway.py ~/autobot/gateway.py && \
   cp ~/martin-api.py ~/autobot/api.py && \
   cp ~/sentinel.py ~/autobot/sentinel.py && \
   cp ~/martin/telegram_bot.py ~/autobot/telegram_bot.py && \
   cp ~/martin/deploy-strategy.py ~/autobot/deploy-strategy.py && \
   cp ~/martin/post-start.sh ~/autobot/post-start.sh && \
   cp ~/martin/strategy-config.json ~/autobot/strategy-config.json && \
   ls -la ~/autobot/"
```

Note: use `cp` first (not `mv`) so originals stay until we verify everything works.

- [ ] **Step 3: Verify all files present**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "echo '=== autobot ===' && ls -la ~/autobot/ && echo '=== frontend ===' && ls -la ~/autobot/frontend/"
# Expected: gateway.py, api.py, sentinel.py, telegram_bot.py, deploy-strategy.py, post-start.sh, strategy-config.json, frontend/index.html
```

---

## Task 4: Fix hardcoded URLs in autobot Python files

**Files on VM:** `~/autobot/deploy-strategy.py`, `~/autobot/telegram_bot.py`, `~/autobot/api.py`, `~/autobot/sentinel.py`, `~/autobot/post-start.sh`

- [ ] **Step 1: Fix deploy-strategy.py**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "sed -i 's|MARTIN_URL = \"http://localhost:8081\"|MARTIN_URL = os.getenv(\"MARTIN_API\", \"http://localhost:8081\")|' ~/autobot/deploy-strategy.py && \
   sed -i 's|CONFIG_PATH = os.path.expanduser(\"~/martin/strategy-config.json\")|CONFIG_PATH = os.path.expanduser(\"~/autobot/strategy-config.json\")|' ~/autobot/deploy-strategy.py && \
   grep -n 'MARTIN_URL\|CONFIG_PATH' ~/autobot/deploy-strategy.py"
# Expected: MARTIN_URL = os.getenv("MARTIN_API", "http://localhost:8081")
# Expected: CONFIG_PATH = os.path.expanduser("~/autobot/strategy-config.json")
```

- [ ] **Step 2: Fix telegram_bot.py**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "sed -i 's|MARTIN = \"http://localhost:8081\"|MARTIN = os.getenv(\"MARTIN_API\", \"http://localhost:8081\")|' ~/autobot/telegram_bot.py && \
   head -1 ~/autobot/telegram_bot.py | grep -q 'import os' || sed -i '1s|^|import os\n|' ~/autobot/telegram_bot.py && \
   grep -n 'MARTIN =' ~/autobot/telegram_bot.py | head -1"
```

Note: telegram_bot.py uses `requests` not `os`, so add `import os` if missing.

- [ ] **Step 3: Fix api.py (martin-api.py)**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "sed -i '1s|^|import os\n|' ~/autobot/api.py && \
   sed -i '/^def fetch_json/i MARTIN_API = os.getenv(\"MARTIN_API\", \"http://localhost:8081\")' ~/autobot/api.py && \
   sed -i 's|http://localhost:8081|\" + MARTIN_API + \"|g' ~/autobot/api.py"
```

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 << 'ENDSSH'
cd ~/autobot
# api.py: add MARTIN_API env var, replace hardcoded URLs
python3 << 'ENDPY'
import re
with open("api.py") as f:
    code = f.read()

# Add import os if missing
if "import os" not in code:
    code = "import os\n" + code

# Add MARTIN_API constant before first function
if "MARTIN_API" not in code:
    code = code.replace(
        "def fetch_json(",
        'MARTIN_API = os.getenv("MARTIN_API", "http://localhost:8081")\n\ndef fetch_json(',
        1
    )

# Replace all hardcoded localhost:8081 URLs
code = code.replace('"http://localhost:8081', 'f"{MARTIN_API}')

with open("api.py", "w") as f:
    f.write(code)
print("api.py updated")
ENDPY
grep -n "MARTIN_API\|localhost:8081" api.py
ENDSSH
# Expected: MARTIN_API = os.getenv(...) and no more hardcoded localhost:8081
```

- [ ] **Step 4: Fix sentinel.py**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "sed -i 's|MARTIN_BASE = \"http://localhost:8081\"|MARTIN_BASE = os.getenv(\"MARTIN_API\", \"http://localhost:8081\")|' ~/autobot/sentinel.py && \
   head -1 ~/autobot/sentinel.py | grep -q 'import os' || sed -i '1s|^|import os\n|' ~/autobot/sentinel.py && \
   grep -n 'MARTIN_BASE\|import os' ~/autobot/sentinel.py | head -2"
# Expected: import os at top, MARTIN_BASE = os.getenv("MARTIN_API", "http://localhost:8081")
```

- [ ] **Step 5: Fix post-start.sh**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "sed -i 's|LOG=~/martin/post-start.log|LOG=~/autobot/post-start.log|' ~/autobot/post-start.sh && \
   sed -i 's|cd ~/martin && python3 deploy-strategy.py|cd ~/autobot \&\& python3 deploy-strategy.py|' ~/autobot/post-start.sh && \
   cat ~/autobot/post-start.sh"
# Expected: LOG=~/autobot/post-start.log and cd ~/autobot && python3 deploy-strategy.py
```

- [ ] **Step 6: Create .env file (extract secrets from existing files, do NOT hardcode)**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 << 'ENDSSH'
# Extract secrets from existing files
SAMBA_KEY=$(grep -oP 'SAMBANOVA_KEY.*?"(\K[^"]+)' ~/martin/gateway.py 2>/dev/null || grep -oP "'([a-f0-9-]{36})'" ~/martin/gateway.py | tr -d "'")
TG_TOKEN=$(grep -oP 'BOT_TOKEN\s*=\s*"(\K[^"]+)' ~/martin/telegram_bot.py)
TG_CHAT=$(grep -oP 'CHAT_ID\s*=\s*"(\K[^"]+)' ~/martin/telegram_bot.py)

cat > ~/autobot/.env << EOF
MARTIN_API=http://localhost:8081
SAMBANOVA_KEY=$SAMBA_KEY
TELEGRAM_TOKEN=$TG_TOKEN
TELEGRAM_CHAT=$TG_CHAT
EOF
echo "Created ~/autobot/.env"
cat ~/autobot/.env
ENDSSH
```

- [ ] **Step 7: Verify no more hardcoded URLs**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "grep -rn 'localhost:8081' ~/autobot/*.py ~/autobot/*.sh | grep -v 'getenv\|os.getenv\|curl'"
# Expected: no output (all hardcoded URLs replaced, curl in post-start.sh is OK)
```

---

## Task 5: Create autobot systemd services on VM

- [ ] **Step 1: Create autobot-gateway.service**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 << 'ENDSSH'
sudo tee /etc/systemd/system/autobot-gateway.service << 'EOF'
[Unit]
Description=Autobot Gateway (FastAPI + WebSocket)
After=network.target martin.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/autobot
EnvironmentFile=/home/ubuntu/autobot/.env
ExecStart=/usr/bin/python3 /home/ubuntu/autobot/gateway.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
echo "Created autobot-gateway.service"
ENDSSH
```

- [ ] **Step 2: Create autobot-api.service**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 << 'ENDSSH'
sudo tee /etc/systemd/system/autobot-api.service << 'EOF'
[Unit]
Description=Autobot Summary API
After=network.target martin.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/autobot
EnvironmentFile=/home/ubuntu/autobot/.env
ExecStart=/usr/bin/python3 /home/ubuntu/autobot/api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
echo "Created autobot-api.service"
ENDSSH
```

- [ ] **Step 3: Create autobot-sentinel.service**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 << 'ENDSSH'
sudo tee /etc/systemd/system/autobot-sentinel.service << 'EOF'
[Unit]
Description=Autobot Sentinel — 24/7 trading watchdog
After=network.target martin.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/autobot
EnvironmentFile=/home/ubuntu/autobot/.env
ExecStart=/usr/bin/python3 /home/ubuntu/autobot/sentinel.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
echo "Created autobot-sentinel.service"
ENDSSH
```

- [ ] **Step 4: Reload systemd and start autobot services, stop old ones**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 << 'ENDSSH'
sudo systemctl daemon-reload

# Stop old services
sudo systemctl stop niam-gateway.service
sudo systemctl stop martin-api.service
sudo systemctl stop sentinel.service

# Disable old services
sudo systemctl disable niam-gateway.service
sudo systemctl disable martin-api.service
sudo systemctl disable sentinel.service

# Enable and start new services
sudo systemctl enable autobot-gateway.service
sudo systemctl enable autobot-api.service
sudo systemctl enable autobot-sentinel.service
sudo systemctl start autobot-gateway.service
sudo systemctl start autobot-api.service
sudo systemctl start autobot-sentinel.service

echo "=== Status ==="
systemctl is-active autobot-gateway.service
systemctl is-active autobot-api.service
systemctl is-active autobot-sentinel.service
systemctl is-active martin.service
ENDSSH
# Expected: active active active active
```

- [ ] **Step 5: Health check all services**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "echo 'Martin:' && curl -s http://localhost:8081/api/system/status | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"status\"])' && \
   echo 'Gateway:' && curl -s http://localhost:8443/health && echo && \
   echo 'API:' && curl -s http://localhost:8083/api/martin | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"grid\",\"?\"))' && \
   echo 'Grids:' && curl -s http://localhost:8081/api/grid/active"
# Expected: UP, ok/connected, active or stopped, [list of grids]
```

---

## Task 6: Update nginx config on VM

- [ ] **Step 1: Write new nginx config**

**NOTE: The HTTPS (port 443) block is preserved as-is from the existing config. Ports 8090/8095 serve existing apps (not part of this migration). Only the HTTP (port 80) block is modified.**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 << 'ENDSSH'
sudo cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.bak

sudo tee /etc/nginx/sites-enabled/default << 'EOF'
server {
    listen 443 ssl;
    server_name niambay.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/niambay.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/niambay.duckdns.org/privkey.pem;

    location /jarvis {
        alias /home/ubuntu/jarvis-dist;
        index index.html;
        try_files $uri $uri/ /jarvis/index.html;
    }

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

    location /gw/ {
        proxy_pass http://127.0.0.1:8443/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8090/;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://127.0.0.1:8095/;
        proxy_set_header Host $host;
        proxy_set_header Content-Type $content_type;
        proxy_set_header Content-Length $content_length;
    }
}

server {
    listen 80;
    server_name _;

    # Autobot frontend at root
    root /home/ubuntu/autobot/frontend;
    index index.html;

    # Jarvis PWA
    location /jarvis {
        alias /home/ubuntu/jarvis-dist;
        index index.html;
        try_files $uri $uri/ /jarvis/index.html;
    }

    location = /brain.html {
        alias /home/ubuntu/cerveau-nb/brain.html;
    }

    location /brain-api/ {
        proxy_pass http://127.0.0.1:8082/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 30s;
        proxy_buffering off;
    }

    location /kraken-api/ {
        proxy_pass https://futures.kraken.com/derivatives/api/v3/;
        proxy_http_version 1.1;
        proxy_set_header Host futures.kraken.com;
        proxy_set_header Accept-Encoding "";
        proxy_ssl_server_name on;
    }

    location /crypto-api/ {
        proxy_pass http://127.0.0.1:8085/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }

    # Autobot summary API
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
        proxy_cache off;
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

    # Autobot gateway REST
    location /gw/ {
        proxy_pass http://127.0.0.1:8443/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /v1/ {
        proxy_pass http://127.0.0.1:8084;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /llm-proxy/ {
        proxy_pass http://127.0.0.1:8084/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Fallback to autobot frontend
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF
echo "Nginx config written"
ENDSSH
```

- [ ] **Step 2: Test and reload nginx**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "sudo nginx -t && sudo systemctl reload nginx && echo 'nginx reloaded OK'"
# Expected: syntax is ok, test is successful, nginx reloaded OK
```

- [ ] **Step 3: Verify autobot serves at root**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "curl -s http://localhost/ | head -5"
# Expected: <!DOCTYPE html> ... NIAM-BAY Trading Dashboard ...
```

- [ ] **Step 4: Verify API routes still work**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "echo 'Martin API:' && curl -s http://localhost/api/grid/active && echo && \
   echo 'Autobot API:' && curl -s http://localhost/api/martin | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"grid\",\"?\"), d.get(\"resume\",\"?\")[:60])'"
# Expected: grid list from Martin, summary from autobot API
```

---

## Task 7: Update martin.service post-start to use autobot

- [ ] **Step 1: Check current martin.service for ExecStartPost**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "cat /etc/systemd/system/martin.service"
```

- [ ] **Step 2: Update post-start reference if needed**

If martin.service has `ExecStartPost` pointing to `~/martin/post-start.sh`, update it:

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "sudo sed -i 's|/home/ubuntu/martin/post-start.sh|/home/ubuntu/autobot/post-start.sh|' /etc/systemd/system/martin.service && \
   sudo systemctl daemon-reload && \
   grep 'post-start' /etc/systemd/system/martin.service"
```

If there's no ExecStartPost (post-start runs via cron or @reboot), check crontab:

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "crontab -l | grep post-start"
```

Update accordingly.

---

## Task 8: Cleanup old files on VM

- [ ] **Step 1: Delete Angular frontend (biggest cleanup)**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "rm -rf ~/martin/frontend && echo 'Angular frontend deleted'"
# This removes ~550 node_modules dirs + Angular build artifacts
```

- [ ] **Step 2: Delete old dashboard dirs**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "rm -rf ~/trading-dashboard && echo 'trading-dashboard deleted' && \
   rm -rf ~/niam-dashboard && echo 'niam-dashboard deleted (now at ~/autobot/frontend)' && \
   rm ~/martin/dashboard.py && echo 'dashboard.py deleted (dead code)'"
```

- [ ] **Step 3: Delete moved files from old locations**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "rm ~/martin/gateway.py ~/martin-api.py ~/sentinel.py ~/martin/telegram_bot.py ~/martin/deploy-strategy.py ~/martin/post-start.sh 2>/dev/null; echo 'Old files cleaned up'"
```

- [ ] **Step 4: Delete old systemd unit files**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "sudo rm /etc/systemd/system/niam-gateway.service /etc/systemd/system/martin-api.service /etc/systemd/system/sentinel.service 2>/dev/null && \
   sudo systemctl daemon-reload && echo 'Old service files removed'"
```

- [ ] **Step 5: Final VM verification**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 << 'ENDSSH'
echo "=== SERVICES ==="
systemctl is-active martin.service
systemctl is-active autobot-gateway.service
systemctl is-active autobot-api.service
systemctl is-active autobot-sentinel.service

echo "=== DIRS ==="
echo "martin:" && ls ~/martin/*.jar ~/martin/data ~/martin/app.log 2>/dev/null | wc -l
echo "autobot:" && ls ~/autobot/*.py ~/autobot/frontend/index.html 2>/dev/null | wc -l
echo "angular:" && ls ~/martin/frontend 2>/dev/null && echo "STILL EXISTS!" || echo "deleted OK"
echo "old dashboards:" && ls ~/trading-dashboard ~/niam-dashboard 2>/dev/null && echo "STILL EXISTS!" || echo "deleted OK"

echo "=== HEALTH ==="
curl -s http://localhost:8081/api/system/status | python3 -c 'import sys,json; print("Martin:", json.load(sys.stdin)["status"])'
curl -s http://localhost:8443/health | python3 -c 'import sys,json; print("Gateway:", json.load(sys.stdin).get("status","?"))'
curl -s http://localhost/ | head -1
ENDSSH
```

---

## Task 9: Reorganize local repo

- [ ] **Step 1: Move martin-vm-snapshot → martin**

```bash
cd C:/Users/tony_/Documents/niam-bay
git mv martin-vm-snapshot martin
```

- [ ] **Step 2: Create autobot directory with files**

```bash
cd C:/Users/tony_/Documents/niam-bay
mkdir -p autobot/frontend
# Copy the Python files from martin (they were in martin-vm-snapshot)
cp martin/gateway.py autobot/gateway.py
cp martin/telegram_bot.py autobot/telegram_bot.py
cp martin/deploy-strategy.py autobot/deploy-strategy.py
cp martin/post-start.sh autobot/post-start.sh
# Copy the dashboard from martin-dashboard
cp martin-dashboard/index.html autobot/frontend/index.html
```

- [ ] **Step 3: Apply same URL fixes to repo copies**

Apply the same `os.getenv("MARTIN_API", ...)` fixes to the repo copies of:
- `autobot/deploy-strategy.py` (line 18: `MARTIN_URL`)
- `autobot/telegram_bot.py` (line 17: `MARTIN`)
- Copy `trading/sentinel.py` to `autobot/sentinel.py` and fix `MARTIN_BASE` (line 34)

- [ ] **Step 4: Create autobot api.py from VM martin-api.py**

martin-api.py doesn't exist in the repo. Copy it from VM:

```bash
scp -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141:~/autobot/api.py C:/Users/tony_/Documents/niam-bay/autobot/api.py
```

- [ ] **Step 5: Archive old directories**

```bash
cd C:/Users/tony_/Documents/niam-bay
git mv martin-dashboard archive/martin-dashboard
git mv martin-backend archive/martin-backend
```

- [ ] **Step 6: Move martin-config into martin**

```bash
cd C:/Users/tony_/Documents/niam-bay
cp martin-config/strategy-config.json autobot/strategy-config.json
cp martin-config/application.yml martin/application.yml
git mv martin-config archive/martin-config
```

- [ ] **Step 7: Remove Python files from martin/ that now belong to autobot**

```bash
cd C:/Users/tony_/Documents/niam-bay
git rm martin/gateway.py martin/telegram_bot.py martin/deploy-strategy.py martin/post-start.sh martin/dashboard.py
```

- [ ] **Step 8: Verify repo structure**

```bash
cd C:/Users/tony_/Documents/niam-bay
echo "=== martin ===" && ls martin/src martin/pom.xml 2>/dev/null
echo "=== autobot ===" && ls autobot/
echo "=== archive ===" && ls archive/
```

Expected:
- `martin/` has `src/`, `pom.xml`, `application.yml`, `strategy-config.json`
- `autobot/` has `frontend/`, `gateway.py`, `api.py`, `sentinel.py`, `telegram_bot.py`, `deploy-strategy.py`, `post-start.sh`, `strategy-config.json`
- `archive/` has `martin-dashboard/`, `martin-backend/`, `martin-config/`

---

## Task 10: Update CLAUDE.md and commands.sh

- [ ] **Step 1: Update CLAUDE.md structure diagram**

Replace the repo structure section in `CLAUDE.md` with:

```markdown
## Structure du repo

```
niam-bay/
├── CLAUDE.md              # Ce fichier
├── README.md              # Vitrine publique
├── martin/                # Moteur de trading (Java Spring Boot)
│   ├── src/               # Source Java
│   ├── pom.xml            # Maven build
│   ├── application.yml    # Config Spring Boot
│   └── strategy-config.json
├── autobot/               # Cerveau + interface (Python)
│   ├── frontend/          # Dashboard v2 (HTML)
│   ├── gateway.py         # FastAPI + WebSocket + chat
│   ├── api.py             # Summary API
│   ├── sentinel.py        # Watchdog 24/7
│   ├── telegram_bot.py    # Alertes Telegram
│   ├── deploy-strategy.py # Orchestrateur de grids
│   └── post-start.sh      # Auto-deploy après reboot VM
├── docs/                  # Mémoire
├── trading/               # Backtests et research
├── cerveau-nb/            # Réseau de neurones associatif
├── scripts/               # Commandes quick
├── site/                  # GitHub Pages
├── ai-lab/                # Expériences IA
├── identite/              # Fichiers d'identité
└── archive/               # Projets en pause
    ├── martin-dashboard/  # Ancien dashboard HTML
    ├── martin-backend/    # Ancien stub Java
    ├── martin-config/     # Ancienne config séparée
    └── ...
```
```

- [ ] **Step 2: Update commands.sh paths**

Update all references in `scripts/commands.sh`:
- `~/martin/deploy-strategy.py` → `~/autobot/deploy-strategy.py`
- `~/martin/post-start.log` → `~/autobot/post-start.log`
- Any other path references

- [ ] **Step 3: Commit all changes**

```bash
cd C:/Users/tony_/Documents/niam-bay
git add -A
git commit -m "refactor: separate Martin (engine) and Autobot (brain+dashboard)

- martin/ = Java trading engine only (was martin-vm-snapshot/)
- autobot/ = Python brain + dashboard v2 + gateway + sentinel + telegram
- Fix night mode: AutoGridScheduler observe-only 02:00-08:00 UTC
- All Python scripts use MARTIN_API env var
- Archive old: martin-dashboard/, martin-backend/, martin-config/
- Angular frontend deleted from VM"
```

- [ ] **Step 4: Push**

```bash
cd C:/Users/tony_/Documents/niam-bay
git push origin master
```

---

## Task 11: Final end-to-end verification

- [ ] **Step 1: Verify grids are running**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "curl -s http://localhost:8081/api/grid/active"
# Expected: ["PF_SOLUSD","PF_LINKUSD","PF_ADAUSD","PF_DOTUSD"]
```

- [ ] **Step 2: Verify dashboard serves at root**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "curl -s http://localhost/ | grep -o 'NIAM-BAY Trading Dashboard'"
# Expected: NIAM-BAY Trading Dashboard
```

- [ ] **Step 3: Verify all autobot services healthy**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "for svc in martin autobot-gateway autobot-api autobot-sentinel; do echo \"\$svc: \$(systemctl is-active \$svc.service)\"; done"
# Expected: all active
```

- [ ] **Step 4: Verify no old services running**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "for svc in niam-gateway martin-api sentinel; do echo \"\$svc: \$(systemctl is-active \$svc.service)\"; done"
# Expected: all inactive
```

- [ ] **Step 5: Wait for next auto-grid check and verify night mode**

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 \
  "tail -20 ~/martin/app.log | grep -E 'Auto-grid|NIGHT'"
# If 02-08 UTC: should see [NIGHT] observe only
# If 08-02 UTC: should see normal Auto-grid decision
```
