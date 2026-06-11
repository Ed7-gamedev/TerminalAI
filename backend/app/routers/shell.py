import os
import subprocess
from fastapi import APIRouter
from app import state, config, models, utils

router = APIRouter()

@router.get("/get-cwd")
def get_cwd():
    return utils.build_response()


@router.get("/get-shell")
def get_shell():
    return {
        "shell": state.current_shell,
        "shell_name": config.SHELL_CONFIGS[state.current_shell]["name"],
        "shell_icon": config.SHELL_CONFIGS[state.current_shell]["icon"],
        "shells": utils.get_shell_list(),
    }


@router.post("/set-shell")
def set_shell(request: models.ShellRequest):
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

    if key not in config.SHELL_CONFIGS:
        available = ", ".join(config.SHELL_CONFIGS.keys())
        return {
            "success": False,
            "error": f"Shell '{request.shell}' desconhecido. Opções: {available} (aliases suportados como 'linux', 'git bash', etc.)",
        }

    if not utils.is_shell_available(key):
        cfg = config.SHELL_CONFIGS[key]
        return {
            "success": False,
            "error": f"{cfg['name']} não encontrado ou não está ativo no sistema.",
        }

    state.current_shell = key
    cfg = config.SHELL_CONFIGS[key]
    return {
        "success": True,
        "shell": key,
        "shell_name": cfg["name"],
        "shell_icon": cfg["icon"],
        "message": f"Alterado para {cfg['icon']} {cfg['name']}",
    }


@router.post("/execute")
def execute_command(request: models.CommandRequest):
    cmd = request.cmd.strip()
    if not cmd:
        return utils.build_response()

    # ── Comando especial: trocar de shell ──────────────────────
    lower = cmd.lower()
    shell_trigger_prefixes = ("shell ", "use ", "switch ")
    for prefix in shell_trigger_prefixes:
        if lower.startswith(prefix):
            shell_key = cmd[len(prefix):].strip().lower()
            result = set_shell(models.ShellRequest(shell=shell_key))
            if result.get("success"):
                return utils.build_response(
                    output=f"{result['shell_icon']} Shell alterado para {result['shell_name']}\r\n"
                    f"Digite seus comandos em {result['shell_name']}."
                )
            else:
                return utils.build_response(error=result.get("error", "Erro desconhecido"))

    # ── Comando especial: listar shells ────────────────────────
    if lower in ("shell list", "shell --list", "shells"):
        lines = ["Shells disponíveis:\r\n"]
        for s in utils.get_shell_list():
            status = "✓" if s["available"] else "✗ (não disponível)"
            current_marker = " ← atual" if s["key"] == state.current_shell else ""
            lines.append(
                f"  {s['icon']}  {s['key']:<12} {s['name']:<14} {status}{current_marker}\r\n")
        lines.append("\r\nUso: shell <nome>  (ex: shell powershell)\r\n")
        return utils.build_response(output="".join(lines))

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
                target_path = os.path.join(state.current_directory, new_path)

            os.chdir(target_path)
            state.current_directory = os.getcwd()
            return utils.build_response()
        except Exception as e:
            return utils.build_response(error=str(e))

    # ── Executar via shell selecionado ─────────────────────────
    return _run_with_shell(cmd)


def _run_with_shell(cmd: str) -> dict:
    """Executa o comando usando o shell atualmente selecionado."""
    exe = utils.resolve_executable(state.current_shell)
    if not exe:
        cfg = config.SHELL_CONFIGS[state.current_shell]
        return utils.build_response(
            error=f"{cfg['name']} não encontrado. Use 'shell list' para ver opções disponíveis."
        )

    cfg = config.SHELL_CONFIGS[state.current_shell]

    # Resolve os argumentos corretos para cada tipo de shell
    args_prefix = cfg["args_prefix"]
    input_data = None

    if state.current_shell == "wsl":
        # Resolve WSL Kali distro dinamicamente
        _, wsl_args = utils.resolve_wsl_config()
        args_prefix = wsl_args

    if state.current_shell == "java":
        # JShell funciona melhor se passarmos comandos via stdin
        full_cmd = [exe, "-q"]
        input_data = cmd + "\n/exit\n"
    elif state.current_shell == "ts":
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
            cwd=state.current_directory,
            encoding="utf-8",
            errors="replace",
        )

        try:
            stdout, stderr = process.communicate(input=input_data, timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return utils.build_response(
                output=stdout,
                error="Comando excedeu o tempo limite de 30 segundos.",
            )

        return utils.build_response(output=stdout, error=stderr)

    except Exception as e:
        return utils.build_response(error=str(e))


@router.post("/sync-session")
def sync_session(request: models.SyncSessionRequest):
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
    if key in config.SHELL_CONFIGS and utils.is_shell_available(key):
        state.current_shell = key

    target_path = os.path.expanduser(request.cwd)
    if not os.path.isabs(target_path):
        target_path = os.path.abspath(target_path)

    if os.path.isdir(target_path):
        try:
            os.chdir(target_path)
            state.current_directory = os.getcwd()
        except Exception:
            pass

    return utils.build_response()
