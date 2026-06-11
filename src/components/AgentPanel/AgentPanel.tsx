import { useEffect, useRef } from "react";
import type { ShellInfo, ChatMessage as ChatMessageType, AiStatusResponse } from "../../types";
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

  return (
    <aside className="agent-panel" id="agent-panel">
      {/* Cabeçalho */}
      <div className="agent-header">
        <span className="agent-icon">✦</span>
        <h5>Agente IA</h5>
        {aiStatus?.available && (
          <span className="ai-badge-status ready" title={`Modelo: ${aiStatus.model}`}>
            {aiStatus.model || "Pronto"}
          </span>
        )}
      </div>

      {/* Seletor de Shell */}
      <div className="agent-shell-container">
        <ShellSelector
          currentShell={currentShell}
          onShellChange={onShellChange}
        />
      </div>

      {/* Status da API / Aviso de Configuração */}
      {aiStatus && !aiStatus.available && (
        <div className="ai-config-warning">
          <span className="ai-warning-icon">⚠</span>
          <div className="ai-warning-text">
            <strong>Gemini não configurado</strong>
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

