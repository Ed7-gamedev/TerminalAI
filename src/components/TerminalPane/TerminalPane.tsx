import type { ShellInfo } from "../../types";
import { TerminalTopbar } from "./TerminalTopbar";
import { TabBar } from "./TabBar";
import type { TabSession } from "../../hooks/useTabManager";

interface TerminalPaneProps {
  terminalRef:  React.RefObject<HTMLDivElement | null>;
  currentShell: ShellInfo;
  copied:       boolean;
  onCopy:       () => void;
  // Tab manager
  tabs:         TabSession[];
  activeTabId:  string;
  onSwitchTab:  (id: string) => void;
  onCloseTab:   (id: string) => void;
  onAddTab:     () => void;
}

export function TerminalPane({
  terminalRef,
  currentShell,
  copied,
  onCopy,
  tabs,
  activeTabId,
  onSwitchTab,
  onCloseTab,
  onAddTab,
}: TerminalPaneProps) {
  return (
    <div className="terminal-wrapper">
      <TabBar
        tabs={tabs}
        activeTabId={activeTabId}
        onSwitch={onSwitchTab}
        onClose={onCloseTab}
        onAdd={onAddTab}
      />
      <TerminalTopbar
        currentShell={currentShell}
        copied={copied}
        onCopy={onCopy}
      />
      <div ref={terminalRef} className="terminal-container" />
    </div>
  );
}

