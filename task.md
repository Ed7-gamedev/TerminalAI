# Terminal-AI — Fase 1: Estabilização

## Tarefas

- [x] Adicionar `backend/requirements.txt`
- [x] Corrigir CORS para origens específicas (`localhost:1420`, `tauri://localhost`)
- [x] Inicialização automática do backend Python via `lib.rs` (setup hook Tauri)
- [x] Tratamento de erro quando backend não está disponível (status bar + retry automático)
- [x] Corrigir layout CSS (substituir `position:absolute` + margins hardcoded por CSS Grid)

## Extras implementados
- [x] Health check endpoint `/health` no backend
- [x] Timeout de 30s nos comandos do backend (evita travamento)
- [x] Timeout de 35s no fetch do frontend
- [x] Ctrl+C no terminal para cancelar input
- [x] Normalização de quebras de linha (`\r\n`) no output
- [x] Tema visual melhorado no xterm (paleta GitHub Dark)
- [x] Sistema de design com CSS Variables

## Próximas fases
- [ ] Fase 2 — Refatoração: separar App.tsx em componentes, criar hooks e services
- [ ] Fase 3 — Agente de IA com chat real
- [ ] Fase 4 — Polish e features avançadas
