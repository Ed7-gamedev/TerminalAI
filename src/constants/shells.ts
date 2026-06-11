// ─────────────────────────────────────────────
// Constantes de Shells — Terminal-AI
// ─────────────────────────────────────────────

export const SHELL_ICONS: Record<string, string> = {
  cmd:        "⊞",
  powershell: "🔷",
  gitbash:    "🐧",
  wsl:        "🐉",
  python:     "🐍",
  node:       "⬡",
  ts:         "🟦",
  java:       "☕",
  docker:     "🐳",
};

export const SHELL_COLORS: Record<string, string> = {
  cmd:        "#cccccc",
  powershell: "#5bc4f5",
  gitbash:    "#f05032",
  wsl:        "#7f52ff",
  python:     "#f7c948",
  node:       "#6cc24a",
  ts:         "#3178c6",
  java:       "#f89820",
  docker:     "#0db7ed",
};

export const SHELL_NAMES: Record<string, string> = {
  cmd:        "CMD",
  powershell: "PowerShell",
  gitbash:    "Git Bash",
  wsl:        "WSL (Kali)",
  python:     "Python",
  node:       "Node.js",
  ts:         "TypeScript",
  java:       "Java",
  docker:     "Docker",
};
