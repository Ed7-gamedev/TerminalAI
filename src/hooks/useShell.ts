// ─────────────────────────────────────────────
// Hook: useShell
// Estado do shell atual + troca via sidebar
// Terminal-AI
// ─────────────────────────────────────────────

import { useRef, useState } from "react";
import type { Terminal } from "xterm";
import { getCwd, setShell } from "../services/api";
import type { ShellInfo } from "../types";

export interface ShellControls {
  currentShell:    ShellInfo;
  setCurrentShell: React.Dispatch<React.SetStateAction<ShellInfo>>;
  handleShellChange: (shellKey: string) => Promise<void>;
}

export function useShell(
  termRef:   React.RefObject<Terminal | null>,
  promptRef: React.RefObject<string>,
  buildPrompt: (cwd: string, shell: ShellInfo) => string
): ShellControls {
  const [currentShell, setCurrentShell] = useState<ShellInfo>({
    key:  "powershell",
    name: "PowerShell",
    icon: "🔷",
  });

  // Evita chamadas simultâneas
  const switching = useRef(false);

  async function handleShellChange(shellKey: string): Promise<void> {
    const term = termRef.current;
    if (!term || switching.current) return;

    switching.current = true;
    try {
      const data = await setShell(shellKey);

      if (data.success) {
        const newShell: ShellInfo = {
          key:  data.shell,
          name: data.shell_name,
          icon: data.shell_icon,
        };
        setCurrentShell(newShell);

        const cwdData = await getCwd();
        const cwd = cwdData.cwd || "~";
        promptRef.current = buildPrompt(cwd, newShell);

        term.write(`\r\n\x1b[32m✓ ${newShell.icon} Alterado para ${newShell.name}\x1b[0m\r\n`);
        term.write(promptRef.current);
        term.focus();
      } else {
        term.write(`\r\n\x1b[31m✗ ${data.error ?? "Erro desconhecido"}\x1b[0m\r\n`);
        term.write(promptRef.current);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      term.write(`\r\n\x1b[31mErro de conexão: ${msg}\x1b[0m\r\n`);
      term.write(promptRef.current);
    } finally {
      switching.current = false;
    }
  }

  return { currentShell, setCurrentShell, handleShellChange };
}
