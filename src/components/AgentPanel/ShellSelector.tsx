import type { ShellInfo } from "../../types";
import { SHELL_ICONS, SHELL_COLORS, SHELL_NAMES } from "../../constants/shells";

interface ShellSelectorProps {
  currentShell:    ShellInfo;
  onShellChange:   (shellKey: string) => void;
}

export function ShellSelector({ currentShell, onShellChange }: ShellSelectorProps) {
  return (
    <div className="shell-selector-panel">
      <label htmlFor="shell-select" className="shell-select-label">
        Shell:
      </label>
      <div className="shell-select-wrapper">
        <span className="shell-select-icon">{SHELL_ICONS[currentShell.key]}</span>
        <select
          id="shell-select"
          className="shell-select-dropdown"
          value={currentShell.key}
          onChange={(e) => onShellChange(e.target.value)}
          style={{ color: SHELL_COLORS[currentShell.key] }}
        >
          {Object.entries(SHELL_ICONS).map(([key, icon]) => (
            <option
              key={key}
              value={key}
              style={{ color: SHELL_COLORS[key] || "#fff", backgroundColor: "#161b22" }}
            >
              {icon} {SHELL_NAMES[key] ?? key}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

