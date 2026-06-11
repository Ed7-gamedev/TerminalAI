// ─────────────────────────────────────────────
// Hook: useAiChat
// Histórico de mensagens + comunicação com
// o agente IA, com contexto do terminal e
// suporte a múltiplos modelos com fallback
// Terminal-AI | Fase 4
// ─────────────────────────────────────────────

import { useState, useRef, useCallback, useEffect } from "react";
import { aiChat, getAiStatus, getAvailableModels } from "../services/api";
import type { ChatMessage, AiStatusResponse, ShellInfo, ModelEntry } from "../types";

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

export interface AiChatControls {
  messages:        ChatMessage[];
  isLoading:       boolean;
  aiStatus:        AiStatusResponse | null;
  lastOutputRef:   React.MutableRefObject<string>;
  availableModels: ModelEntry[];
  selectedModel:   string;
  activeModel:     string | null;
  setSelectedModel: (modelKey: string) => void;
  sendMessage:     (text: string) => Promise<void>;
  clearChat:       () => void;
  checkAiStatus:   () => Promise<void>;
}

export function useAiChat(
  promptRef:    React.RefObject<string>,
  currentShell: ShellInfo
): AiChatControls {
  const [messages,        setMessages]        = useState<ChatMessage[]>([]);
  const [isLoading,       setIsLoading]       = useState(false);
  const [aiStatus,        setAiStatus]        = useState<AiStatusResponse | null>(null);
  const [availableModels, setAvailableModels] = useState<ModelEntry[]>([]);
  const [selectedModel,   setSelectedModel]   = useState<string>("llama-3.3-70b-versatile");
  const [activeModel,     setActiveModel]     = useState<string | null>(null);

  // Buffer do último output do terminal (actualizado externamente)
  const lastOutputRef = useRef<string>("");

  // Extrai o cwd do prompt actual (formato: "icon [Shell] /path > ")
  function extractCwd(): string {
    const prompt = promptRef.current ?? "";
    const match = prompt.match(/\]\s(.+?)\s>/);
    return match ? match[1].trim() : "~";
  }

  // Constrói o histórico alternado para a API
  function buildHistory(msgs: ChatMessage[]): string[] {
    return msgs.slice(-10).map((m) => m.content);
  }

  // Carrega modelos disponíveis ao iniciar
  useEffect(() => {
    (async () => {
      try {
        const data = await getAvailableModels();
        setAvailableModels(data.models);
        // Seleciona automaticamente o primeiro modelo disponível
        const firstAvailable = data.models.find((m) => m.available);
        if (firstAvailable) {
          setSelectedModel(firstAvailable.key);
        }
      } catch {
        // silencia erros — backend pode estar iniciando
      }
    })();
  }, []);

  const checkAiStatus = useCallback(async () => {
    try {
      const status = await getAiStatus();
      setAiStatus(status);
      // Também actualiza a lista de modelos
      try {
        const data = await getAvailableModels();
        setAvailableModels(data.models);
      } catch { /* silencia */ }
    } catch {
      setAiStatus({ available: false, model: null, reason: "Backend indisponível" });
    }
  }, []);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id:        newId(),
      role:      "user",
      content:   text.trim(),
      commands:  [],
      timestamp: new Date(),
    };

    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setIsLoading(true);

    try {
      const data = await aiChat(
        text.trim(),
        {
          shell:       currentShell.key,
          cwd:         extractCwd(),
          last_output: lastOutputRef.current.slice(-1500),
          history:     buildHistory(messages),
        },
        selectedModel
      );

      // Regista qual modelo efetivamente respondeu
      const respondingModel = data.active_model ?? selectedModel;
      setActiveModel(respondingModel);

      // Aviso de fallback se o modelo mudou
      const requestedEntry = availableModels.find((m) => m.key === selectedModel);
      const respondingEntry = availableModels.find((m) => m.key === respondingModel);
      const didFallback = respondingModel !== selectedModel;

      let content = data.reply || data.error || "Sem resposta.";
      if (didFallback && requestedEntry && respondingEntry) {
        content = `> ⚠️ *Modelo ${requestedEntry.name} indisponível. Respondido por **${respondingEntry.name}**.*\n\n${content}`;
      }

      const aiMsg: ChatMessage = {
        id:        newId(),
        role:      "assistant",
        content,
        commands:  data.commands ?? [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMsg]);

      // Se a IA não estava disponível, actualiza status
      if (data.error === "AI_NOT_CONFIGURED" || data.error === "NO_MODELS_AVAILABLE") {
        setAiStatus({ available: false, model: null, reason: data.reply });
      }
    } catch (err) {
      const errMsg: ChatMessage = {
        id:        newId(),
        role:      "assistant",
        content:   `❌ Erro: ${err instanceof Error ? err.message : String(err)}`,
        commands:  [],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, isLoading, currentShell, promptRef, selectedModel, availableModels]);

  const clearChat = useCallback(() => {
    setMessages([]);
    lastOutputRef.current = "";
  }, []);

  return {
    messages,
    isLoading,
    aiStatus,
    lastOutputRef,
    availableModels,
    selectedModel,
    activeModel,
    setSelectedModel,
    sendMessage,
    clearChat,
    checkAiStatus,
  };
}
