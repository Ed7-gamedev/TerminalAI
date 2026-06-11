import os
import shutil
import subprocess
from app import config, state

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
    config_dict = config.SHELL_CONFIGS.get(shell_key)
    if not config_dict:
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

    exe = config_dict["executable"]
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
        for key, cfg in config.SHELL_CONFIGS.items()
    ]


def build_response(output: str = "", error: str = "") -> dict:
    """Monta a resposta padrão com cwd e shell atual."""
    return {
        "output": output,
        "error": error,
        "cwd": state.current_directory,
        "shell": state.current_shell,
        "shell_name": config.SHELL_CONFIGS[state.current_shell]["name"],
        "shell_icon": config.SHELL_CONFIGS[state.current_shell]["icon"],
    }
