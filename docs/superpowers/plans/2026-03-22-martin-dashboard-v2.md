# Martin Trading Dashboard v2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un dashboard de trading futuriste, temps réel tick par tick, multi-crypto, avec grid + scalping manuel/auto, déployé sur la VM Oracle nginx.

**Architecture:** Frontend standalone (HTML/JS/CSS) servi par nginx. Communique avec le backend Martin Java (port 8081) via SSE (ticks temps réel) et REST (actions). Chandeliers via lightweight-charts (TradingView open source). Deux thèmes : futuriste (défaut) et classique.

**Tech Stack:** HTML5/CSS3/JS vanilla, lightweight-charts v4 (CDN), SSE EventSource, REST fetch. Déployé sur nginx VM Oracle 141.253.108.141.

---

## File Structure

Tous les fichiers sont créés sur la VM via SSH dans `/home/ubuntu/trading-dashboard/` puis servis par nginx.

```
/home/ubuntu/trading-dashboard/
├── index.html
├── css/
│   ├── base.css              # Layout, reset, common
│   ├── theme-futuristic.css  # Thème futuriste (défaut)
│   └── theme-classic.css     # Thème TradingView-like
├── js/
│   ├── api.js                # REST client (fetch wrapper)
│   ├── ticker.js             # SSE connexion, prix temps réel
│   ├── chart.js              # lightweight-charts, chandeliers, indicateurs
│   ├── grid-panel.js         # Panel grid (statut, niveaux, contrôles)
│   ├── scalp-panel.js        # Panel scalping (buy/sell, positions, auto)
│   ├── notifications.js      # Toasts + sons sur fills
│   └── app.js                # Init, state, wiring
```

---

### Task 1: Squelette HTML + CSS base + thèmes

**Files:**
- Create: `index.html`
- Create: `css/base.css`
- Create: `css/theme-futuristic.css`
- Create: `css/theme-classic.css`

- [ ] **Step 1: Créer index.html**

Structure : header bar (paire selector, prix live, PnL, boutons thème/settings), main (graphe centre 60%, panels droite 40%), footer (stats VM, connexion, notifications). Charger lightweight-charts depuis CDN. Charger tous les JS en defer.

- [ ] **Step 2: Créer css/base.css**

Layout flex, reset, header/main/footer sizing, responsive breakpoints. Variables CSS pour les couleurs (--bg, --text, --accent, --buy, --sell, --panel-bg, --border).

- [ ] **Step 3: Créer css/theme-futuristic.css**

Override variables : --bg: #0a0a1a, --accent: #4fc3f7, --buy: #00e676, --sell: #ff1744. Glassmorphism (backdrop-filter blur), glow effects (box-shadow cyan), animations pulse. Fonts: system-ui.

- [ ] **Step 4: Créer css/theme-classic.css**

Override variables : --bg: #1a1a2e, --accent: #2196f3, --buy: #26a69a, --sell: #ef5350. Sobre, pas de glow, bordures solides.

- [ ] **Step 5: Déployer sur VM + configurer nginx**

```bash
ssh VM "mkdir -p /home/ubuntu/trading-dashboard/css /home/ubuntu/trading-dashboard/js"
# Upload files via cat/heredoc
# Add nginx location /trading/ -> /home/ubuntu/trading-dashboard/
# Test: curl http://141.253.108.141/trading/
```

- [ ] **Step 6: Commit local**

```bash
git commit -m "feat: dashboard skeleton + dual themes"
```

---

### Task 2: API client + Ticker SSE

**Files:**
- Create: `js/api.js`
- Create: `js/ticker.js`

- [ ] **Step 1: Créer js/api.js**

```javascript
const API = {
    base: '/api',

    async get(path) { /* fetch GET, parse JSON, handle errors */ },
    async post(path, data) { /* fetch POST JSON */ },

    // Grid
    async gridStatus(instrument) { return this.get(`/grid/status/${instrument}`); },
    async gridStart(params) { return this.post('/grid/start?' + new URLSearchParams(params)); },
    async gridStop(instrument) { return this.post(`/grid/stop/${instrument}`); },
    async gridActive() { return this.get('/grid/active'); },

    // Scalping
    async scalpOrder(params) { return this.post('/scalp/order', params); },
    async scalpPositions() { return this.get('/scalp/positions'); },
    async scalpBotStart(params) { return this.post('/scalp/bot/start', params); },
    async scalpBotStop(instrument) { return this.post(`/scalp/bot/stop/${instrument}`); },
    async scalpBotStatus(instrument) { return this.get(`/scalp/bot/status/${instrument}`); },

    // System
    async systemStatus() { return this.get('/system/status'); },
    async balance() { return this.get('/bot/balance'); },
    async openOrders() { return this.get('/bot/orders'); },
    async ohlc(instrument) { return this.get(`/bot/ohlc/${instrument}`); },
    async ticker() { return this.get('/bot/prices/all'); },

    // Top pairs by volume (Kraken public API)
    async topPairs() { /* fetch from futures.kraken.com/derivatives/api/v3/tickers, sort by volume, return top 10 */ },
};
```

- [ ] **Step 2: Créer js/ticker.js**

```javascript
const Ticker = {
    source: null,
    instrument: null,
    callbacks: { price: [], fill: [], status: [] },

    connect(instrument) {
        if (this.source) this.source.close();
        this.instrument = instrument;
        this.source = new EventSource(`/api/sse/dashboard/${instrument}`);
        this.source.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.price) this.callbacks.price.forEach(cb => cb(data.price, data));
            if (data.fill) this.callbacks.fill.forEach(cb => cb(data.fill));
        };
        this.source.onerror = () => { /* auto-reconnect after 3s */ };
    },

    on(event, callback) { this.callbacks[event].push(callback); },
    disconnect() { if (this.source) this.source.close(); },
};
```

- [ ] **Step 3: Déployer + tester**

Upload files, vérifier que SSE se connecte : ouvrir la console Chrome sur /trading/, vérifier `EventSource` connected.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: API client + SSE ticker"
```

---

### Task 3: Graphe chandeliers (lightweight-charts)

**Files:**
- Create: `js/chart.js`

- [ ] **Step 1: Créer js/chart.js**

```javascript
const Chart = {
    chart: null,
    candleSeries: null,
    volumeSeries: null,
    gridLines: [],      // horizontal lines for grid levels
    markers: [],         // buy/sell fill markers

    init(container) {
        // Create lightweight-charts instance
        // Dark theme matching our CSS vars
        // Candlestick series (green/red)
        // Volume histogram below
        // Crosshair, time scale, price scale
    },

    setTimeframe(tf) {
        // Load historical candles from API /bot/ohlc/{instrument}?interval={tf}
        // Set data on candleSeries
    },

    addTick(price, time) {
        // Update last candle or create new one based on timeframe
    },

    showGridLevels(levels) {
        // Draw horizontal lines at each grid level price
        // Green for buy, red for sell, orange for filled
    },

    addFillMarker(side, price, time) {
        // Add arrow marker on chart (up=buy green, down=sell red)
    },

    setIndicators(indicators) {
        // Toggle EMA, RSI, Bollinger overlays
    },

    resize() { this.chart.resize(...); },
    destroy() { this.chart.remove(); },
};
```

- [ ] **Step 2: Connecter au ticker**

In app.js : `Ticker.on('price', (p) => Chart.addTick(p))`. Load historical on instrument change.

- [ ] **Step 3: Déployer + tester visuellement**

Ouvrir /trading/, vérifier chandeliers visibles avec prix live.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: candlestick chart with live ticks"
```

---

### Task 4: Panel Grid

**Files:**
- Create: `js/grid-panel.js`

- [ ] **Step 1: Créer js/grid-panel.js**

```javascript
const GridPanel = {
    container: null,

    init(container) {
        // Create DOM: status indicator, levels list, controls, stats
    },

    update(gridStatus) {
        // Update levels display (colored bars: green=buy, red=sell)
        // Update RT count, profit, fills
        // Show/hide start/stop buttons
    },

    renderLevels(levels, currentPrice) {
        // Visual bar chart of levels with price labels
        // Animate when a fill happens
        // Current price marker
    },

    // Controls
    onStart(instrument, capital, leverage, spacing, levels, maxLoss) {
        return API.gridStart({ instrument, capital, leverage, gridSpacingPct: spacing, totalLevels: levels, maxLossPercent: maxLoss });
    },

    onStop(instrument) { return API.gridStop(instrument); },

    // Multi-grid tabs
    renderTabs(activeGrids) {
        // Tab per active grid instrument
    },
};
```

- [ ] **Step 2: Start/stop grid form**

Inputs : capital, leverage (slider 1-20), spacing % (slider 0.5-5), levels (3-10), maxLoss %. Bouton Start / Stop.

- [ ] **Step 3: Polling grid status toutes les 2s**

```javascript
setInterval(async () => {
    const status = await API.gridStatus(currentInstrument);
    GridPanel.update(status);
    Chart.showGridLevels(status.levels);
}, 2000);
```

- [ ] **Step 4: Déployer + tester**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: grid panel with controls + multi-grid tabs"
```

---

### Task 5: Panel Scalping

**Files:**
- Create: `js/scalp-panel.js`

- [ ] **Step 1: Créer js/scalp-panel.js**

```javascript
const ScalpPanel = {
    container: null,

    init(container) {
        // BIG buy/sell buttons (prominent, colored)
        // Size input with quick buttons (25%, 50%, 100%)
        // Position list with live PnL
        // Auto-scalp toggle + params
        // Trade history today
    },

    async buy(instrument, size) {
        const result = await API.scalpOrder({ instrument, side: 'buy', size, orderType: 'mkt' });
        Notifications.show('BUY', `${size} ${instrument} @ market`, 'buy');
        this.refreshPositions();
    },

    async sell(instrument, size) {
        const result = await API.scalpOrder({ instrument, side: 'sell', size, orderType: 'mkt' });
        Notifications.show('SELL', `${size} ${instrument} @ market`, 'sell');
        this.refreshPositions();
    },

    async refreshPositions() {
        const positions = await API.scalpPositions();
        this.renderPositions(positions);
    },

    renderPositions(positions) {
        // Each position: instrument, side, size, entry price, current PnL (colored)
        // Close button per position
    },

    // Auto scalp
    toggleAuto(instrument, params) {
        // Start/stop scalping bot via API
    },
};
```

- [ ] **Step 2: Keyboard shortcuts**

Enter = buy, Shift+Enter = sell. Espace = close position.

- [ ] **Step 3: Déployer + tester**

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: scalping panel — manual buy/sell + auto mode"
```

---

### Task 6: Notifications + sons

**Files:**
- Create: `js/notifications.js`

- [ ] **Step 1: Créer js/notifications.js**

```javascript
const Notifications = {
    container: null,

    init(container) { /* create notification area top-right */ },

    show(title, message, type) {
        // type: 'info', 'buy', 'sell', 'alert', 'fill'
        // Toast slide-in, auto-dismiss 5s
        // Color by type: buy=green, sell=red, fill=orange, alert=red
        // Sound on fill and alert
    },

    playSound(type) {
        // Use Web Audio API to generate beep
        // buy: ascending tone
        // sell: descending tone
        // fill: double beep
        // alert: alarm
    },
};
```

- [ ] **Step 2: Wire fill notifications**

```javascript
Ticker.on('fill', (fill) => {
    Notifications.show('FILL', `${fill.side} @ ${fill.price}`, 'fill');
    Chart.addFillMarker(fill.side, fill.price, fill.time);
});
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: notifications with sounds on fills"
```

---

### Task 7: Header bar — sélecteur paires + prix live + PnL

**Files:**
- Modify: `index.html` (header section)
- Modify: `js/app.js`

- [ ] **Step 1: Sélecteur de paire**

Dropdown qui charge les top 10 paires par volume depuis Kraken public API. On instrument change: reconnect ticker, reload chart, reload grid status.

- [ ] **Step 2: Prix live animé**

Gros prix au centre du header. Flash vert quand monte, flash rouge quand descend. Pourcentage 24h à côté.

- [ ] **Step 3: PnL bar**

Aujourd'hui | 3 jours | Semaine | Mois — avec couleurs (vert positif, rouge négatif). Charge depuis `/api/martin` (l'endpoint qu'on a créé).

- [ ] **Step 4: Boutons thème + settings**

Toggle thème : swap la CSS class sur body. Settings : modal avec config grid/scalp par défaut.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: header — pair selector, live price, PnL, theme toggle"
```

---

### Task 8: Footer bar — stats VM + connexion

**Files:**
- Modify: `index.html` (footer section)
- Modify: `js/app.js`

- [ ] **Step 1: Stats VM**

Poll `/api/system/status` toutes les 10s. Afficher CPU, RAM, uptime.

- [ ] **Step 2: Stats trading**

RT aujourd'hui, fills total, profit total. Charge depuis grid status.

- [ ] **Step 3: Indicateur connexion**

Dot vert = SSE connecté, rouge = déconnecté. Nombre de ticks/seconde.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: footer — VM stats, trading stats, connection indicator"
```

---

### Task 9: App.js — assemblage final

**Files:**
- Create: `js/app.js`

- [ ] **Step 1: Init all modules**

```javascript
document.addEventListener('DOMContentLoaded', async () => {
    // Load top pairs
    const pairs = await API.topPairs();
    renderPairSelector(pairs);

    // Init modules
    Chart.init(document.getElementById('chart-container'));
    GridPanel.init(document.getElementById('grid-panel'));
    ScalpPanel.init(document.getElementById('scalp-panel'));
    Notifications.init(document.getElementById('notifications'));

    // Connect to default pair (first active grid or first top pair)
    const activeGrids = await API.gridActive();
    const defaultPair = activeGrids[0] || pairs[0].symbol;
    switchInstrument(defaultPair);

    // Start polling
    startPolling();
});
```

- [ ] **Step 2: switchInstrument function**

Disconnect old ticker, connect new, reload chart history, reload grid status, update header.

- [ ] **Step 3: Theme toggle**

Load saved theme from localStorage, toggle on click, persist.

- [ ] **Step 4: Responsive**

Mobile : panels stack vertically, chart takes full width above, panels below.

- [ ] **Step 5: Déployer tout + test end-to-end**

Upload all files to VM, verify in Chrome : chart visible, ticks moving, grid panel shows ADA levels, buy/sell buttons work.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: dashboard v2 complete — chart + grid + scalp + notifications"
```

---

## Récapitulatif

| Task | Composant | Type |
|------|-----------|------|
| 1 | HTML + CSS + thèmes | Frontend |
| 2 | API client + SSE ticker | Frontend |
| 3 | Graphe chandeliers | Frontend |
| 4 | Panel Grid | Frontend |
| 5 | Panel Scalping | Frontend |
| 6 | Notifications + sons | Frontend |
| 7 | Header (paires, prix, PnL) | Frontend |
| 8 | Footer (stats, connexion) | Frontend |
| 9 | App.js assemblage | Frontend |
| **Total** | **9 tasks** | |

Après : ouvrir `http://141.253.108.141/trading/` → voir les chandeliers live, la grid ADA, pouvoir scalper, recevoir les notifications de fills, switcher entre cryptos. Futuriste et beau.
