// ─────────────────────────────────────────────
// Tipos partilhados — Terminal-AI
// ─────────────────────────────────────────────

export type BackendStatus = "connecting" | "ready" | "error";

export interface ShellInfo {
  key: string;
  name: string;
  icon: string;
}

export interface ShellEntry extends ShellInfo {
  description: string;
  available: boolean;
}

export interface ExecuteResponse {
  output: string;
  error: string;
  cwd: string;
  shell: string;
  shell_name: string;
  shell_icon: string;
}

export interface SetShellResponse {
  success: boolean;
  shell: string;
  shell_name: string;
  shell_icon: string;
  message?: string;
  error?: string;
}

export interface GetShellResponse {
  shell: string;
  shell_name: string;
  shell_icon: string;
  shells: ShellEntry[];
}

export interface GetCwdResponse {
  cwd: string;
}

// ── Chat / IA ──────────────────────────────────

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  commands: string[];   // comandos sugeríveis extraídos da resposta
  timestamp: Date;
}

export interface AiContext {
  shell: string;
  cwd: string;
  last_output: string;
  history: string[];   // alternado: [user, ai, user, ai, ...]
}

export interface AiChatResponse {
  reply: string;
  commands: string[];
  error: string;
}

export interface AiStatusResponse {
  available: boolean;
  model: string | null;
  reason: string | null;
}

