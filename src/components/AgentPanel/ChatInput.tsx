// ─────────────────────────────────────────────
// Componente: ChatInput
// Caixa de input do chat com o agente IA
// Terminal-AI | Fase 3
// ─────────────────────────────────────────────

import { useRef, useState } from "react";

interface ChatInputProps {
  isLoading:  boolean;
  onSend:     (text: string) => void;
  onClear:    () => void;
}

export function ChatInput({ isLoading, onSend, onClear }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSend() {
    const text = value.trim();
    if (!text || isLoading) return;
    onSend(text);
    setValue("");
    // Restaura altura do textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setValue(e.target.value);
    // Auto-resize
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
    }
  }

  return (
    <div className="chat-input-area">
      <textarea
        ref={textareaRef}
        id="chat-textarea"
        className="chat-textarea"
        placeholder="Pergunta ao agente… (Enter envia, Shift+Enter = nova linha)"
        value={value}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
        rows={1}
        spellCheck={false}
      />
      <div className="chat-input-actions">
        <button
          id="btn-chat-clear"
          className="chat-btn-clear"
          onClick={onClear}
          title="Limpar conversa"
          disabled={isLoading}
        >
          🗑
        </button>
        <button
          id="btn-chat-send"
          className={`chat-btn-send ${isLoading ? "chat-btn-send--loading" : ""}`}
          onClick={handleSend}
          disabled={isLoading || !value.trim()}
          title="Enviar (Enter)"
        >
          {isLoading
            ? <span className="chat-spinner" />
            : <span>↑</span>
          }
        </button>
      </div>
    </div>
  );
}
