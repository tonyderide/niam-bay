# Design: Claude Tray — Usage Monitor

**Date**: 2026-04-05
**Status**: Approved
**Author**: Niam-Bay + Tony

## Goal

A Windows system tray app that shows Claude usage (session, weekly, Sonnet) as 3 concentric circular gauges in the tray icon, with a popup for details.

## Data Source

**Endpoint:** `GET https://api.anthropic.com/api/oauth/usage`

**Auth:** Bearer token from `~/.claude/.credentials.json` → `claudeAiOauth.accessToken`

**Header:** `anthropic-beta: oauth-2025-04-20`

**Response:**
```json
{
  "five_hour": { "utilization": 8.0, "resets_at": "2026-04-05T22:30:00Z" },
  "seven_day": { "utilization": 62.0, "resets_at": "2026-04-08T08:00:00Z" },
  "seven_day_sonnet": { "utilization": 39.0, "resets_at": "2026-04-09T00:00:00Z" }
}
```

**Refresh:** Every 5 minutes (cache to avoid 429 rate-limit).

**Token refresh:** If 401, use refresh_token from same credentials file to get new access_token via `POST https://console.anthropic.com/v1/oauth/token`.

---

## Tray Icon (16x16 / 32x32)

3 concentric circular arcs (donut style):
- **Outer ring** = session (5h) usage %
- **Middle ring** = weekly all-models (7d) usage %
- **Inner ring** = weekly Sonnet (7d) usage %

Color per ring based on utilization:
- `< 50%` → green (#00ff88)
- `50-80%` → orange (#ffaa00)
- `> 80%` → red (#ff3366)

Background: transparent. The arcs fill clockwise proportional to usage %.

---

## Tooltip

On hover: `Session: 8% | Hebdo: 62% | Sonnet: 39%`

---

## Popup (left click)

Small borderless window anchored above the tray icon. Dark theme.

Content:
- 3 horizontal progress bars with labels:
  - `Session (5h)  ████████░░░░  8%   — Reset dans 4h07`
  - `Hebdo          ██████████░░  62%  — Reset mer. 10:00`
  - `Sonnet          ████████░░░░  39%  — Reset jeu. 02:00`
- Each bar colored green/orange/red per threshold
- "Derniere MAJ: il y a 2 min" at bottom
- Click outside to close

---

## Architecture

```
claude-tray/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs          # Tauri entry, tray setup
│   │   ├── usage.rs         # HTTP client, fetch usage, cache
│   │   ├── credentials.rs   # Read/refresh OAuth token
│   │   └── tray.rs          # Generate tray icon image (3 rings)
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                     # Frontend (popup)
│   ├── index.html
│   ├── style.css
│   └── main.js
├── .gitignore
└── README.md
```

### Rust modules

**credentials.rs**
- `read_token()` — parse `~/.claude/.credentials.json`, return access_token
- `refresh_token()` — POST to console.anthropic.com, save new tokens

**usage.rs**
- `UsageData { five_hour, seven_day, seven_day_sonnet }` struct
- `fetch_usage(token) -> Result<UsageData>` — GET endpoint, parse JSON
- `CachedUsage` — stores last result + timestamp, only re-fetches after 300s

**tray.rs**
- `generate_icon(usage: &UsageData) -> Vec<u8>` — render 32x32 RGBA image with 3 concentric arcs using simple math (no GPU, just pixel manipulation)
- Color logic: green/orange/red per threshold

**main.rs**
- Tauri app with `system_tray` (no window on startup)
- Timer every 300s: fetch usage → update icon + tooltip
- Left click: open popup window
- Right click: menu with "Refresh", "Quit"

### Frontend (popup)

- `index.html` — 3 progress bars, reset timers
- `main.js` — calls Tauri command `get_usage()` to get cached data
- `style.css` — dark theme, compact, no frame

---

## Config

No config file needed. Reads token from `~/.claude/.credentials.json` (standard Claude Code location).

If token not found: tray icon shows grey rings + tooltip "Token not found — run Claude Code first".

---

## Constraints

- **Rate limit:** Max 1 request per 300s. Cache aggressively.
- **Token refresh:** Single-use refresh tokens — must save both new access + refresh tokens atomically.
- **No EUR balance:** The overage/credits balance requires browser session auth — out of scope for v1.
- **Windows only** for now (tray behavior). Tauri supports macOS/Linux later.
- **Undocumented API** — may break. App should handle errors gracefully (show last known data + "API error" indicator).
