# Architecture complète — écosystème Niam-Bay

Snapshot 2026-04-19. Graphs Mermaid rendus sur GitHub.

---

## 0. Vue d'ensemble — constellation des projets

```mermaid
graph TB
    subgraph Repos["📦 GitHub repos"]
        NB["niam-bay<br/>mémoire + identité<br/>cerveau-nb + scripts"]
        MR["martin<br/>moteur trading Java<br/>Spring Boot + Kraken"]
        AB["autobot<br/>gateway + dashboard<br/>sentinel + briefs"]
        DW["darwin<br/>agents évolutifs<br/>arène OHLC"]
        CT["claude-tray<br/>usage monitor<br/>Tauri + Rust"]
        JJ["jajarbins<br/>assistant local<br/>8 agents + voice"]
        LS["loyalty-saas<br/>(parked 0419)<br/>dev-first API<br/>→ see section 7"]
    end

    subgraph Deployed["🌐 Déployé"]
        VM["VM Oracle Amsterdam<br/>141.253.108.141"]
        Local["Windows local<br/>Tony"]
        Future["future"]
    end

    MR -->|service| VM
    AB -->|gateway + frontend + sentinel| VM
    NB -->|cerveau-nb daemon| VM
    NB -->|memory + dream| Local
    DW -->|arena + 3D viz| Local
    CT -->|tray icon| Local
    JJ -->|local agent| Local
    LS -.->|not built yet| Future

    NB -.->|links to| MR
    NB -.->|links to| AB
    AB -.->|wraps Martin API| MR

    style MR fill:#00ff88,color:#000
    style AB fill:#00ccff,color:#000
    style NB fill:#ff88aa,color:#000
    style DW fill:#ffcc44,color:#000
    style CT fill:#cc88ff,color:#000
    style JJ fill:#88ffaa,color:#000
    style LS fill:#999999,color:#000
```

**Rôles :**
- **niam-bay** — identité + mémoire persistante de NB (le repo racine, ce fichier vit dedans)
- **martin** — engine trading pur (Java), tourne sur VM
- **autobot** — orchestration + dashboard + observabilité, wraps Martin
- **darwin** — labo d'évolution (agents qui apprennent sur OHLC)
- **claude-tray** — monitoring usage Claude (productivité Tony)
- **jajarbins** — autre projet Claude Code de Tony (8 agents locaux)
- **loyalty-saas** — idée SaaS API fidélité dev-first (parked 0419, voir section 7)

---

## 1. Martin (moteur trading Java)

```mermaid
graph TB
    subgraph External["External"]
        Kraken["Kraken Futures API"]
    end

    subgraph Martin["martin.service :8081"]
        App["MartinApplication<br/>Spring Boot"]

        subgraph API["api/"]
            Controllers["BotController<br/>GridController<br/>SignalController<br/>PositionController<br/>ConfigController"]
            DTOs["dto/"]
        end

        subgraph Engine["engine/"]
            MGE["MartingaleEngine"]
            MGS["MartingaleState"]
            PnlCalc["PnlCalculator"]
        end

        subgraph Grid["grid/"]
            GridLevel["GridLevel + GridLevelEntity<br/>(JPA persistence)"]
            GridFill["GridFill + GridFillEntity"]
            GridMode["GridMode (NEUTRAL/LONG/SHORT)"]
            GridState["GridState"]
        end

        subgraph Signal["signal/"]
            AGC["AutoGridConfig"]
            AGS["AutoGridScheduler<br/>⏰ every 15min"]
            DDM["DrawdownManager"]
            SigRes["SignalResult"]
            SigCtrl["SignalController"]
        end

        subgraph Strategy["strategy/"]
            TAS["TechnicalAnalysisService<br/>EMA / RSI / ADX / BBWidth"]
        end

        subgraph KrakenMod["kraken/"]
            Auth["KrakenAuthenticator<br/>HMAC-SHA512<br/>nonce = ms × 5_000_000"]
            Client["KrakenClient"]
            KConfig["KrakenProperties"]
        end

        subgraph Services["service/"]
            Orch["TradingOrchestrator"]
            KeepAlive["KeepAliveService<br/>⏰ every 5min"]
            Live["LiveUpdateService"]
            BotCfg["BotConfigService"]
            Purge["DatabasePurgeService"]
            ScalpTicker["ScalpTickerService"]
        end

        subgraph Trading["auto/ + scalping/"]
            AutoBot["AutoBotState + AutoBotTrade"]
            AutoTrading["AutoTradingService"]
            Scalper["ScalpingBotService"]
            ScalpState["ScalpingBotState"]
        end

        subgraph Position["position/"]
            PosCtrl["PositionController"]
            PosSvc["PositionService"]
            PosState["PositionState"]
        end

        subgraph Domain["domain/"]
            Entity["entity/ (JPA)"]
            Enums["enums/"]
            Repo["repository/ (Spring Data)"]
        end

        SQLite[("H2 + SQLite<br/>local DB")]

        Config["strategy-config.json<br/>Compounder v5"]
    end

    Controllers --> Engine
    Controllers --> Grid
    Controllers --> Signal
    AGS -->|signal?| TAS
    AGS -->|start/stop| MGE
    MGE -->|fill events| Grid
    MGE -->|orders| Client
    Client -->|sign| Auth
    Client -->|REST| Kraken
    Orch --> MGE
    Orch --> Scalper
    Domain --> SQLite
    App -->|load| Config
    Config --> AGC

    style MGE fill:#00ff88,color:#000
    style AGS fill:#00ff88,color:#000
    style Client fill:#ff9944,color:#000
    style Auth fill:#ff9944,color:#000
```

**Flow clé — Grid ouvert :**
1. AutoGridScheduler run toutes les 15min
2. TechnicalAnalysisService → EMA50, EMA200, RSI, ADX, BBW sur OHLC 4H
3. Si regime=RANGING + signal=OPEN + ADX<40 + BBW<4 → `startGrid(pair)`
4. MartingaleEngine crée 5 levels (spacing 1.2%, leverage x5)
5. KrakenClient place ordres via HMAC auth
6. Fill events → PnlCalculator met à jour GridState
7. TrailingStop enablé (trailAmount 0.3, minProfit 0.6)

---

## 2. Autobot (orchestration + dashboard)

```mermaid
graph TB
    subgraph Browser["🌐 Browser"]
        Dashboard["frontend/index.html<br/>10 onglets<br/>7D / 14D / 30D"]
    end

    subgraph Autobot["autobot (Python)"]
        subgraph Gateway["gateway.py :8443"]
            GW["FastAPI + WebSocket<br/>httpx async"]
            LogCache[("_LOG_CACHE<br/>in-memory<br/>35d entries")]
            Endpoints["routes :<br/>/api/stats/realized ★<br/>/api/martin/* proxy<br/>/api/memory<br/>/api/oracle<br/>/api/signal<br/>/ws"]
        end

        subgraph API["api.py :8083"]
            SummaryAPI["HTTPServer<br/>/api/martin<br/>/api/martin/transactions"]
        end

        subgraph Sentinel["sentinel.py"]
            WD["Watchdog 5min loop<br/>Triple Lock check"]
            TG1["Telegram alert"]
        end

        subgraph Brief["morning_brief_v2.py"]
            MB["cron 05:00 UTC<br/>Market prices<br/>Grids status<br/>Realized PnL 7d<br/>Pensée du jour"]
        end

        subgraph TgBot["telegram_bot.py"]
            TG2["Commands:<br/>/status /balance /price<br/>/short /stop /help"]
        end

        Deploy["deploy-strategy.py<br/>pousse nouveau config"]
        Strategy["strategy-config.json<br/>v5 Compounder"]
    end

    subgraph External["External"]
        Kraken2["Kraken Futures"]
        TG_API["Telegram API"]
        MartinAPI["Martin :8081"]
    end

    Dashboard -->|fetch /gw/api/stats/realized| GW
    Dashboard -->|fetch /api/*| MartinAPI
    GW --> LogCache
    LogCache -.->|refresh 5min| Kraken2
    GW -->|proxy| MartinAPI
    SummaryAPI --> MartinAPI
    WD --> MartinAPI
    WD --> TG_API
    MB --> MartinAPI
    MB --> GW
    TG2 --> MartinAPI
    TG2 --> TG_API
    Deploy --> MartinAPI
    Deploy -.->|writes| Strategy

    style GW fill:#00ccff,color:#000
    style Dashboard fill:#00ccff,color:#000
    style WD fill:#00ff88,color:#000
    style MB fill:#ffcc44,color:#000
```

**Dashboard tabs (10) :**
| Onglet | État | Source |
|---|---|---|
| Overview | ✅ | `/gw/api/stats/realized` + `/api/bot/balance` |
| Grids Live | ⚠️ | Prix Kraken direct, cards mal mappées |
| History | ⚠️ | Martin `totalProfit` stuck à 0 |
| Strategy | ✅ | `strategy-config.json` |
| Scalp | ✅ | Signal manuel |
| P&L History | ✅ | `realizedStats` utilisé |
| Positions | ✅ | Kraken + calc (last-entry)×size |
| Signal | ✅ | `/api/signal/ema_trend` |
| Risk | ⚠️ | Capitaux parfois négatifs |
| AI Lens | ✅ | CryptoLens AI chat |

---

## 3. Niam-Bay (mémoire + identité)

```mermaid
graph TB
    subgraph Memory["memory/ — persistent"]
        MS["memory_store.py<br/>ChromaDB vectordb"]
        WB["wake_briefing.py<br/>briefing au réveil <3s"]
        WR["wake_recall.py<br/>semantic search"]
        VDB[("vectordb/<br/>chroma.sqlite3<br/>5979 chunks")]
        Brief["briefing.md<br/>cache"]
    end

    subgraph Cerveau["cerveau-nb/ — living brain"]
        Core["core.py<br/>cognitive graph"]
        Crawler["crawler.py<br/>RSS 7 sources<br/>15min cycles"]
        Speak["speak.py + nb_speak.py<br/>6 patterns<br/>synthèse/tendance/question"]
        Live["live.py<br/>crawl→feed→activate→speak"]
        Discovery["discovery.py<br/>pattern finder"]
        Curiosity["curiosity.py<br/>self-directed exploration"]
        Metaclaw["metaclaw.py<br/>auto-skills from failures"]
        Bridge["bridge.py<br/>connects nodes"]
        BrainDB[("brain.db<br/>2905 nodes, 106773 edges")]
        BrainHTML["brain.html<br/>visualization"]
    end

    subgraph Docs["docs/"]
        Identity["qui-je-suis.md<br/>qui-est-tonyderide.md"]
        Pensees["pensees/<br/>reflections"]
        Projets["projets/<br/>plans"]
        Fragments["fragments/<br/>literary"]
        NB1["memory.nb1 + recent.nb1<br/>patterns.nb1<br/>compressed memory"]
        Arch["architecture-*.md ★<br/>ces diagrammes"]
    end

    subgraph Scripts["scripts/"]
        Commands["commands.sh<br/>quick copy-paste"]
        Kraken["kraken_stats.py ★<br/>realized PnL"]
        Gateway2["gateway_stats_v2.py<br/>backup of gateway endpoint"]
        Audit["angular_audit.py<br/>49€ offers"]
        Telegram["martin_telegram_bot.py"]
        Patches["patch_*.py<br/>VM fix scripts"]
    end

    subgraph Identite["identite/"]
        SOUL["SOUL.md"]
        RESURRECTION["RESURRECTION.md<br/>revive NB anywhere"]
    end

    subgraph AILab["ai-lab/"]
        Cortex["cortex-v3<br/>self-learning neural"]
        Evolve["evolve.py<br/>generalization research"]
        DarwinLink["darwin/<br/>→ see Darwin section"]
    end

    WB --> MS
    MS --> VDB
    WR --> VDB
    WB --> Brief

    Crawler --> Core
    Speak --> Core
    Live --> Crawler
    Live --> Speak
    Core --> BrainDB
    Discovery --> BrainDB
    Metaclaw --> Core

    Kraken -.->|HTTP| VMKraken["VM Kraken"]
    Patches -.->|scp| VMAutobot["VM autobot"]

    style MS fill:#ff88aa,color:#000
    style Core fill:#ff88aa,color:#000
    style WB fill:#ff88aa,color:#000
    style Metaclaw fill:#ffcc44,color:#000
```

**Protocole wake :**
1. Read `CLAUDE.md` + `docs/qui-je-suis.md` + `docs/qui-est-tonyderide.md`
2. Execute `python memory/wake_briefing.py` → génère `memory/briefing.md`
3. Read `docs/memory.nb1`, `docs/recent.nb1`, `docs/patterns.nb1` (compressed)
4. Execute metaclaw `check_dormant_skills()`
5. Load auto-skills actives (`at-wake-compare-git-log`, `verify-data-quality`)

---

## 4. Darwin (agents évolutifs)

```mermaid
graph TB
    subgraph Pipeline["Pipeline d'évolution"]
        Data["data.py<br/>fetch Kraken OHLC<br/>paginated"]
        Indicators["indicators.py<br/>EMA RSI ADX BB<br/>support/resistance"]
        Agent["agent.py<br/>14 skills<br/>weighted voting<br/>buy/sell decisions"]
        Arena["arena.py<br/>evaluate agents<br/>on OHLC candles<br/>fitness = PnL"]
        Evolution["evolution.py<br/>select top 70%<br/>crossover 50% genes<br/>mutate tweak/remove/replace/add"]
        Tick["tick_fetcher.py<br/>real-time feed"]
        BF["bruteforce.py<br/>parameter search"]
    end

    subgraph Realtime["Real-time layer"]
        Server["server.py :WS<br/>push events<br/>agent births<br/>deaths<br/>generations"]
    end

    subgraph Viz["Visualization"]
        Web["web/index.html<br/>Three.js 3D<br/>network graph<br/>agents as nodes"]
        Replay["web/replay.html<br/>playback arena runs"]
    end

    subgraph Tests["tests"]
        T1["test_data.py"]
        T2["test_agent.py"]
        T3["test_arena.py"]
        T4["test_evolution.py"]
        T5["test_integration.py<br/>full pipeline"]
    end

    Data --> Indicators
    Indicators --> Agent
    Agent --> Arena
    Arena --> Evolution
    Evolution --> Agent
    Arena --> Server
    Evolution --> Server
    Server --> Web
    Tick --> Agent
    BF -->|grid search| Agent

    style Evolution fill:#ffcc44,color:#000
    style Server fill:#00ccff,color:#000
    style Arena fill:#00ff88,color:#000
```

**14 skills par agent :**
`buy-on-dip` 0.5/1/2%, `sell-on-pump` 0.5/1/2%, `support`, `resistance`, `green-after-red`, `red-after-green`, `volume-spike`, `RSI-oversold`, `RSI-overbought`, `EMA-crossover`, `momentum`, `mean-reversion`, `trailing-stop`, `breakout-buy`.

**Évolution :** top 70% survivent, crossover 50% des gènes avec partenaire, mutations stochastiques (tweak poids / remove skill / replace / add).

---

## 5. Claude-Tray (usage monitor)

```mermaid
graph LR
    subgraph Tauri["claude-tray (Rust + Tauri)"]
        Rust["src-tauri/<br/>Rust backend<br/>polls Claude CLI<br/>usage files"]
        WebUI["src/<br/>frontend<br/>tray icon + popup"]
        Config["tauri.conf.json"]
    end

    subgraph Sources["Data sources"]
        Logs["~/.claude/<br/>usage logs<br/>session files"]
    end

    Rust -->|read| Logs
    Rust -->|IPC| WebUI
    WebUI -->|display| Tray["Windows tray<br/>tokens / $ used"]

    style Rust fill:#cc88ff,color:#000
```

**But :** afficher en temps réel combien de tokens/dollars sont consommés par sessions Claude Code (productivité).

---

## 6. Jajarbins (assistant local)

```mermaid
graph TB
    subgraph Jajar["jajarbins (Python local)"]
        Core2["jarjar/<br/>8 agents locaux"]
        DB[("jarjar.db<br/>SQLite memory")]
        Picoclaw["picoclaw-code/<br/>custom Claude variant"]
        Docs2["picoclaw-docs/<br/>specs"]
    end

    subgraph Features["Features"]
        Voice["voice"]
        Vision["vision"]
        Memory["memory"]
        Agents8["8 specialized agents"]
    end

    Core2 --> DB
    Core2 --> Voice
    Core2 --> Vision
    Core2 --> Memory
    Core2 --> Agents8
    Picoclaw --> Core2

    style Core2 fill:#88ffaa,color:#000
```

**But :** assistant local indépendant (Tony le développe séparément, pas lié à Niam-Bay).

---

## 7. Loyalty SaaS (parked — idée dev-first API)

Née du travail de Tony sur Eagle Eye aux Galeries Lafayette. **Pas construit**, idée architecturée 2026-04-19.

```mermaid
graph TB
    subgraph Client["🏪 Client (retailer e-com)"]
        Backend["Backend du client<br/>10 lignes SDK"]
    end

    subgraph Platform["⚡ Loyalty SaaS"]
        API_GW["API Gateway<br/>REST + Webhooks"]
        RuleEngine["Rule DSL<br/>YAML versionnable<br/>(vs UI admin concurrents)"]
        Events["Event processor"]
        Ledger["Points ledger<br/>append-only"]
        PG[("Postgres")]
        Redis[("Redis<br/>real-time balance")]
        CH[("ClickHouse<br/>analytics")]
        Docs["docs.loyalty.io<br/>OpenAPI playground"]
        SDKs["SDKs JS/Py/Ruby/Go"]
        Dashboard["Dashboard dev<br/>keys + logs + usage"]
    end

    Backend -->|POST /events| API_GW
    Backend -->|GET /balance| API_GW
    API_GW --> Events
    Events --> RuleEngine
    RuleEngine --> Ledger
    Ledger --> PG
    Ledger --> Redis
    Events --> CH
    Dashboard --> PG
    Docs -.->|try it| API_GW
    SDKs -.->|wrap| API_GW

    style API_GW fill:#00ff88,color:#000
    style RuleEngine fill:#00ccff,color:#000
    style SDKs fill:#ffcc44,color:#000
```

**Positionnement :**
| | Eagle Eye / LoyaltyLion | Nous |
|---|---|---|
| Cible | Marketers | Devs |
| Intégration | Semaines | Heures |
| Config | UI admin | YAML / code |
| Pricing | "Call us" | Self-serve |

**Détails complets :** `docs/projets/2026-04-19-loyalty-saas-architecture.md`

**Statut :** parked 2026-04-19. À reconsidérer quand trading auto tourne sans supervision OU quand Eagle Eye devient insupportable au boulot.

---

## Flow inter-projets (end-to-end trading)

```mermaid
sequenceDiagram
    participant T as Tony
    participant NB as Niam-Bay wake
    participant DB as Dashboard (autobot)
    participant GW as autobot-gateway
    participant M as martin :8081
    participant K as Kraken Futures
    participant S as autobot-sentinel
    participant TG as Telegram

    T->>NB: "reveille toi"
    NB->>NB: read memory.nb1
    NB->>M: curl /bot/balance
    NB->>GW: /api/stats/realized
    GW->>K: account-log (cached 5min)
    NB-->>T: briefing

    loop Every 15min
        M->>K: OHLC 4H
        M->>M: compute ADX/EMA/RSI
        alt ADX<40 + signal=OPEN
            M->>K: place grid orders
        else ADX>40 trending
            M->>K: cancel grid
        end
    end

    loop Every 5min
        S->>M: GET /grid/active
        S->>M: GET /grid/status/<pair>
        alt out of range / maxloss
            S->>M: POST /grid/stop
            S->>TG: alert
        end
    end

    loop Every 5s (dashboard open)
        DB->>M: /bot/balance, /grid/*
        DB->>GW: /api/stats/realized
        DB->>DB: render hero + tabs
    end

    Note over M,K: Auto-grid loop runs independently<br/>even without Tony
```

---

## Services / ports / cron sur VM

| Service | Port | Binaire | Rôle |
|---|---|---|---|
| `martin.service` | 8081 | Java | engine trading |
| `autobot-gateway` | 8443 | Python FastAPI | stats + proxy + WS |
| `autobot-api` | 8083 | Python HTTPServer | legacy summary |
| `autobot-sentinel` | — | Python | watchdog |
| `nginx` | 80, 443 | nginx | reverse proxy |
| (brain-api) | 8082 | Python | cerveau REST |
| (llm-proxy) | 8084 | Python | OpenAI-compat proxy |
| (crypto) | 8085 | uvicorn | crypto API |
| (cryptolens) | 8090 | Python | CryptoLens AI |
| (alexa-niambay) | 8095 | Python | Alexa hook |

**Cron :**
- `*/5 * * * *` — Martin keepalive ping
- `0 5 * * *` — `morning_brief_v2.py` → `/home/ubuntu/docs/`

---

## Règles critiques partagées

### Nonce Kraken
Tous les clients partagent la même API key. Nonce strictement monotone par key.
- Martin Java : `currentTimeMillis() × 5_000_000` ≈ 8.88e18
- Gateway Python : `time.time_ns() × 5` (même échelle)
- Scripts manuels : idem
- **Max safe :** 9.22e18 (Long.MAX_VALUE)

### Saves / commits
- `niam-bay` : commits fréquents (mémoire)
- `martin` + `autobot` : commits atomiques (trading = critique)
- Toujours `rtk git ...` devant (RTK golden rule)

### Mémoire NB
- Fichiers > RAM
- `.nb1` compressés > .md étendus
- Vector recall avant fichiers
- `dream` à la fin des sessions pour consolider

---

*Diagrammes générés 2026-04-19. Vérifiés E2E live.*
