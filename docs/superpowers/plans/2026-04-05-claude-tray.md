# Claude Tray — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Windows system tray app that shows Claude usage limits (session, weekly, Sonnet) as 3 concentric circular gauges, with a popup for details.

**Architecture:** Tauri 2 app with 4 Rust modules (credentials, usage, tray icon, main) and a minimal HTML/CSS/JS popup. Fetches usage from Anthropic OAuth API every 5 min, renders a 32x32 icon with 3 colored arcs, updates tooltip. Left-click opens popup, right-click shows Refresh/Quit menu.

**Tech Stack:** Rust 1.94, Tauri 2, reqwest, serde, image crate for icon rendering. Vanilla HTML/CSS/JS frontend.

**Spec:** `docs/superpowers/specs/2026-04-05-claude-tray-design.md`

**Credentials:** `~/.claude/.credentials.json` → `claudeAiOauth.accessToken` (verified: has accessToken, refreshToken, expiresAt, scopes, subscriptionType, rateLimitTier)

---

## Task 1: Project scaffolding

**Files:**
- Create: `claude-tray/` project via `cargo tauri init`
- Create: `claude-tray/.gitignore`
- Create: `claude-tray/README.md`

- [ ] **Step 1: Install Tauri CLI**

```bash
cargo install tauri-cli --locked
```

Expected: `tauri-cli` installed. Verify: `cargo tauri --version` → `tauri-cli 2.x.x`

- [ ] **Step 2: Create project directory and GitHub repo**

```bash
cd C:/Users/tony_/Documents
mkdir claude-tray && cd claude-tray
gh repo create tonyderide/claude-tray --private --description "Claude usage monitor — system tray with 3 concentric gauges (Tauri + Rust)"
git init && git config user.name "Niam-Bay" && git config user.email "niam-bay@github.com"
git remote add origin https://github.com/tonyderide/claude-tray.git
```

- [ ] **Step 3: Initialize Tauri project**

```bash
cd C:/Users/tony_/Documents/claude-tray
cargo tauri init
```

When prompted:
- App name: `claude-tray`
- Window title: `Claude Tray`
- Frontend dev URL: `../src` (static files)
- Frontend dist: `../src`
- Dev command: (leave empty)
- Build command: (leave empty)

- [ ] **Step 4: Create frontend directory with placeholder**

```bash
mkdir -p src
```

Create `src/index.html`:
```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Claude Tray</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="app">Loading...</div>
  <script src="main.js"></script>
</body>
</html>
```

Create `src/style.css`:
```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #1a1a2e; color: #e8e8f0; font-family: 'Segoe UI', sans-serif; }
#app { padding: 16px; }
```

Create `src/main.js`:
```javascript
// placeholder
document.getElementById('app').textContent = 'Claude Tray';
```

- [ ] **Step 5: Add dependencies to Cargo.toml**

In `src-tauri/Cargo.toml`, add under `[dependencies]`:

```toml
serde = { version = "1", features = ["derive"] }
serde_json = "1"
reqwest = { version = "0.12", features = ["json", "rustls-tls"], default-features = false }
tokio = { version = "1", features = ["full"] }
dirs = "6"
chrono = { version = "0.4", features = ["serde"] }
image = "0.25"
```

- [ ] **Step 6: Configure tauri.conf.json for tray-only app**

Edit `src-tauri/tauri.conf.json`. Set:
```json
{
  "productName": "claude-tray",
  "identifier": "com.niambay.claude-tray",
  "build": {
    "frontendDist": "../src"
  },
  "app": {
    "withGlobalTauri": true,
    "windows": []
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": ["icons/icon.png"]
  }
}
```

Key: `"windows": []` — no window on startup, tray only.

- [ ] **Step 7: Create .gitignore**

```
target/
node_modules/
dist/
*.exe
.env
```

- [ ] **Step 8: Verify it compiles**

```bash
cd C:/Users/tony_/Documents/claude-tray/src-tauri
cargo check
```

Expected: compiles with no errors (warnings OK).

- [ ] **Step 9: Commit**

```bash
cd C:/Users/tony_/Documents/claude-tray
git add -A
git commit -m "init: Tauri 2 project scaffold for claude-tray"
```

---

## Task 2: credentials.rs — Read and refresh OAuth token

**Files:**
- Create: `src-tauri/src/credentials.rs`

- [ ] **Step 1: Create credentials module**

Create `src-tauri/src/credentials.rs`:

```rust
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct OAuthCredentials {
    pub access_token: String,
    pub refresh_token: String,
    pub expires_at: Option<String>,
    pub scopes: Option<Vec<String>>,
    pub subscription_type: Option<String>,
    pub rate_limit_tier: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
struct CredentialsFile {
    claude_ai_oauth: OAuthCredentials,
}

#[derive(Debug, Deserialize)]
struct TokenResponse {
    access_token: String,
    refresh_token: String,
}

fn credentials_path() -> PathBuf {
    let home = dirs::home_dir().expect("No home directory");
    home.join(".claude").join(".credentials.json")
}

pub fn read_token() -> Result<String, String> {
    let path = credentials_path();
    let content = fs::read_to_string(&path)
        .map_err(|e| format!("Cannot read {:?}: {}", path, e))?;
    let creds: CredentialsFile = serde_json::from_str(&content)
        .map_err(|e| format!("Invalid credentials JSON: {}", e))?;
    Ok(creds.claude_ai_oauth.access_token)
}

pub fn read_refresh_token() -> Result<String, String> {
    let path = credentials_path();
    let content = fs::read_to_string(&path)
        .map_err(|e| format!("Cannot read {:?}: {}", path, e))?;
    let creds: CredentialsFile = serde_json::from_str(&content)
        .map_err(|e| format!("Invalid credentials JSON: {}", e))?;
    Ok(creds.claude_ai_oauth.refresh_token)
}

pub async fn refresh_access_token(refresh_tok: &str) -> Result<(String, String), String> {
    let client = reqwest::Client::new();
    let resp = client
        .post("https://console.anthropic.com/v1/oauth/token")
        .json(&serde_json::json!({
            "grant_type": "refresh_token",
            "refresh_token": refresh_tok,
            "client_id": "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
        }))
        .send()
        .await
        .map_err(|e| format!("Token refresh request failed: {}", e))?;

    if !resp.status().is_success() {
        return Err(format!("Token refresh HTTP {}", resp.status()));
    }

    let token_resp: TokenResponse = resp.json().await
        .map_err(|e| format!("Token refresh parse error: {}", e))?;

    // Atomic write: write to temp file then rename
    let path = credentials_path();
    let content = fs::read_to_string(&path)
        .map_err(|e| format!("Cannot read credentials for update: {}", e))?;
    let mut creds: CredentialsFile = serde_json::from_str(&content)
        .map_err(|e| format!("Invalid credentials JSON: {}", e))?;

    creds.claude_ai_oauth.access_token = token_resp.access_token.clone();
    creds.claude_ai_oauth.refresh_token = token_resp.refresh_token.clone();

    let tmp_path = path.with_extension("json.tmp");
    let new_content = serde_json::to_string_pretty(&creds)
        .map_err(|e| format!("Serialize error: {}", e))?;
    fs::write(&tmp_path, &new_content)
        .map_err(|e| format!("Write tmp failed: {}", e))?;
    fs::rename(&tmp_path, &path)
        .map_err(|e| format!("Rename failed: {}", e))?;

    Ok((token_resp.access_token, token_resp.refresh_token))
}
```

- [ ] **Step 2: Register module in main.rs**

Add to `src-tauri/src/main.rs`:
```rust
mod credentials;
```

- [ ] **Step 3: Verify it compiles**

```bash
cd C:/Users/tony_/Documents/claude-tray/src-tauri && cargo check
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/tony_/Documents/claude-tray
git add -A && git commit -m "feat: credentials.rs — read/refresh OAuth token from ~/.claude/.credentials.json"
```

---

## Task 3: usage.rs — Fetch and cache usage data

**Files:**
- Create: `src-tauri/src/usage.rs`

- [ ] **Step 1: Create usage module**

Create `src-tauri/src/usage.rs`:

```rust
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::time::Instant;

use crate::credentials;

const CACHE_DURATION_SECS: u64 = 300;
const USAGE_URL: &str = "https://api.anthropic.com/api/oauth/usage";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageBucket {
    pub utilization: f64,
    pub resets_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageData {
    pub five_hour: UsageBucket,
    pub seven_day: UsageBucket,
    pub seven_day_sonnet: Option<UsageBucket>,
}

impl Default for UsageData {
    fn default() -> Self {
        Self {
            five_hour: UsageBucket { utilization: 0.0, resets_at: String::new() },
            seven_day: UsageBucket { utilization: 0.0, resets_at: String::new() },
            seven_day_sonnet: None,
        }
    }
}

pub struct CachedUsage {
    pub data: UsageData,
    pub last_fetch: Option<Instant>,
    pub error: Option<String>,
}

impl Default for CachedUsage {
    fn default() -> Self {
        Self { data: UsageData::default(), last_fetch: None, error: None }
    }
}

pub type UsageState = Mutex<CachedUsage>;

pub async fn fetch_usage_if_stale(state: &UsageState) -> UsageData {
    {
        let cache = state.lock().unwrap();
        if let Some(last) = cache.last_fetch {
            if last.elapsed().as_secs() < CACHE_DURATION_SECS {
                return cache.data.clone();
            }
        }
    }

    match fetch_usage().await {
        Ok(data) => {
            let mut cache = state.lock().unwrap();
            cache.data = data.clone();
            cache.last_fetch = Some(Instant::now());
            cache.error = None;
            data
        }
        Err(e) => {
            let mut cache = state.lock().unwrap();
            cache.error = Some(e);
            cache.last_fetch = Some(Instant::now()); // don't retry immediately
            cache.data.clone()
        }
    }
}

async fn fetch_usage() -> Result<UsageData, String> {
    let token = credentials::read_token()?;

    let client = reqwest::Client::new();
    let resp = client
        .get(USAGE_URL)
        .header("Authorization", format!("Bearer {}", token))
        .header("anthropic-beta", "oauth-2025-04-20")
        .header("Content-Type", "application/json")
        .send()
        .await
        .map_err(|e| format!("Usage request failed: {}", e))?;

    if resp.status().as_u16() == 401 {
        // Try token refresh
        let refresh_tok = credentials::read_refresh_token()?;
        let (new_token, _) = credentials::refresh_access_token(&refresh_tok).await?;

        let resp2 = client
            .get(USAGE_URL)
            .header("Authorization", format!("Bearer {}", new_token))
            .header("anthropic-beta", "oauth-2025-04-20")
            .header("Content-Type", "application/json")
            .send()
            .await
            .map_err(|e| format!("Usage retry failed: {}", e))?;

        if !resp2.status().is_success() {
            return Err(format!("Usage API HTTP {} after refresh", resp2.status()));
        }

        return resp2.json::<UsageData>().await
            .map_err(|e| format!("Usage parse error: {}", e));
    }

    if !resp.status().is_success() {
        return Err(format!("Usage API HTTP {}", resp.status()));
    }

    resp.json::<UsageData>().await
        .map_err(|e| format!("Usage parse error: {}", e))
}
```

- [ ] **Step 2: Register module**

Add to `src-tauri/src/main.rs`:
```rust
mod usage;
```

- [ ] **Step 3: Verify it compiles**

```bash
cd C:/Users/tony_/Documents/claude-tray/src-tauri && cargo check
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/tony_/Documents/claude-tray
git add -A && git commit -m "feat: usage.rs — fetch and cache Claude usage data with 5min TTL"
```

---

## Task 4: tray.rs — Generate tray icon with 3 concentric rings

**Files:**
- Create: `src-tauri/src/tray.rs`

- [ ] **Step 1: Create tray icon renderer**

Create `src-tauri/src/tray.rs`:

```rust
use crate::usage::UsageData;

const SIZE: u32 = 32;
const CENTER: f64 = 15.5;

struct Ring {
    radius: f64,
    width: f64,
}

const RINGS: [Ring; 3] = [
    Ring { radius: 13.0, width: 3.5 }, // outer = session
    Ring { radius: 9.0,  width: 3.5 }, // middle = weekly
    Ring { radius: 5.0,  width: 3.0 }, // inner = sonnet
];

fn color_for_pct(pct: f64) -> [u8; 4] {
    if pct > 80.0 {
        [0xff, 0x33, 0x66, 0xff] // red
    } else if pct > 50.0 {
        [0xff, 0xaa, 0x00, 0xff] // orange
    } else {
        [0x00, 0xff, 0x88, 0xff] // green
    }
}

fn grey() -> [u8; 4] {
    [0x40, 0x40, 0x50, 0xff]
}

pub fn generate_icon(usage: &UsageData) -> Vec<u8> {
    let mut pixels = vec![0u8; (SIZE * SIZE * 4) as usize];

    let pcts = [
        usage.five_hour.utilization,
        usage.seven_day.utilization,
        usage.seven_day_sonnet.as_ref().map(|s| s.utilization).unwrap_or(0.0),
    ];

    for y in 0..SIZE {
        for x in 0..SIZE {
            let dx = x as f64 - CENTER;
            let dy = y as f64 - CENTER;
            let dist = (dx * dx + dy * dy).sqrt();

            // Angle: 0 = top, clockwise, in range [0, 1)
            let angle = (dx.atan2(-dy) / std::f64::consts::TAU + 0.5).fract();

            let idx = ((y * SIZE + x) * 4) as usize;

            for (i, ring) in RINGS.iter().enumerate() {
                let inner = ring.radius - ring.width / 2.0;
                let outer = ring.radius + ring.width / 2.0;

                if dist >= inner && dist <= outer {
                    let pct = pcts[i];
                    let fill = pct / 100.0;

                    if angle <= fill {
                        let c = color_for_pct(pct);
                        pixels[idx..idx + 4].copy_from_slice(&c);
                    } else {
                        let c = grey();
                        pixels[idx..idx + 4].copy_from_slice(&c);
                    }
                    break;
                }
            }
        }
    }

    pixels
}

pub fn generate_grey_icon() -> Vec<u8> {
    let mut pixels = vec![0u8; (SIZE * SIZE * 4) as usize];

    for y in 0..SIZE {
        for x in 0..SIZE {
            let dx = x as f64 - CENTER;
            let dy = y as f64 - CENTER;
            let dist = (dx * dx + dy * dy).sqrt();
            let idx = ((y * SIZE + x) * 4) as usize;

            for ring in &RINGS {
                let inner = ring.radius - ring.width / 2.0;
                let outer = ring.radius + ring.width / 2.0;
                if dist >= inner && dist <= outer {
                    pixels[idx..idx + 4].copy_from_slice(&grey());
                    break;
                }
            }
        }
    }

    pixels
}

pub fn tooltip_text(usage: &UsageData) -> String {
    let sonnet = usage.seven_day_sonnet.as_ref()
        .map(|s| format!(" | Sonnet: {:.0}%", s.utilization))
        .unwrap_or_default();
    format!(
        "Session: {:.0}% | Hebdo: {:.0}%{}",
        usage.five_hour.utilization,
        usage.seven_day.utilization,
        sonnet
    )
}
```

- [ ] **Step 2: Register module**

Add to `src-tauri/src/main.rs`:
```rust
mod tray;
```

- [ ] **Step 3: Verify it compiles**

```bash
cd C:/Users/tony_/Documents/claude-tray/src-tauri && cargo check
```

- [ ] **Step 4: Commit**

```bash
cd C:/Users/tony_/Documents/claude-tray
git add -A && git commit -m "feat: tray.rs — render 32x32 icon with 3 concentric colored rings"
```

---

## Task 5: main.rs — Wire everything together

**Files:**
- Modify: `src-tauri/src/main.rs`

- [ ] **Step 1: Write main.rs**

Replace `src-tauri/src/main.rs` entirely:

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod credentials;
mod tray;
mod usage;

use std::sync::Mutex;
use tauri::{
    image::Image,
    menu::{MenuBuilder, MenuItemBuilder},
    tray::TrayIconBuilder,
    Manager,
    WindowEvent,
};
use usage::{CachedUsage, UsageState};

#[tauri::command]
fn get_usage(state: tauri::State<'_, UsageState>) -> Result<usage::UsageData, String> {
    let cache = state.lock().unwrap();
    Ok(cache.data.clone())
}

#[tauri::command]
fn get_error(state: tauri::State<'_, UsageState>) -> Option<String> {
    let cache = state.lock().unwrap();
    cache.error.clone()
}

#[tauri::command]
fn get_last_fetch(state: tauri::State<'_, UsageState>) -> Option<u64> {
    let cache = state.lock().unwrap();
    cache.last_fetch.map(|t| t.elapsed().as_secs())
}

fn update_tray_icon(app: &tauri::AppHandle, data: &usage::UsageData) {
    let pixels = tray::generate_icon(data);
    let icon = Image::new_owned(pixels, 32, 32);
    if let Some(tray) = app.tray_by_id("main") {
        let _ = tray.set_icon(Some(icon));
        let _ = tray.set_tooltip(Some(&tray::tooltip_text(data)));
    }
}

fn main() {
    tauri::Builder::default()
        .manage(Mutex::new(CachedUsage::default()) as UsageState)
        .setup(|app| {
            let handle = app.handle().clone();

            // Right-click menu
            let refresh = MenuItemBuilder::with_id("refresh", "Refresh").build(app)?;
            let quit = MenuItemBuilder::with_id("quit", "Quit").build(app)?;
            let menu = MenuBuilder::new(app).items(&[&refresh, &quit]).build()?;

            // Grey icon on startup
            let grey_pixels = tray::generate_grey_icon();
            let grey_icon = Image::new_owned(grey_pixels, 32, 32);

            let _tray = TrayIconBuilder::with_id("main")
                .icon(grey_icon)
                .tooltip("Claude Tray — loading...")
                .menu(&menu)
                .on_menu_event(move |app, event| {
                    match event.id().as_ref() {
                        "quit" => app.exit(0),
                        "refresh" => {
                            let h = app.clone();
                            tauri::async_runtime::spawn(async move {
                                let state = h.state::<UsageState>();
                                {
                                    let mut cache = state.lock().unwrap();
                                    cache.last_fetch = None; // force refresh
                                }
                                let data = usage::fetch_usage_if_stale(&state).await;
                                update_tray_icon(&h, &data);
                            });
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let tauri::tray::TrayIconEvent::Click {
                        button: tauri::tray::MouseButton::Left,
                        button_state: tauri::tray::MouseButtonState::Up,
                        position,
                        ..
                    } = event {
                        let app = tray.app_handle();
                        if let Some(win) = app.get_webview_window("popup") {
                            let _ = win.set_position(tauri::Position::Physical(
                                tauri::PhysicalPosition {
                                    x: position.x as i32 - 150,
                                    y: position.y as i32 - 220,
                                }
                            ));
                            let _ = win.show();
                            let _ = win.set_focus();
                        } else {
                            let _ = tauri::WebviewWindowBuilder::new(
                                app,
                                "popup",
                                tauri::WebviewUrl::App("index.html".into()),
                            )
                            .title("Claude Usage")
                            .inner_size(300.0, 200.0)
                            .decorations(false)
                            .resizable(false)
                            .always_on_top(true)
                            .position(
                                position.x - 150.0,
                                position.y - 220.0,
                            )
                            .build();
                        }
                    }
                })
                .build(app)?;

            // Periodic fetch every 300s
            tauri::async_runtime::spawn(async move {
                loop {
                    let state = handle.state::<UsageState>();
                    let data = usage::fetch_usage_if_stale(&state).await;
                    update_tray_icon(&handle, &data);
                    tokio::time::sleep(std::time::Duration::from_secs(300)).await;
                }
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            // Close popup on focus loss
            if window.label() == "popup" {
                if let WindowEvent::Focused(false) = event {
                    let _ = window.hide();
                }
            }
        })
        .invoke_handler(tauri::generate_handler![get_usage, get_error, get_last_fetch])
        .run(tauri::generate_context!())
        .expect("error running claude-tray");
}
```

- [ ] **Step 2: Verify it compiles**

```bash
cd C:/Users/tony_/Documents/claude-tray/src-tauri && cargo check
```

Fix any compilation errors (API may vary slightly with Tauri version). Key things to adjust:
- `Image::new_owned` may be `Image::from_bytes` or `tauri::image::Image::new`
- Window event API may need `matches!` pattern

- [ ] **Step 3: Commit**

```bash
cd C:/Users/tony_/Documents/claude-tray
git add -A && git commit -m "feat: main.rs — tray icon, periodic refresh, popup window, right-click menu"
```

---

## Task 6: Frontend popup

**Files:**
- Modify: `src/index.html`
- Modify: `src/style.css`
- Modify: `src/main.js`

- [ ] **Step 1: Write index.html**

Replace `src/index.html`:

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Claude Usage</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="app">
    <div class="bar-group">
      <div class="bar-row">
        <span class="label">Session (5h)</span>
        <div class="bar"><div class="fill" id="bar-session"></div></div>
        <span class="pct" id="pct-session">—</span>
      </div>
      <div class="reset" id="reset-session"></div>
    </div>
    <div class="bar-group">
      <div class="bar-row">
        <span class="label">Hebdo</span>
        <div class="bar"><div class="fill" id="bar-weekly"></div></div>
        <span class="pct" id="pct-weekly">—</span>
      </div>
      <div class="reset" id="reset-weekly"></div>
    </div>
    <div class="bar-group" id="sonnet-group">
      <div class="bar-row">
        <span class="label">Sonnet</span>
        <div class="bar"><div class="fill" id="bar-sonnet"></div></div>
        <span class="pct" id="pct-sonnet">—</span>
      </div>
      <div class="reset" id="reset-sonnet"></div>
    </div>
    <div class="footer" id="footer">Chargement...</div>
  </div>
  <script src="main.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write style.css**

Replace `src/style.css`:

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #1a1a2e;
  color: #e8e8f0;
  font-family: 'Segoe UI', sans-serif;
  font-size: 13px;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.08);
}

#app { padding: 14px 16px; }

.bar-group { margin-bottom: 10px; }
.bar-group:last-of-type { margin-bottom: 8px; }

.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label {
  width: 80px;
  font-size: 12px;
  color: #9090a8;
  flex-shrink: 0;
}

.bar {
  flex: 1;
  height: 8px;
  background: #2a2a3e;
  border-radius: 4px;
  overflow: hidden;
}

.fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease, background-color 0.5s ease;
  width: 0%;
}

.pct {
  width: 35px;
  text-align: right;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.reset {
  font-size: 10px;
  color: #5a5a70;
  margin-top: 2px;
  margin-left: 88px;
}

.footer {
  font-size: 10px;
  color: #5a5a70;
  text-align: center;
  margin-top: 4px;
  padding-top: 6px;
  border-top: 1px solid rgba(255,255,255,0.05);
}
```

- [ ] **Step 3: Write main.js**

Replace `src/main.js`:

```javascript
const { invoke } = window.__TAURI__.core;

function colorForPct(pct) {
  if (pct > 80) return '#ff3366';
  if (pct > 50) return '#ffaa00';
  return '#00ff88';
}

function formatReset(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  const now = new Date();
  const diff = d - now;
  if (diff <= 0) return 'Reset imminent';
  const hours = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  if (hours > 24) {
    const days = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
    return `Reset ${days[d.getDay()]} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
  }
  return `Reset dans ${hours}h${String(mins).padStart(2, '0')}`;
}

function setBar(id, pct, resetAt) {
  const fill = document.getElementById(`bar-${id}`);
  const pctEl = document.getElementById(`pct-${id}`);
  const resetEl = document.getElementById(`reset-${id}`);
  fill.style.width = `${Math.min(pct, 100)}%`;
  fill.style.backgroundColor = colorForPct(pct);
  pctEl.textContent = `${Math.round(pct)}%`;
  pctEl.style.color = colorForPct(pct);
  resetEl.textContent = formatReset(resetAt);
}

async function update() {
  try {
    const data = await invoke('get_usage');
    const elapsed = await invoke('get_last_fetch');
    const error = await invoke('get_error');

    setBar('session', data.five_hour.utilization, data.five_hour.resets_at);
    setBar('weekly', data.seven_day.utilization, data.seven_day.resets_at);

    const sonnetGroup = document.getElementById('sonnet-group');
    if (data.seven_day_sonnet) {
      sonnetGroup.style.display = 'block';
      setBar('sonnet', data.seven_day_sonnet.utilization, data.seven_day_sonnet.resets_at);
    } else {
      sonnetGroup.style.display = 'none';
    }

    let footer = '';
    if (error) footer = `Erreur: ${error}`;
    else if (elapsed != null) {
      const mins = Math.floor(elapsed / 60);
      footer = mins === 0 ? 'MAJ: maintenant' : `MAJ: il y a ${mins} min`;
    }
    document.getElementById('footer').textContent = footer;
  } catch (e) {
    document.getElementById('footer').textContent = `Erreur: ${e}`;
  }
}

update();
```

- [ ] **Step 4: Verify full build**

```bash
cd C:/Users/tony_/Documents/claude-tray/src-tauri && cargo build
```

- [ ] **Step 5: Commit**

```bash
cd C:/Users/tony_/Documents/claude-tray
git add -A && git commit -m "feat: popup frontend — 3 progress bars with reset timers, dark theme"
```

---

## Task 7: First run and debug

- [ ] **Step 1: Run in dev mode**

```bash
cd C:/Users/tony_/Documents/claude-tray/src-tauri && cargo run
```

Expected: tray icon appears in system tray. Grey rings initially, then colored after first fetch (~5s).

- [ ] **Step 2: Test tooltip**

Hover over tray icon. Expected: `Session: X% | Hebdo: Y% | Sonnet: Z%`

- [ ] **Step 3: Test popup**

Left-click tray icon. Expected: dark popup with 3 progress bars. Click outside to close.

- [ ] **Step 4: Test right-click menu**

Right-click tray icon. Expected: "Refresh" and "Quit" menu items.

- [ ] **Step 5: Fix any issues found**

Debug and fix compilation errors, API response parsing issues, icon rendering.

- [ ] **Step 6: Commit fixes**

```bash
cd C:/Users/tony_/Documents/claude-tray
git add -A && git commit -m "fix: debug and polish first run issues"
```

---

## Task 8: README and push

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Create `claude-tray/README.md`:

```markdown
# Claude Tray

Windows system tray app showing Claude usage limits as 3 concentric circular gauges.

## Features
- 3 colored rings: Session (5h) / Weekly / Sonnet
- Green (< 50%) / Orange (50-80%) / Red (> 80%)
- Tooltip with percentages
- Click for detailed popup with reset timers
- Auto-refresh every 5 minutes

## Requirements
- Claude Code installed (needs `~/.claude/.credentials.json`)
- Windows 10/11

## Build
```bash
cargo install tauri-cli --locked
cd src-tauri && cargo build --release
```

The binary is at `src-tauri/target/release/claude-tray.exe`

## Run
```bash
cargo tauri dev    # development
cargo tauri build  # production build
```
```

- [ ] **Step 2: Final push**

```bash
cd C:/Users/tony_/Documents/claude-tray
git add -A && git commit -m "docs: README with build instructions"
git push -u origin master
```
