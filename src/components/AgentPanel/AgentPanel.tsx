import { useEffect, useRef } from "react";
import type { ShellInfo, ChatMessage as ChatMessageType, AiStatusResponse, ModelEntry } from "../../types";
import { ShellSelector } from "./ShellSelector";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

interface AgentPanelProps {
  currentShell:     ShellInfo;
  onShellChange:    (shellKey: string) => void;
  messages:         ChatMessageType[];
  isLoading:        boolean;
  aiStatus:         AiStatusResponse | null;
  sendMessage:      (text: string) => Promise<void>;
  clearChat:        () => void;
  checkAiStatus:    () => Promise<void>;
  onExecuteCommand: (cmd: string) => void;
  availableModels:  ModelEntry[];
  selectedModel:    string;
  activeModel:      string | null;
  onModelChange:    (modelKey: string) => void;
  onCloseAgent:     () => void;
}

export function AgentPanel({
  currentShell,
  onShellChange,
  messages,
  isLoading,
  aiStatus,
  sendMessage,
  clearChat,
  checkAiStatus,
  onExecuteCommand,
  availableModels,
  selectedModel,
  activeModel,
  onModelChange,
  onCloseAgent,
}: AgentPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Check status on mount
  useEffect(() => {
    checkAiStatus();
  }, [checkAiStatus]);

  // Auto scroll to bottom when messages or loading state changes
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const activeModelEntry = availableModels.find((m) => m.key === (activeModel ?? selectedModel));
  const availableCount = availableModels.filter((m) => m.available).length;

  return (
    <aside className="agent-panel" id="agent-panel">
      {/* Cabeçalho */}
      <div className="agent-header">
        <span className="agent-icon">✦</span>
        <h5>Agente IA</h5>
        {aiStatus?.available && (
          <span className="ai-badge-status ready" title={`Modelo ativo: ${activeModelEntry?.name ?? selectedModel}`}>
            {activeModelEntry?.name ?? (aiStatus.model || "Pronto")}
          </span>
        )}
        <button
          id="btn-close-agent"
          className="agent-close-btn"
          onClick={onCloseAgent}
          title="Ocultar painel da IA"
        >
          ×
        </button>
      </div>

      {/* Seletor de Shell + Seletor de Modelo */}
      <div className="agent-controls-row">
        <ShellSelector
          currentShell={currentShell}
          onShellChange={onShellChange}
        />

        {availableModels.length > 0 && (
          <div className="model-selector-wrap" title={`${availableCount} modelo(s) disponíveis`}>
            <span className="model-selector-icon">🤖</span>
            <select
              id="model-selector"
              className="model-select-dropdown"
              value={selectedModel}
              onChange={(e) => onModelChange(e.target.value)}
              aria-label="Selecionar modelo de IA"
            >
              {availableModels.map((m) => (
                <option key={m.key} value={m.key} disabled={!m.available}>
                  {m.name}{!m.available ? " (indisponível)" : ""}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Status da API / Aviso de Configuração */}
      {aiStatus && !aiStatus.available && (
        <div className="ai-config-warning">
          <span className="ai-warning-icon">⚠</span>
          <div className="ai-warning-text">
            <strong>IA não configurada</strong>
            <p>{aiStatus.reason || "Configure a chave de API no backend."}</p>
          </div>
        </div>
      )}

      {/* Área de Mensagens do Chat */}
      <div className="agent-chat-area" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="agent-placeholder">
            <span className="placeholder-icon">💬</span>
            <p>Olá! Sou o assistente de IA integrado no seu terminal.</p>
            <p className="placeholder-tip">Posso ajudar a compor comandos, analisar erros ou sugerir ferramentas. O contexto do seu terminal é enviado automaticamente!</p>
          </div>
        ) : (
          <div className="chat-messages-list">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onExecuteCommand={onExecuteCommand}
              />
            ))}
            {isLoading && (
              <div className="chat-msg chat-msg-ai chat-msg-thinking">
                <div className="chat-msg-avatar" aria-hidden>✦</div>
                <div className="chat-msg-bubble">
                  <div className="thinking-dots">
                    <span>.</span><span>.</span><span>.</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Caixa de Input */}
      <ChatInput
        isLoading={isLoading}
        onSend={sendMessage}
        onClear={clearChat}
      />
    </aside>
  );
}
