use base64::Engine;
use base64::engine::general_purpose::STANDARD as BASE64;
use screenshots::Screen;
use serde::{Deserialize, Serialize};
use tauri::{Emitter, Manager};

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

#[derive(Deserialize)]
struct OllamaResponse {
    message: OllamaMessage,
}

/// Call Ollama from Rust — bypasses CORS restrictions in the WebView
#[tauri::command]
async fn ollama_chat(messages: Vec<OllamaMessage>) -> Result<String, String> {
    let client = reqwest::Client::new();
    let body = OllamaRequest {
        model: "llama3.2".to_string(),
        stream: false,
        messages,
    };
    let res = client
        .post("http://localhost:11434/api/chat")
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("Ollama unreachable: {e}"))?;
    let data: OllamaResponse = res
        .json()
        .await
        .map_err(|e| format!("Ollama parse error: {e}"))?;
    Ok(data.message.content)
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
        .invoke_handler(tauri::generate_handler![capture_screen, toggle_panel, ollama_chat])
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

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
