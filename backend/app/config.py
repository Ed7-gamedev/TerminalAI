import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

try:
    from dotenv import load_dotenv
    # Carrega o arquivo .env no diretório backend/
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(dotenv_path=os.path.join(backend_dir, ".env"))
except ImportError:
    pass  # dotenv opcional

# ─────────────────────────────────────────────
# Configuração do Agente IA (Gemini)
# ─────────────────────────────────────────────

_GEMINI_KEY = os.getenv("GEMINI_API_KEY")
_GEMINI_MODEL = None
_AI_READY = False

if _GEMINI_KEY and _GEMINI_KEY != "your_gemini_api_key_here":
    try:
        genai.configure(api_key=_GEMINI_KEY)
        _GEMINI_MODEL = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.4,
                max_output_tokens=1024,
            ),
        )
        _AI_READY = True
    except Exception:
        pass

# ─────────────────────────────────────────────
# Configuração do Agente IA (Groq Cloud)
# ─────────────────────────────────────────────

_GROQ_KEY = os.getenv("GROQ_API_KEY")
_GROQ_CLIENT = None

if _GROQ_KEY and _GROQ_KEY != "your_groq_api_key_here" and _GROQ_AVAILABLE:
    try:
        _GROQ_CLIENT = Groq(api_key=_GROQ_KEY)
    except Exception:
        pass

# ─────────────────────────────────────────────
# Lista de Modelos suportados e provedores
# ─────────────────────────────────────────────

SUPPORTED_MODELS = [
    {"key": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "gemini"},
    {"key": "openai/gpt-oss-120b",
        "name": "GPT OSS 120B (Groq)", "provider": "groq"},
    {"key": "openai/gpt-oss-20b",
        "name": "GPT OSS 20B (Groq)", "provider": "groq"},
    {"key": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "provider": "groq"},
    {"key": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B Versatile", "provider": "groq"},
    {"key": "meta-llama/llama-4-scout-17b-16e-instruct",
        "name": "Llama 4 Scout 17B", "provider": "groq"},
    {"key": "qwen/qwen3-32b", "name": "Qwen 3 32B (Groq)", "provider": "groq"},
]
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
