use base64::Engine;
use base64::engine::general_purpose::STANDARD as BASE64;
use futures_util::StreamExt;
use screenshots::Screen;
use serde::{Deserialize, Serialize};
use tauri::{Emitter, Manager};
use std::sync::Mutex;

#[derive(Serialize, Deserialize, Clone)]
pub struct OllamaMessage {
    pub role: String,
    pub content: String,
}

#[derive(Serialize)]
struct OllamaRequest {
    model: String,
    stream: bool,
    messages: Vec<OllamaMessage>,
}


/// Load conversation history and journal summary from disk
#[tauri::command]
fn load_history() -> String {
    let base = std::path::PathBuf::from("C:\\niam-bay\\docs");

    // Read last ~3000 chars of journal
    let journal = std::fs::read_to_string(base.join("journal.md"))
        .unwrap_or_default();
    let journal_tail = if journal.len() > 3000 {
        &journal[journal.len() - 3000..]
    } else {
        &journal
    };

    // Read last conversation file if it exists
    let conv_dir = base.join("conversations");
    let last_conv = std::fs::read_dir(&conv_dir)
        .ok()
        .and_then(|mut entries| {
            let mut files: Vec<_> = entries
                .filter_map(|e| e.ok())
                .filter(|e| e.path().extension().map(|x| x == "md").unwrap_or(false))
                .collect();
            files.sort_by_key(|e| e.file_name());
            files.last().map(|e| std::fs::read_to_string(e.path()).unwrap_or_default())
        })
        .unwrap_or_default();

    format!("=== JOURNAL (extrait) ===\n{journal_tail}\n\n=== DERNIÈRE CONVERSATION ===\n{last_conv}")
}

/// Save current conversation to disk
#[tauri::command]
fn save_conversation(content: String) -> Result<(), String> {
    let conv_dir = std::path::PathBuf::from("C:\\niam-bay\\docs\\conversations");
    std::fs::create_dir_all(&conv_dir).map_err(|e| e.to_string())?;

    let now = chrono::Utc::now();
    let filename = now.format("%Y-%m-%d_%H-%M.md").to_string();
    std::fs::write(conv_dir.join(filename), content).map_err(|e| e.to_string())
}

/// Stream Ollama response token by token via Tauri events
#[allow(unused_mut)]
#[tauri::command]
async fn ollama_chat(app: tauri::AppHandle, messages: Vec<OllamaMessage>) -> Result<String, String> {
    let client = reqwest::Client::new();
    let body = OllamaRequest {
        model: "niambay2".to_string(),
        stream: true,
        messages,
    };
    let res = client
        .post("http://localhost:11434/api/chat")
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("Ollama unreachable: {e}"))?;

    let mut full = String::new();
    let mut stream = res.bytes_stream();

    while let Some(chunk) = stream.next().await {
        let bytes = chunk.map_err(|e| format!("Stream error: {e}"))?;
        if let Ok(text) = std::str::from_utf8(&bytes) {
            for line in text.lines() {
                if line.is_empty() { continue; }
                if let Ok(val) = serde_json::from_str::<serde_json::Value>(line) {
                    if let Some(token) = val["message"]["content"].as_str() {
                        full.push_str(token);
                        let _ = app.emit("ollama-token", token);
                    }
                }
            }
        }
    }

    let _ = app.emit("ollama-done", &full);
    Ok(full)
}

/// Capture the primary screen and return it as a base64-encoded PNG
#[tauri::command]
fn capture_screen() -> Result<String, String> {
    let screens = Screen::all().map_err(|e| format!("Cannot list screens: {e}"))?;
    let screen = screens.into_iter().next().ok_or("No screen found")?;
    let image = screen.capture().map_err(|e| format!("Capture failed: {e}"))?;
    let mut png_bytes: Vec<u8> = Vec::new();
    image::DynamicImage::ImageRgba8(image)
        .write_to(&mut std::io::Cursor::new(&mut png_bytes), image::ImageFormat::Png)
        .map_err(|e| format!("PNG encode failed: {e}"))?;
    Ok(BASE64.encode(&png_bytes))
}

/// Call Martin API via SSH tunnel
fn ssh_martin(path: &str) -> Result<String, String> {
    let key = "C:\\Users\\tony_\\.ssh\\martin_vm.key";
    let cmd = format!("curl -s http://localhost:8081{path}");
    let out = std::process::Command::new("ssh")
        .args([
            "-i", key,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=5",
            "-o", "BatchMode=yes",
            "ubuntu@141.253.108.141",
            &cmd,
        ])
        .output()
        .map_err(|e| format!("SSH spawn error: {e}"))?;
    if out.status.success() {
        String::from_utf8(out.stdout).map_err(|e| e.to_string())
    } else {
        Err(String::from_utf8_lossy(&out.stderr).to_string())
    }
}

/// Return Martin grid status as JSON string
#[tauri::command]
fn check_martin() -> Result<String, String> {
    ssh_martin("/api/grid/status/PF_ETHUSD")
}

/// Toggle the panel window visibility
#[tauri::command]
fn toggle_panel(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(panel) = app.get_webview_window("panel") {
        if panel.is_visible().map_err(|e: tauri::Error| e.to_string())? {
            panel.hide().map_err(|e: tauri::Error| e.to_string())?;
        } else {
            panel.show().map_err(|e: tauri::Error| e.to_string())?;
            panel.set_focus().map_err(|e: tauri::Error| e.to_string())?;
        }
    }
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .invoke_handler(tauri::generate_handler![capture_screen, toggle_panel, ollama_chat, load_history, save_conversation, check_martin])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // Register global shortcut: Ctrl+Shift+Space to toggle panel
            use tauri_plugin_global_shortcut::GlobalShortcutExt;
            let app_handle = app.handle().clone();
            app.global_shortcut().on_shortcut("ctrl+shift+space", move |_app, _shortcut, event| {
                if event.state == tauri_plugin_global_shortcut::ShortcutState::Pressed {
                    let _ = app_handle.emit("toggle-panel", ());
                    let _ = toggle_panel(app_handle.clone());
                }
            }).map_err(|e| format!("Failed to register shortcut: {e}"))?;

            // Background Martin grid monitor — polls every 60s
            let app_handle = app.handle().clone();
            let last_trips = Mutex::new(0u64);
            tauri::async_runtime::spawn(async move {
                loop {
                    tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
                    if let Ok(json) = ssh_martin("/api/grid/status/PF_ETHUSD") {
                        if let Ok(val) = serde_json::from_str::<serde_json::Value>(&json) {
                            let trips = val["completedRoundTrips"].as_u64().unwrap_or(0);
                            let profit = val["totalProfit"].as_f64().unwrap_or(0.0);
                            let center = val["centerPrice"].as_f64().unwrap_or(0.0);
                            let _ = app_handle.emit("martin-update", serde_json::json!({
                                "trips": trips, "profit": profit, "center": center,
                                "active": val["active"].as_bool().unwrap_or(false)
                            }));
                            let mut last = last_trips.lock().unwrap();
                            if trips > *last && *last > 0 {
                                let new_trips = trips - *last;
                                let _ = app_handle.emit("martin-roundtrip", serde_json::json!({
                                    "new_trips": new_trips, "total_trips": trips, "profit": profit
                                }));
                            }
                            *last = trips;
                        }
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
