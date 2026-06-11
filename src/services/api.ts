// ─────────────────────────────────────────────
// Camada de serviço — API do backend
// Terminal-AI
// ─────────────────────────────────────────────

import type {
  ExecuteResponse,
  GetCwdResponse,
  GetShellResponse,
  SetShellResponse,
  AiChatResponse,
  AiStatusResponse,
  AiContext,
  RiskResponse,
  ModelEntry,
} from "../types";

export const API_BASE = "http://127.0.0.1:8000";

const JSON_HEADERS = { "Content-Type": "application/json" };

// ── Health / Conexão ──────────────────────────

/**
 * Aguarda o backend ficar disponível com retry automático.
 */
export async function waitForBackend(
  maxAttempts = 10,
  intervalMs = 600
): Promise<boolean> {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(`${API_BASE}/health`, {
        signal: AbortSignal.timeout(1000),
      });
      if (res.ok) return true;
    } catch {
      /* ainda não pronto */
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}

// ── Shell ─────────────────────────────────────

/**
 * Busca o shell atual e a lista completa de shells disponíveis.
 */
export async function getShell(): Promise<GetShellResponse> {
  const res = await fetch(`${API_BASE}/get-shell`);
  if (!res.ok) throw new Error(`GET /get-shell: ${res.status}`);
  return res.json();
}

/**
 * Troca o shell ativo no backend.
 */
export async function setShell(shell: string): Promise<SetShellResponse> {
  const res = await fetch(`${API_BASE}/set-shell`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ shell }),
  });
  if (!res.ok) throw new Error(`POST /set-shell: ${res.status}`);
  return res.json();
}

// ── Diretório ─────────────────────────────────

/**
 * Busca o diretório de trabalho atual.
 */
export async function getCwd(): Promise<GetCwdResponse> {
  const res = await fetch(`${API_BASE}/get-cwd`);
  if (!res.ok) throw new Error(`GET /get-cwd: ${res.status}`);
  return res.json();
}

// ── Execução ──────────────────────────────────

/**
 * Executa um comando no shell ativo do backend.
 * Timeout de 35s para comandos lentos.
 */
export async function executeCommand(cmd: string): Promise<ExecuteResponse> {
  const res = await fetch(`${API_BASE}/execute`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ cmd }),
    signal: AbortSignal.timeout(35_000),
  });
  if (!res.ok) throw new Error(`POST /execute: ${res.status}`);
  return res.json();
}

// ── Agente IA ─────────────────────────────────

/**
 * Verifica se a integração com a Gemini IA está disponível.
 */
export async function getAiStatus(): Promise<AiStatusResponse> {
  const res = await fetch(`${API_BASE}/ai/status`);
  if (!res.ok) throw new Error(`GET /ai/status: ${res.status}`);
  return res.json();
}

/**
 * Envia uma mensagem ao agente IA com contexto do terminal.
 * Retorna a resposta em texto e uma lista de comandos sugeridos.
 * @param model - Chave do modelo de IA a usar (ex: "gemini-2.5-flash", "llama-3.3-70b-versatile").
 */
export async function aiChat(
  message: string,
  context: AiContext,
  model?: string
): Promise<AiChatResponse> {
  const res = await fetch(`${API_BASE}/ai/chat`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ message, ...context, ...(model ? { model } : {}) }),
    signal: AbortSignal.timeout(30_000),
  });
  if (!res.ok) throw new Error(`POST /ai/chat: ${res.status}`);
  return res.json();
}

/**
 * Busca a lista de modelos de IA suportados e sua disponibilidade.
 */
export async function getAvailableModels(): Promise<{ models: ModelEntry[] }> {
  const res = await fetch(`${API_BASE}/ai/models`);
  if (!res.ok) throw new Error(`GET /ai/models: ${res.status}`);
  return res.json();
}

/**
 * Sincroniza a sessão (shell e cwd) no backend.
 */
export async function syncSession(
  shell: string,
  cwd: string
): Promise<ExecuteResponse> {
  const res = await fetch(`${API_BASE}/sync-session`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ shell, cwd }),
    signal: AbortSignal.timeout(5_000),
  });
  if (!res.ok) throw new Error(`POST /sync-session: ${res.status}`);
  return res.json();
}

/**
 * Verifica o risco de execução de um comando no backend.
 */
export async function checkCommandRisk(cmd: string, model?: string): Promise<RiskResponse> {
  const res = await fetch(`${API_BASE}/ai/check-risk`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ cmd, ...(model ? { model } : {}) }),
    signal: AbortSignal.timeout(10_000),
  });
  if (!res.ok) throw new Error(`POST /ai/check-risk: ${res.status}`);
  return res.json();
}

