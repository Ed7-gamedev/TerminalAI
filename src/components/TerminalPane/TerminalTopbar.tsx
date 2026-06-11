// ─────────────────────────────────────────────
// Componente: TerminalTopbar
// Barra superior do terminal com dots, badge
// do shell ativo e botão de cópia
// Terminal-AI
// ─────────────────────────────────────────────

import type { ShellInfo } from "../../types";
import { SHELL_COLORS } from "../../constants/shells";

interface TerminalTopbarProps {
  currentShell: ShellInfo;
  copied:       boolean;
  onCopy:       () => void;
}

export function TerminalTopbar({ currentShell, copied, onCopy }: TerminalTopbarProps) {
  const shellColor = SHELL_COLORS[currentShell.key] ?? "#e6edf3";

  return (
    <div className="terminal-topbar">
      {/* Botões estilo macOS */}
      <div className="window-dots">
        <span className="dot dot-red"    />
        <span className="dot dot-yellow" />
        <span className="dot dot-green"  />
      </div>

      {/* Badge do shell ativo */}
      <div className="shell-badge" style={{ color: shellColor }}>
        <span className="shell-badge-icon">{currentShell.icon}</span>
        <span className="shell-badge-name">{currentShell.name}</span>
      </div>

      {/* Ações copiar e hint */}
      <div className="topbar-actions">
        <button
          id="btn-copy-terminal"
          className={`copy-btn ${copied ? "copy-btn--success" : ""}`}
          onClick={onCopy}
          title="Copiar conteúdo do terminal"
        >
          <span className="copy-btn-icon">{copied ? "✓" : "📋"}</span>
          <span>{copied ? "Copiado" : "Copiar"}</span>
        </button>
        <span className="shell-hint">
          shell list · shell &lt;nome&gt;
        </span>
      </div>
    </div>
  );
}
