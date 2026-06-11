// ─────────────────────────────────────────────
// Hook: useCommandHistory
// Fila de histórico de comandos com navegação
// por setas cima/baixo — Terminal-AI
// ─────────────────────────────────────────────

import { useRef } from "react";

export interface CommandHistoryControls {
  /** Adiciona um comando ao histórico (ignora vazios e duplicados). */
  push: (cmd: string) => void;
  /**
   * Navega para o comando anterior.
   * Recebe o texto atual do input para salvar como rascunho.
   * Retorna o comando anterior ou null se o histórico estiver vazio.
   */
  navigateUp: (currentInput: string) => string | null;
  /**
   * Navega para o próximo comando.
   * Retorna o próximo comando ou o rascunho guardado se estiver no fim.
   */
  navigateDown: () => string;
  /** Reseta o índice e o rascunho (usar no Enter e Ctrl+C). */
  reset: () => void;
}

export function useCommandHistory(): CommandHistoryControls {
  const history      = useRef<string[]>([]);
  const index        = useRef<number>(-1);
  const draftInput   = useRef<string>("");

  function push(cmd: string): void {
    const trimmed = cmd.trim();
    if (!trimmed) return;
    const last = history.current[history.current.length - 1];
    if (last === trimmed) return; // ignora duplicados consecutivos
    history.current.push(trimmed);
  }

  function navigateUp(currentInput: string): string | null {
    if (history.current.length === 0) return null;

    if (index.current === -1) {
      // Guarda o que o utilizador estava a escrever
      draftInput.current = currentInput;
      index.current = history.current.length - 1;
    } else if (index.current > 0) {
      index.current--;
    }

    return history.current[index.current];
  }

  function navigateDown(): string {
    if (index.current === -1) return "";

    if (index.current === history.current.length - 1) {
      // Chegou ao fim — restaura o rascunho
      index.current = -1;
      return draftInput.current;
    }

    index.current++;
    return history.current[index.current];
  }

  function reset(): void {
    index.current      = -1;
    draftInput.current = "";
  }

  return { push, navigateUp, navigateDown, reset };
}
