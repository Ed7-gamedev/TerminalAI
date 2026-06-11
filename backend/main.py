from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import shutil


try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass  # dotenv opcional

try:
    import google.generativeai as genai
    _GEMINI_KEY = "AIzaSyDyljuJhKHjShmDka6SBr5zvaTH7ea0Tfg"
    if _GEMINI_KEY:
        genai.configure(api_key=_GEMINI_KEY)
        _GEMINI_MODEL = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.4,
                max_output_tokens=1024,
            ),
        )
        _AI_READY = True
    else:
        _GEMINI_MODEL = None
        _AI_READY = False
except ImportError:
    _GEMINI_MODEL = None
    _AI_READY = False

app = FastAPI(title="Terminal-AI Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ─────────────────────────────────────────────
# Configuração dos Shells disponíveis
# ─────────────────────────────────────────────

SHELL_CONFIGS = {
    "cmd": {
        "name": "CMD",
        "icon": "⊞",
        "description": "Windows Command Prompt",
        "executable": "cmd.exe",
        "args_prefix": ["/C"],
        "shell_flag": False,
    },
    "powershell": {
        "name": "PowerShell",
        "icon": "🔷",
        "description": "Windows PowerShell",
        "executable": "powershell.exe",
        "args_prefix": ["-NoProfile", "-NonInteractive", "-Command"],
        "shell_flag": False,
    },
    "gitbash": {
        "name": "Git Bash",
        "icon": "🐧",
        "description": "Git Bash for Windows",
        "executable": None,  # Resolvido dinamicamente
        "args_prefix": ["-c"],
        "shell_flag": False,
    },
    "wsl": {
        "name": "WSL (Kali)",
        "icon": "🐉",
        "description": "Kali Linux via WSL2",
        "executable": "wsl.exe",
        "args_prefix": ["-d", "kali-linux", "-e", "sh", "-c"],
        "shell_flag": False,
    },
    "python": {
        "name": "Python",
        "icon": "🐍",
        "description": "Python interpreter",
        "executable": "python",
        "args_prefix": ["-c"],
        "shell_flag": False,
    },
    "node": {
        "name": "Node.js",
        "icon": "⬡",
        "description": "Node.js runtime",
        "executable": "node",
        "args_prefix": ["-e"],
        "shell_flag": False,
    },
    "ts": {
        "name": "TypeScript",
        "icon": "🟦",
        "description": "TypeScript (ts-node / tsx)",
        "executable": "ts-node",  # Resolvido dinamicamente
        "args_prefix": ["-e"],
        "shell_flag": False,
    },
    "java": {
        "name": "Java",
        "icon": "☕",
        "description": "Java JShell REPL",
        "executable": "jshell",
        "args_prefix": [],
        "shell_flag": False,
    },
    "docker": {
        "name": "Docker",
        "icon": "🐳",
        "description": "Docker Container (Alpine)",
        "executable": "docker",
        "args_prefix": ["run", "--rm", "-i", "alpine", "sh", "-c"],
        "shell_flag": False,
    },
}

# ─────────────────────────────────────────────
# Estado da sessão
# ─────────────────────────────────────────────

current_directory: str = os.getcwd()
current_shell: str = "powershell" if os.name == "nt" else "bash"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def find_in_windows_registry(exe_name: str) -> str | None:
    """Busca o caminho de um executável no Registro do Windows (App Paths)."""
    if os.name != "nt":
        return None

    try:
        import winreg
    except ImportError:
        return None

    # Garante que termina com .exe
    if not exe_name.lower().endswith(".exe"):
        exe_name += ".exe"

    for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        try:
            key_path = fr"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"
            with winreg.OpenKey(root_key, key_path) as key:
                # O valor padrão (nome vazio "") contém o caminho completo do executável
                path, _ = winreg.QueryValueEx(key, "")
                if path:
                    # Expande variáveis de ambiente como %SystemRoot%
                    expanded_path = os.path.expandvars(path)
                    if os.path.isfile(expanded_path):
                        return expanded_path
        except OSError:
            continue
    return None


def resolve_wsl_config():
    """Detecta a distribuição Kali ou outra no WSL e retorna a distro e os argumentos corretos."""
    wsl_exe = shutil.which("wsl.exe")
    if not wsl_exe:
        path = os.path.join(os.environ.get(
            "SystemRoot", "C:\\Windows"), "System32", "wsl.exe")
        if os.path.isfile(path):
            wsl_exe = path
        else:
            return None, []

    # Tenta listar para achar distros com "kali"
    try:
        res = subprocess.run(
            [wsl_exe, "--list", "--quiet"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2,
        )
        output = ""
        for encoding in ["utf-16-le", "utf-16", "utf-8"]:
            try:
                output = res.stdout.decode(encoding)
                if output.strip():
                    break
            except Exception:
                continue

        distros = [line.strip().replace("\x00", "")
                   for line in output.splitlines() if line.strip()]
        for d in distros:
            if "kali" in d.lower():
                return d, ["-d", d, "-e", "sh", "-c"]
    except Exception:
        pass

    # Fallback para a distribuição padrão
    return "Default WSL", ["-e", "sh", "-c"]


def is_docker_active() -> bool:
    """Verifica se o Docker está ativo e o daemon respondendo."""
    exe = resolve_executable("docker")
    if not exe:
        return False
    try:
        res = subprocess.run(
            [exe, "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        return res.returncode == 0
    except Exception:
        return False


def find_bash_executable() -> str | None:
    """Localiza o executável bash no sistema."""
    # 1. Tenta bash no PATH primeiro (Linux/macOS/WSL)
    if shutil.which("bash"):
        return "bash"

    if os.name == "nt":
        # 2. Tenta encontrar bash.exe no Registro do Windows
        bash_reg = find_in_windows_registry("bash.exe")
        if bash_reg:
            return bash_reg

        # 3. Tenta encontrar git.exe no Registro para inferir o caminho do bash.exe
        git_reg = find_in_windows_registry("git.exe")
        if git_reg:
            git_dir = os.path.dirname(os.path.dirname(git_reg))
            for sub in [r"bin\bash.exe", r"usr\bin\bash.exe"]:
                p = os.path.join(git_dir, sub)
                if os.path.isfile(p):
                    return p

    # 4. Locais comuns do Git Bash no Windows (fallback hardcoded)
    git_bash_paths = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\bash.exe"),
    ]
    for path in git_bash_paths:
        if os.path.isfile(path):
            return path

    return None


def resolve_executable(shell_key: str) -> str | None:
    """Retorna o executável para um shell, resolvendo bash dinamicamente."""
    config = SHELL_CONFIGS.get(shell_key)
    if not config:
        return None

    if shell_key == "gitbash":
        return find_bash_executable()

    if shell_key == "wsl":
        wsl_exe = shutil.which("wsl.exe")
        if not wsl_exe:
            path = os.path.join(os.environ.get(
                "SystemRoot", "C:\\Windows"), "System32", "wsl.exe")
            if os.path.isfile(path):
                wsl_exe = path
        return wsl_exe

    if shell_key == "ts":
        # Tenta achar ts-node local/global primeiro, ou tsx
        for name in ["ts-node", "ts-node.cmd", "tsx", "tsx.cmd"]:
            if shutil.which(name):
                return name
        # Se não achar, mas tiver node/npx, podemos usar npx
        npx_exe = "npx.cmd" if os.name == "nt" else "npx"
        if shutil.which(npx_exe):
            return npx_exe
        return None

    if shell_key == "java":
        jshell = shutil.which("jshell")
        if jshell:
            return jshell
        # Tenta inferir a partir do java.exe no Registro
        java_reg = find_in_windows_registry("java.exe")
        if java_reg:
            jshell_path = os.path.join(os.path.dirname(java_reg), "jshell.exe")
            if os.path.isfile(jshell_path):
                return jshell_path
        return None

    if shell_key == "docker":
        docker_exe = shutil.which("docker")
        if not docker_exe and os.name == "nt":
            possible_paths = [
                r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
                r"C:\Program Files\Docker\Docker\resources\bin\docker",
            ]
            for p in possible_paths:
                if os.path.isfile(p):
                    return p
        return docker_exe

    exe = config["executable"]
    if not exe:
        return None

    # 1. Tenta pelo PATH comum
    path = shutil.which(exe)
    if path:
        return path

    # 2. Tenta pelo Registro do Windows
    if os.name == "nt":
        reg_path = find_in_windows_registry(exe)
        if reg_path:
            return reg_path

    return None


def is_shell_available(shell_key: str) -> bool:
    if shell_key == "docker":
        return is_docker_active()
    if shell_key == "wsl":
        return resolve_executable("wsl") is not None
    return resolve_executable(shell_key) is not None


def get_shell_list():
    return [
        {
            "key": key,
            "name": cfg["name"],
            "icon": cfg["icon"],
            "description": cfg["description"],
            "available": is_shell_available(key),
        }
        for key, cfg in SHELL_CONFIGS.items()
    ]


def build_response(output: str = "", error: str = "") -> dict:
    """Monta a resposta padrão com cwd e shell atual."""
    return {
        "output": output,
        "error": error,
        "cwd": current_directory,
        "shell": current_shell,
        "shell_name": SHELL_CONFIGS[current_shell]["name"],
        "shell_icon": SHELL_CONFIGS[current_shell]["icon"],
    }


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────

class CommandRequest(BaseModel):
    cmd: str


class ShellRequest(BaseModel):
    shell: str


class AiChatRequest(BaseModel):
    message: str
    shell: str = "powershell"
    cwd: str = "~"
    last_output: str = ""          # últimas linhas do output do terminal
    # histórico de mensagens anteriores (alternado user/ai)
    history: list[str] = []


class AiChatResponse(BaseModel):
    reply: str
    commands: list[str] = []       # comandos sugeridos extraídos do markdown
    error: str = ""


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Terminal-AI API v0.2.0"}


@app.get("/get-cwd")
def get_cwd():
    return build_response()


@app.get("/get-shell")
def get_shell():
    return {
        "shell": current_shell,
        "shell_name": SHELL_CONFIGS[current_shell]["name"],
        "shell_icon": SHELL_CONFIGS[current_shell]["icon"],
        "shells": get_shell_list(),
    }


@app.post("/set-shell")
def set_shell(request: ShellRequest):
    global current_shell

    key = request.shell.lower().strip()

    # Aliases mapping para facilitar a digitação do usuário
    aliases = {
        "linux": "wsl",
        "wsl": "wsl",
        "kali": "wsl",
        "kali linux": "wsl",
        "git bash": "gitbash",
        "gitbash": "gitbash",
        "bash": "gitbash",
        "sh": "gitbash",
        "python terminal": "python",
        "python": "python",
        "py": "python",
        "node js terminal": "node",
        "node js": "node",
        "nodejs": "node",
        "node": "node",
        "ts": "ts",
        "typescript": "ts",
        "java": "java",
        "jshell": "java",
        "docker": "docker",
        "cmd": "cmd",
        "powershell": "powershell",
        "ps": "powershell",
    }

    key = aliases.get(key, key)

    if key not in SHELL_CONFIGS:
        available = ", ".join(SHELL_CONFIGS.keys())
        return {
            "success": False,
            "error": f"Shell '{request.shell}' desconhecido. Opções: {available} (aliases suportados como 'linux', 'git bash', etc.)",
        }

    if not is_shell_available(key):
        cfg = SHELL_CONFIGS[key]
        return {
            "success": False,
            "error": f"{cfg['name']} não encontrado ou não está ativo no sistema.",
        }

    current_shell = key
    cfg = SHELL_CONFIGS[key]
    return {
        "success": True,
        "shell": key,
        "shell_name": cfg["name"],
        "shell_icon": cfg["icon"],
        "message": f"Alterado para {cfg['icon']} {cfg['name']}",
    }


@app.post("/execute")
def execute_command(request: CommandRequest):
    global current_directory, current_shell

    cmd = request.cmd.strip()
    if not cmd:
        return build_response()

    # ── Comando especial: trocar de shell ──────────────────────
    # Suporta: `shell powershell`, `use bash`, `switch node`, etc.
    lower = cmd.lower()
    shell_trigger_prefixes = ("shell ", "use ", "switch ")
    for prefix in shell_trigger_prefixes:
        if lower.startswith(prefix):
            shell_key = cmd[len(prefix):].strip().lower()
            result = set_shell(ShellRequest(shell=shell_key))
            if result.get("success"):
                return build_response(
                    output=f"{result['shell_icon']} Shell alterado para {result['shell_name']}\r\n"
                    f"Digite seus comandos em {result['shell_name']}."
                )
            else:
                return build_response(error=result.get("error", "Erro desconhecido"))

    # ── Comando especial: listar shells ────────────────────────
    if lower in ("shell list", "shell --list", "shells"):
        lines = ["Shells disponíveis:\r\n"]
        for s in get_shell_list():
            status = "✓" if s["available"] else "✗ (não disponível)"
            current_marker = " ← atual" if s["key"] == current_shell else ""
            lines.append(
                f"  {s['icon']}  {s['key']:<12} {s['name']:<14} {status}{current_marker}\r\n")
        lines.append("\r\nUso: shell <nome>  (ex: shell powershell)\r\n")
        return build_response(output="".join(lines))

    # ── Interceptar cd (funciona em todos os shells) ───────────
    if lower == "cd" or lower.startswith("cd ") or lower.startswith("cd\t"):
        try:
            parts = cmd.split(None, 1)
            new_path = parts[1].strip() if len(parts) > 1 else "~"

            # Remove aspas se houver e expande o caractere home ~
            new_path = new_path.strip('"').strip("'")
            new_path = os.path.expanduser(new_path)

            if os.path.isabs(new_path):
                target_path = new_path
            else:
                target_path = os.path.join(current_directory, new_path)

            os.chdir(target_path)
            current_directory = os.getcwd()
            return build_response()
        except Exception as e:
            return build_response(error=str(e))

    # ── Executar via shell selecionado ─────────────────────────
    return _run_with_shell(cmd)


def _run_with_shell(cmd: str) -> dict:
    """Executa o comando usando o shell atualmente selecionado."""
    global current_shell, current_directory

    exe = resolve_executable(current_shell)
    if not exe:
        cfg = SHELL_CONFIGS[current_shell]
        return build_response(
            error=f"{cfg['name']} não encontrado. Use 'shell list' para ver opções disponíveis."
        )

    cfg = SHELL_CONFIGS[current_shell]

    # Resolve os argumentos corretos para cada tipo de shell
    args_prefix = cfg["args_prefix"]
    input_data = None

    if current_shell == "wsl":
        # Resolve WSL Kali distro dinamicamente
        _, wsl_args = resolve_wsl_config()
        args_prefix = wsl_args

    if current_shell == "java":
        # JShell funciona melhor se passarmos comandos via stdin
        full_cmd = [exe, "-q"]
        input_data = cmd + "\n/exit\n"
    elif current_shell == "ts":
        # ts-node executa mais seguro via stdin para evitar problemas de quotes/escaping
        if os.path.basename(exe).lower().startswith("npx"):
            full_cmd = [exe, "-y", "ts-node"]
        else:
            full_cmd = [exe]
        input_data = cmd + "\n"
    else:
        full_cmd = [exe] + args_prefix + [cmd]

    try:
        process = subprocess.Popen(
            full_cmd,
            shell=False,           # Mais seguro: sem shell=True
            stdin=subprocess.PIPE,  # Habilita stdin
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_directory,
            encoding="utf-8",
            errors="replace",
        )

        try:
            stdout, stderr = process.communicate(input=input_data, timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return build_response(
                output=stdout,
                error="Comando excedeu o tempo limite de 30 segundos.",
            )

        return build_response(output=stdout, error=stderr)

    except Exception as e:
        return build_response(error=str(e))


# ─────────────────────────────────────────────
# Endpoints — Agente IA
# ─────────────────────────────────────────────

@app.get("/ai/status")
def ai_status():
    """Verifica se a integração com IA está disponível."""
    return {
        "available": _AI_READY,
        "model": "gemini-2.5-flash" if _AI_READY else None,
        "reason": None if _AI_READY else (
            "API key não configurada. Edita backend/.env e reinicia."
            if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here"
            else "Instala: pip install google-generativeai python-dotenv"
        ),
    }


@app.post("/ai/chat")
async def ai_chat(request: AiChatRequest):
    """
    Envia uma mensagem ao agente IA com contexto do terminal.
    Retorna resposta em texto + lista de comandos sugeridos extraídos.
    """
    import re

    if not _AI_READY or _GEMINI_MODEL is None:
        return AiChatResponse(
            reply="⚠️ Agente IA não configurado.\n\nEdita `backend/.env` com a tua GEMINI_API_KEY e reinicia o backend.\n\nObtém a chave em: https://aistudio.google.com/app/apikey",
            commands=[],
            error="AI_NOT_CONFIGURED",
        )

    # ── Monta o system prompt com contexto do terminal ──────────
    shell_name = SHELL_CONFIGS.get(
        request.shell, {}).get("name", request.shell)
    last_out_section = ""
    if request.last_output.strip():
        # Trunca para não explodir o contexto
        truncated = request.last_output[-1500:].strip()
        last_out_section = f"\n\nÚltimo output do terminal:\n```\n{truncated}\n```"

    system_prompt = f"""Você é um assistente de terminal especialista e conciso.
Contexto atual:
- Shell: {shell_name}
- Diretório: {request.cwd}{last_out_section}

Regras:
1. Responda SEMPRE em português do Brasil.
2. Seja direto e prático. Priorize exemplos de comandos.
3. Quando sugerir comandos, coloque-os em blocos de código markdown: ```bash ou ```powershell ou ```python etc.
4. Se o utilizador pedir para executar algo, sugira o comando exato no bloco de código.
5. Não repita o contexto de volta ao utilizador.
6. Máximo 300 palavras por resposta."""

    # ── Monta o histórico de conversa ───────────────────────────
    try:
        history_parts = []
        # request.history é uma lista alternada [user_msg, ai_reply, user_msg, ai_reply, ...]
        for i, msg in enumerate(request.history[-10:]):  # últimas 10 mensagens
            role = "user" if i % 2 == 0 else "model"
            history_parts.append({"role": role, "parts": [msg]})

        chat = _GEMINI_MODEL.start_chat(history=history_parts)
        # Injeta o system prompt no primeiro turno se não houver histórico
        if not history_parts:
            user_msg = f"{system_prompt}\n\n---\n\nUtilizador: {request.message}"
        else:
            user_msg = request.message

        response = await chat.send_message_async(user_msg)
        reply_text = response.text

    except Exception as e:
        return AiChatResponse(
            reply="",
            commands=[],
            error=f"Erro ao contactar a IA: {str(e)}",
        )

    # ── Extrai comandos dos blocos de código markdown ───────────
    # Captura conteúdo de ```lang ... ``` onde lang é shell-like
    code_block_pattern = re.compile(
        r"```(?:bash|sh|powershell|ps1|cmd|python|py|javascript|js|typescript|ts|node)?\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    commands = []
    for match in code_block_pattern.finditer(reply_text):
        block = match.group(1).strip()
        # Separa linhas que são comandos individuais (ignora comentários)
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(line)

    return AiChatResponse(
        reply=reply_text,
        commands=commands,
    )


class SyncSessionRequest(BaseModel):
    shell: str
    cwd: str


@app.post("/sync-session")
def sync_session(request: SyncSessionRequest):
    global current_shell, current_directory

    key = request.shell.lower().strip()
    aliases = {
        "linux": "wsl",
        "wsl": "wsl",
        "kali": "wsl",
        "kali linux": "wsl",
        "git bash": "gitbash",
        "gitbash": "gitbash",
        "bash": "gitbash",
        "sh": "gitbash",
        "python": "python",
        "py": "python",
        "node": "node",
        "nodejs": "node",
        "ts": "ts",
        "typescript": "ts",
        "java": "java",
        "jshell": "java",
        "docker": "docker",
        "cmd": "cmd",
        "powershell": "powershell",
        "ps": "powershell",
    }
    key = aliases.get(key, key)
    if key in SHELL_CONFIGS and is_shell_available(key):
        current_shell = key

    target_path = os.path.expanduser(request.cwd)
    if not os.path.isabs(target_path):
        target_path = os.path.abspath(target_path)

    if os.path.isdir(target_path):
        try:
            os.chdir(target_path)
            current_directory = os.getcwd()
        except Exception:
            pass

    return build_response()
