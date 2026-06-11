import { useEffect, useState, useRef } from "react";
import "xterm/css/xterm.css";
import "./App.css";

import {
  waitForBackend,
  getShell,
  getCwd,
  executeCommand,
  syncSession,
} from "./services/api";
import { useTerminal } from "./hooks/useTerminal";
import { useShell }    from "./hooks/useShell";
import { useCommandHistory } from "./hooks/useCommandHistory";
import { useTabManager } from "./hooks/useTabManager";
import { useAiChat } from "./hooks/useAiChat";
import { TerminalPane } from "./components/TerminalPane/TerminalPane";
import { AgentPanel }   from "./components/AgentPanel/AgentPanel";

import type { BackendStatus, ShellInfo } from "./types";


// ── Helpers ───────────────────────────────────

function buildPrompt(cwd: string, shell: ShellInfo): string {
  return `${shell.icon} [${shell.name}] ${cwd} > `;
}

// ── Componente principal ──────────────────────

function App() {
  const { terminalRef, termRef, promptRef, terminalReady, copied, handleCopyTerminal } = useTerminal();
  const { currentShell, setCurrentShell, handleShellChange: rawHandleShellChange } = useShell(termRef, promptRef, buildPrompt);
  const cmdHistory = useCommandHistory();

  // Tab Manager
  const { tabs, activeTabId, addTab, closeTab, switchTab, updateTab } = useTabManager(currentShell);

  // AI Chat
  const { messages, isLoading, aiStatus, lastOutputRef, sendMessage, clearChat, checkAiStatus } = useAiChat(promptRef, currentShell);

  const [backendStatus, setBackendStatus] = useState<BackendStatus>("connecting");

  const isFirstMount = useRef(true);

  // ── Sincronização de Tabs ──────────────────
  useEffect(() => {
    if (!terminalReady) return;

    if (isFirstMount.current) {
      isFirstMount.current = false;
      return;
    }

    const activeTab = tabs.find((t) => t.id === activeTabId);
    if (!activeTab) return;

    // Sincroniza o backend com o estado da aba ativada
    syncSession(activeTab.shell.key, activeTab.cwd).catch((err) => {
      console.error("Erro ao sincronizar sessão no backend:", err);
    });

    // Atualiza estados do shell ativo na UI
    setCurrentShell(activeTab.shell);
    promptRef.current = buildPrompt(activeTab.cwd, activeTab.shell);

    const term = termRef.current;
    if (term) {
      term.clear();
      term.write(`\x1b[90m--- Alternado para ${activeTab.label} (${activeTab.shell.name}) ---\x1b[0m\r\n`);
      term.write(promptRef.current);
      term.focus();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTabId, terminalReady]);

  // ── Inicialização do terminal ───────────────
  useEffect(() => {
    const term = termRef.current;
    if (!term) return;

    term.write("\x1b[36mConectando ao backend...\x1b[0m\r\n");

    waitForBackend().then(async (connected) => {
      if (!connected) {
        setBackendStatus("error");
        term.write("\x1b[31m✗ Falha ao conectar ao backend Python.\x1b[0m\r\n");
        term.write("\x1b[33mDica: cd backend && python -m uvicorn main:app\x1b[0m\r\n");
        return;
      }

      setBackendStatus("ready");

      try {
        const shellData = await getShell();
        const shell: ShellInfo = {
          key:  shellData.shell,
          name: shellData.shell_name,
          icon: shellData.shell_icon,
        };
        setCurrentShell(shell);

        const cwdData = await getCwd();
        const cwd = cwdData.cwd || "~";
        promptRef.current = buildPrompt(cwd, shell);

        // Atualiza a primeira aba com as definições originais obtidas do backend
        updateTab(activeTabId, { shell, cwd });

        term.write("\x1b[32m✓ Terminal pronto\x1b[0m\r\n");
        term.write("\x1b[90mDigite 'shell list' para ver shells disponíveis\x1b[0m\r\n");
        term.write(promptRef.current);
        term.focus();
      } catch (err) {
        term.write(`\x1b[31mErro ao inicializar: ${err}\x1b[0m\r\n`);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terminalReady]);

  // ── Input handler ───────────────────────────
  useEffect(() => {
    const term = termRef.current;
    if (!term) return;

    const inputBuffer = { current: "" };

    const disposable = term.onData((data) => {
      const code = data.charCodeAt(0);

      if (code === 13) { // Enter
        term.write("\r\n");
        const cmd = inputBuffer.current;
        cmdHistory.push(cmd);
        cmdHistory.reset();
        handleCommand(cmd);
        inputBuffer.current = "";

      } else if (code === 127 || code === 8) { // Backspace
        if (inputBuffer.current.length > 0) {
          term.write("\b \b");
          inputBuffer.current = inputBuffer.current.slice(0, -1);
        }

      } else if (code === 3) { // Ctrl+C
        term.write("^C\r\n");
        inputBuffer.current = "";
        cmdHistory.reset();
        term.write(promptRef.current);

      } else if (data === "\u001b[A") { // Seta CIMA
        const prev = cmdHistory.navigateUp(inputBuffer.current);
        if (prev !== null) {
          term.write("\b \b".repeat(inputBuffer.current.length));
          term.write(prev);
          inputBuffer.current = prev;
        }

      } else if (data === "\u001b[B") { // Seta BAIXO
        const next = cmdHistory.navigateDown();
        term.write("\b \b".repeat(inputBuffer.current.length));
        term.write(next);
        inputBuffer.current = next;

      } else if (data.startsWith("\u001b")) {
        // Ignora outros escapes (ex: setas laterais)
        return;

      } else {
        term.write(data);
        inputBuffer.current += data;
      }
    });

    return () => disposable.dispose();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terminalReady]);

  // Wrapper do handleShellChange para também atualizar o estado da tab
  const handleShellChange = async (shellKey: string) => {
    await rawHandleShellChange(shellKey);
    try {
      const shellData = await getShell();
      const cwdData = await getCwd();
      const newShell: ShellInfo = {
        key:  shellData.shell,
        name: shellData.shell_name,
        icon: shellData.shell_icon,
      };
      updateTab(activeTabId, {
        shell: newShell,
        cwd: cwdData.cwd || "~",
      });
    } catch (err) {
      console.error(err);
    }
  };

  // Execução programática via chat do Agente IA
  const handleExecuteFromAi = (cmd: string) => {
    const term = termRef.current;
    if (!term) return;
    term.write(cmd + "\r\n");
    handleCommand(cmd);
  };

  const handleNewTab = () => {
    addTab(currentShell);
  };

  // ── Execução de comandos ────────────────────
  const handleCommand = async (cmd: string) => {
    const term = termRef.current;
    if (!term) return;

    const trimmed = cmd.trim();

    if (trimmed.toLowerCase() === "cls" || trimmed.toLowerCase() === "clear") {
      term.clear();
      term.write(promptRef.current);
      return;
    }

    if (!trimmed) {
      term.write(promptRef.current);
      return;
    }

    try {
      const data = await executeCommand(cmd);

      // Grava output para contexto do chat da IA
      let outputText = "";
      if (data.output) outputText += data.output;
      if (data.error) outputText += data.error;
      lastOutputRef.current = (lastOutputRef.current + "\n" + outputText).slice(-3000);

      // Atualiza shell se mudou no backend
      let updatedShell = currentShell;
      if (data.shell && data.shell !== currentShell.key) {
        updatedShell = {
          key:  data.shell,
          name: data.shell_name,
          icon: data.shell_icon,
        };
        setCurrentShell(updatedShell);
      }

      if (data.cwd) {
        promptRef.current = buildPrompt(data.cwd, updatedShell);
      }

      // Sincroniza aba ativa localmente com o novo shell e cwd
      updateTab(activeTabId, {
        shell: updatedShell,
        cwd: data.cwd || "~",
      });

      if (data.output) term.write(data.output.replace(/\r?\n/g, "\r\n"));
      if (data.error)  term.write(`\x1b[31m${data.error.replace(/\r?\n/g, "\r\n")}\x1b[0m`);

    } catch (err) {
      if (err instanceof Error) {
        if (err.name === "TimeoutError") {
          term.write("\x1b[33mComando cancelado: tempo limite excedido.\x1b[0m\r\n");
        } else {
          term.write(`\x1b[31mErro de conexão: ${err.message}\x1b[0m\r\n`);
        }
      }
    }

    term.write(promptRef.current);
  };

  // ── Render ──────────────────────────────────
  return (
    <main className="container">
      {/* Status bar de conexão */}
      {backendStatus === "connecting" && (
        <div className="status-bar status-connecting">
          <span className="status-dot" /> Conectando ao backend...
        </div>
      )}
      {backendStatus === "error" && (
        <div className="status-bar status-error">
          <span className="status-dot" /> Backend indisponível — verifique o Python
        </div>
      )}

      <TerminalPane
        terminalRef={terminalRef}
        currentShell={currentShell}
        copied={copied}
        onCopy={handleCopyTerminal}
        tabs={tabs}
        activeTabId={activeTabId}
        onSwitchTab={switchTab}
        onCloseTab={closeTab}
        onAddTab={handleNewTab}
      />

      <AgentPanel
        currentShell={currentShell}
        onShellChange={handleShellChange}
        messages={messages}
        isLoading={isLoading}
        aiStatus={aiStatus}
        sendMessage={sendMessage}
        clearChat={clearChat}
        checkAiStatus={checkAiStatus}
        onExecuteCommand={handleExecuteFromAi}
      />
    </main>
  );
}

export default App;