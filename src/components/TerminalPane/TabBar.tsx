// ─────────────────────────────────────────────
// Componente: TabBar
// Barra de abas para múltiplos terminais
// Terminal-AI | Fase 3
// ─────────────────────────────────────────────

import type { TabSession } from "../../hooks/useTabManager";
import { SHELL_COLORS } from "../../constants/shells";

interface TabBarProps {
  tabs:        TabSession[];
  activeTabId: string;
  onSwitch:    (id: string) => void;
  onClose:     (id: string) => void;
  onAdd:       () => void;
}

export function TabBar({ tabs, activeTabId, onSwitch, onClose, onAdd }: TabBarProps) {
  return (
    <div className="tab-bar">
      {tabs.map((tab) => {
        const isActive = tab.id === activeTabId;
        const color    = SHELL_COLORS[tab.shell.key] ?? "#e6edf3";
        return (
          <div
            key={tab.id}
            id={`tab-${tab.id}`}
            className={`tab-item ${isActive ? "tab-item--active" : ""}`}
            style={isActive ? { borderTopColor: color } : {}}
            onClick={() => onSwitch(tab.id)}
            title={`${tab.shell.icon} ${tab.shell.name} — ${tab.cwd}`}
          >
            <span className="tab-shell-icon">{tab.shell.icon}</span>
            <span className="tab-label">{tab.label}</span>
            {tab.isCloseable && (
              <button
                className="tab-close"
                onClick={(e) => { e.stopPropagation(); onClose(tab.id); }}
                title="Fechar aba"
              >
                ×
              </button>
            )}
          </div>
        );
      })}

      {/* Botão nova tab */}
      <button
        id="btn-new-tab"
        className="tab-new"
        onClick={onAdd}
        title="Abrir novo terminal"
      >
        +
      </button>
    </div>
  );
}
