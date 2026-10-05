#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use tauri::Manager;

fn core_process(app: &tauri::AppHandle, mode: &str) -> Command {
    let name = if cfg!(windows) {
        "lector-core.exe"
    } else {
        "lector-core"
    };
    let resources = app
        .path()
        .resource_dir()
        .unwrap_or_default()
        .join("core")
        .join(name);
    let portable = std::env::current_exe()
        .unwrap_or_default()
        .parent()
        .unwrap_or(std::path::Path::new("."))
        .join("core")
        .join(name);
    let sidecar = if resources.is_file() {
        resources
    } else {
        portable
    };
    let mut command;
    if !cfg!(debug_assertions) {
        command = Command::new(sidecar);
    } else {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
        let python = root.join(if cfg!(windows) {
            ".venv/Scripts/python.exe"
        } else {
            ".venv/bin/python"
        });
        command = Command::new(python);
        command.arg("-m").arg("reader_core");
        command.current_dir(root);
    }
    command.arg(mode);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    command
}

#[tauri::command]
async fn core_request(
    app: tauri::AppHandle,
    message: serde_json::Value,
) -> Result<serde_json::Value, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let data = serde_json::to_vec(&message).map_err(|_| "Mensaje inválido.")?;
        if data.len() > 900_000 {
            return Err("Mensaje demasiado grande.".to_string());
        }
        let mut child = core_process(&app, "request")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|_| "No se encuentra el motor incluido. Reinstala Lector Local.")?;
        child
            .stdin
            .take()
            .ok_or("No se pudo abrir el canal local.")?
            .write_all(&data)
            .map_err(|_| "El canal local se cerró.")?;
        let output = child
            .wait_with_output()
            .map_err(|_| "El core no respondió.")?;
        serde_json::from_slice(&output.stdout)
            .map_err(|_| "Respuesta del core inválida.".to_string())
    })
    .await
    .map_err(|_| "Falló la comunicación local.".to_string())?
}

#[tauri::command]
async fn install_model(app: tauri::AppHandle, engine: String) -> Result<(), String> {
    if engine != "kokoro" && engine != "piper" {
        return Err("Motor desconocido.".into());
    }
    tauri::async_runtime::spawn_blocking(move || {
        let output = core_process(&app, "install-model")
            .arg("--engine")
            .arg(engine)
            .arg("--accept")
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .map_err(|_| "No se pudo iniciar el instalador del modelo.")?;
        if output.success() {
            Ok(())
        } else {
            Err(
                "La descarga o verificación falló. Comprueba tu conexión y vuelve a intentarlo."
                    .to_string(),
            )
        }
    })
    .await
    .map_err(|_| "Falló la instalación del modelo.".to_string())?
}

#[tauri::command]
async fn register_host(
    app: tauri::AppHandle,
    chromium_id: String,
    firefox_only: bool,
) -> Result<(), String> {
    if !firefox_only
        && (chromium_id.len() != 32
            || !chromium_id
                .bytes()
                .all(|value| (b'a'..=b'p').contains(&value)))
    {
        return Err(
            "El ID debe contener 32 letras de a a p. Cópialo desde la página de extensiones."
                .to_string(),
        );
    }
    tauri::async_runtime::spawn_blocking(move || {
        let mut command = core_process(&app, "install-host");
        if firefox_only { command.arg("--browser").arg("firefox"); }
        else { command.arg("--chromium-id").arg(chromium_id); }
        let status = command.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null()).status().map_err(|_| "No se pudo iniciar el registro del host.")?;
        if status.success() { Ok(()) } else { Err("No se pudo registrar el host. Comprueba que el navegador tenga un perfil y que no exista un registro anterior distinto.".to_string()) }
    }).await.map_err(|_| "Falló el registro del host.".to_string())?
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let handle = app.handle().clone();
            tauri::async_runtime::spawn_blocking(move || {
                let _ = core_process(&handle, "install-host")
                    .arg("--channel")
                    .arg("production")
                    .stdin(Stdio::null())
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .status();
            });
            Ok(())
        })
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            core_request,
            install_model,
            register_host
        ])
        .run(tauri::generate_context!())
        .expect("No se pudo iniciar Lector Local");
}
