// ─────────────────────────────────────────────
// Componente: ChatMessage
// Balão de mensagem individual do chat de IA
// Terminal-AI | Fase 3
// ─────────────────────────────────────────────

import { useState } from "react";
import type { ChatMessage as ChatMessageType } from "../../types";

interface ChatMessageProps {
  message:          ChatMessageType;
  onExecuteCommand: (cmd: string) => void;
}

function CodeHeaderActions({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Falha ao copiar:", err);
    }
  };

  return (
    <div className="chat-code-header">
      <span className="chat-code-lang">{lang}</span>
      <button
        className={`chat-code-copy-btn ${copied ? "chat-code-copy-btn--copied" : ""}`}
        onClick={handleCopy}
        title="Copiar código para a área de transferência"
      >
        {copied ? "✓ Copiado" : "📋 Copiar"}
      </button>
    </div>
  );
}

export function ChatMessage({ message, onExecuteCommand }: ChatMessageProps) {
  const isUser = message.role === "user";

  // Renderiza o conteúdo com blocos de código destacados
  function renderContent(text: string) {
    const parts = text.split(/(```[\w]*\n[\s\S]*?```)/g);
    return parts.map((part, i) => {
      const codeMatch = part.match(/^```([\w]*)\n([\s\S]*?)```$/);
      if (codeMatch) {
        const lang = codeMatch[1] || "bash";
        const code = codeMatch[2].trim();
        return (
          <div key={i} className="chat-code-block">
            <CodeHeaderActions code={code} lang={lang} />
            <pre className="chat-code-pre"><code>{code}</code></pre>
            <button
              className="chat-code-run"
              onClick={() => onExecuteCommand(code)}
              title="Executar no terminal"
            >
              ▶ Executar
            </button>
          </div>
        );
      }
      // Texto normal — converte \n em quebras
      return (
        <span key={i} className="chat-text">
          {part.split("\n").map((line, j, arr) => (
            <span key={j}>
              {line}
              {j < arr.length - 1 && <br />}
            </span>
          ))}
        </span>
      );
    });
  }

  return (
    <div className={`chat-msg ${isUser ? "chat-msg-user" : "chat-msg-ai"}`}>
      {!isUser && (
        <div className="chat-msg-avatar" aria-hidden>✦</div>
      )}
      <div className="chat-msg-bubble">
        {renderContent(message.content)}

        {/* Comandos sugeridos rápidos (fora dos blocos de código) */}
        {!isUser && message.commands.length > 0 && (
          <div className="chat-suggestions">
            <span className="chat-suggestions-label">Sugestões:</span>
            {message.commands.slice(0, 3).map((cmd, i) => (
              <button
                key={i}
                className="chat-suggestion-chip"
                onClick={() => onExecuteCommand(cmd)}
                title={cmd}
              >
                ▶ {cmd.length > 40 ? cmd.slice(0, 40) + "…" : cmd}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
