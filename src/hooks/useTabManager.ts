// ─────────────────────────────────────────────
// Hook: useTabManager
// Gestão de múltiplas sessões de terminal (tabs)
// Terminal-AI | Fase 3
// ─────────────────────────────────────────────

import { useState, useRef, useCallback } from "react";
import type { ShellInfo } from "../types";

export interface TabSession {
  id:           string;
  label:        string;
  shell:        ShellInfo;
  cwd:          string;
  isCloseable:  boolean;
}

export interface TabManagerControls {
  tabs:        TabSession[];
  activeTabId: string;
  addTab:      (shell?: ShellInfo) => void;
  closeTab:    (id: string) => void;
  switchTab:   (id: string) => void;
  updateTab:   (id: string, patch: Partial<Omit<TabSession, "id">>) => void;
}

const DEFAULT_SHELL: ShellInfo = { key: "powershell", name: "PowerShell", icon: "🔷" };

function newId(): string {
  return `tab-${Date.now()}-${Math.random().toString(36).slice(2, 5)}`;
}

export function useTabManager(initialShell?: ShellInfo): TabManagerControls {
  const firstId = useRef(newId());

  const [tabs, setTabs] = useState<TabSession[]>([
    {
      id:          firstId.current,
      label:       "Terminal 1",
      shell:       initialShell ?? DEFAULT_SHELL,
      cwd:         "~",
      isCloseable: false, // a primeira tab não pode ser fechada
    },
  ]);

  const [activeTabId, setActiveTabId] = useState<string>(firstId.current);

  const addTab = useCallback((shell?: ShellInfo) => {
    const id = newId();
    const idx = tabs.length + 1;
    const newTab: TabSession = {
      id,
      label:       `Terminal ${idx}`,
      shell:       shell ?? DEFAULT_SHELL,
      cwd:         "~",
      isCloseable: true,
    };
    setTabs((prev) => [...prev, newTab]);
    setActiveTabId(id);
  }, [tabs.length]);

  const closeTab = useCallback((id: string) => {
    setTabs((prev) => {
      if (prev.length <= 1) return prev; // não fecha a última
      const next = prev.filter((t) => t.id !== id);
      return next;
    });

    setActiveTabId((prev) => {
      if (prev !== id) return prev;
      // Activa a tab anterior ou a seguinte
      const idx = tabs.findIndex((t) => t.id === id);
      const fallback = tabs[idx - 1] ?? tabs[idx + 1];
      return fallback?.id ?? tabs[0].id;
    });
  }, [tabs]);

  const switchTab = useCallback((id: string) => {
    setActiveTabId(id);
  }, []);

  const updateTab = useCallback((id: string, patch: Partial<Omit<TabSession, "id">>) => {
    setTabs((prev) =>
      prev.map((t) => (t.id === id ? { ...t, ...patch } : t))
    );
  }, []);

  return { tabs, activeTabId, addTab, closeTab, switchTab, updateTab };
}
