// ─────────────────────────────────────────────
// Hook: useTerminal
// Ciclo de vida do xterm.js + cópia de conteúdo
// Terminal-AI
// ─────────────────────────────────────────────

import { useEffect, useRef, useState } from "react";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";

export const TERMINAL_THEME = {
  background:          "#0d1117",
  foreground:          "#e6edf3",
  cursor:              "#58a6ff",
  selectionBackground: "#264f78",
  black:               "#484f58",
  red:                 "#ff7b72",
  green:               "#3fb950",
  yellow:              "#d29922",
  blue:                "#58a6ff",
  magenta:             "#bc8cff",
  cyan:                "#39c5cf",
  white:               "#b1bac4",
};

export interface TerminalControls {
  /** Ref para o elemento DOM onde o xterm é montado. */
  terminalRef:      React.RefObject<HTMLDivElement | null>;
  /** Ref para a instância do xterm.js. */
  termRef:          React.RefObject<Terminal | null>;
  /** Ref para o FitAddon (resize). */
  fitAddonRef:      React.RefObject<FitAddon | null>;
  /** Ref para o texto do prompt actual. */
  promptRef:        React.RefObject<string>;
  /** true depois do xterm.open() — usar como dependency de useEffect em vez de termRef.current */
  terminalReady:    boolean;
  /** Estado de feedback do botão copiar. */
  copied:           boolean;
  /** Copia a seleção ou o buffer completo da tela. */
  handleCopyTerminal: () => void;
}

export function useTerminal(): TerminalControls {
  const terminalRef = useRef<HTMLDivElement | null>(null);
  const termRef     = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const promptRef   = useRef<string>("$ > ");
  const [terminalReady, setTerminalReady] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const term = new Terminal({
      cursorBlink:  true,
      theme:        TERMINAL_THEME,
      fontSize:     14,
      fontFamily:   "'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace",
      lineHeight:   1.4,
      letterSpacing: 0.5,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);

    if (terminalRef.current) {
      term.open(terminalRef.current);
      fitAddon.fit();
    }

    termRef.current     = term;
    fitAddonRef.current = fitAddon;
    // Sinaliza que o terminal está pronto para useEffects dependentes
    setTerminalReady(true);

    const handleResize = () => fitAddon.fit();
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      term.dispose();
    };
  }, []);

  function handleCopyTerminal(): void {
    const term = termRef.current;
    if (!term) return;

    let text = "";
    if (term.hasSelection()) {
      text = term.getSelection();
    } else {
      const buffer = term.buffer.active;
      const lines: string[] = [];
      for (let i = 0; i < buffer.length; i++) {
        const line = buffer.getLine(i);
        if (line) lines.push(line.translateToString(true));
      }
      text = lines.join("\n");
    }

    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return {
    terminalRef,
    termRef,
    fitAddonRef,
    promptRef,
    terminalReady,
    copied,
    handleCopyTerminal,
  };
}
