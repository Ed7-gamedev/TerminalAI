use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;

/// Guarda o processo do backend Python para encerrá-lo ao fechar o app.
struct BackendProcess(Mutex<Option<Child>>);

/// Resolve o diretório do backend relativo ao Cargo.toml em dev,
/// ou ao executável em produção.
fn resolve_backend_dir() -> PathBuf {
    if cfg!(debug_assertions) {
        // Em desenvolvimento, o manifest fica em src-tauri/
        // então subimos um nível para a raiz do projeto
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .expect("Falha ao resolver diretório raiz do projeto")
            .join("backend")
    } else {
        // Em produção, o executável fica em resources/
        std::env::current_exe()
            .expect("Falha ao obter caminho do executável")
            .parent()
            .expect("Falha ao obter diretório do executável")
            .join("backend")
    }
}

/// Tenta iniciar o backend Python (uvicorn) e retorna o Child process.
fn start_python_backend(backend_dir: &PathBuf) -> Option<Child> {
    // Tenta `python` primeiro; fallback para `python3` (Linux/macOS)
    let python_cmds = if cfg!(target_os = "windows") {
        vec!["python"]
    } else {
        vec!["python3", "python"]
    };

    for python_cmd in python_cmds {
        let result = Command::new(python_cmd)
            .args([
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ])
            .current_dir(backend_dir)
            // Redireciona para herdar os logs no terminal de debug
            .stdout(std::process::Stdio::inherit())
            .stderr(std::process::Stdio::inherit())
            .spawn();

        match result {
            Ok(child) => {
                eprintln!("[terminal-ai] Backend Python iniciado (PID: {})", child.id());
                return Some(child);
            }
            Err(e) => {
                eprintln!(
                    "[terminal-ai] Falha ao iniciar backend com '{}': {}",
                    python_cmd, e
                );
            }
        }
    }

    eprintln!("[terminal-ai] AVISO: Backend Python não pôde ser iniciado. Verifique se Python está no PATH.");
    None
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        // Gerencia o processo do backend como estado global do app
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let backend_dir = resolve_backend_dir();
            eprintln!("[terminal-ai] Diretório do backend: {:?}", backend_dir);

            if !backend_dir.exists() {
                eprintln!(
                    "[terminal-ai] AVISO: Diretório do backend não encontrado em {:?}",
                    backend_dir
                );
                return Ok(());
            }

            let child = start_python_backend(&backend_dir);

            // Armazena o processo no estado gerenciado
            let state = app.state::<BackendProcess>();
            *state.0.lock().unwrap() = child;

            // Aguarda um momento para o servidor subir antes da UI conectar
            std::thread::sleep(Duration::from_millis(1500));

            Ok(())
        })
        .on_window_event(|window, event| {
            // Encerra o processo Python ao fechar a janela principal
            if let tauri::WindowEvent::Destroyed = event {
                // Extrai o Child em bloco isolado para que `state` (borrow de `window`)
                // seja dropado antes de usarmos `child`.
                let child_opt = {
                    let state = window.state::<BackendProcess>();
                    state.0.lock().ok().and_then(|mut guard| guard.take())
                };

                if let Some(mut child) = child_opt {
                    eprintln!(
                        "[terminal-ai] Encerrando backend Python (PID: {})...",
                        child.id()
                    );
                    let _ = child.kill();
                    let _ = child.wait();
                    eprintln!("[terminal-ai] Backend encerrado.");
                }
            }
        })
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("Erro ao iniciar aplicação Tauri");
}
