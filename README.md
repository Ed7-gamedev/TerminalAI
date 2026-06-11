# 🐉 Terminal-AI

**Terminal-AI** é um emulador de terminal moderno e inteligente construído sobre **Tauri v2**, **React (TypeScript)** e **FastAPI (Python)**. Ele integra um terminal robusto (via `xterm.js`) a um **Agente de Inteligência Artificial** (alimentado pelo Google Gemini) capaz de compreender o contexto atual do shell, histórico de comandos e sugerir ações corretivas ou novos comandos diretamente na interface.

---

## 📸 Demonstração & Interface

A interface do Terminal-AI foi projetada para ser limpa, moderna e produtiva:
* **Área de Terminal (Esquerda):** Terminal interativo baseado em `xterm.js` com suporte a múltiplas abas, troca rápida de shell e controle de execução.
* **Painel do Agente IA (Direita):** Um chat integrado com o modelo `gemini-2.5-flash` que lê o contexto do seu terminal (últimos logs, diretório de trabalho atual e shell em uso) para oferecer assistência em tempo real.

---

## ⚡ Principais Funcionalidades

### 💻 Terminal Avançado & Multi-Shell
* **Seleção Inteligente de Shells:** Troca instantânea e direta entre diversos ambientes, detectados e configurados dinamicamente no sistema:
  * ⊞ **CMD** (Windows Command Prompt)
  * 🔷 **PowerShell**
  * 🐧 **Git Bash**
  * 🐉 **WSL (Kali Linux)**
  * 🐍 **Python** (Interpretador interativo)
  * ⬡ **Node.js**
  * 🟦 **TypeScript** (via `ts-node` ou `tsx`)
  * ☕ **Java** (via `jshell`)
  * 🐳 **Docker** (Container Alpine isolado)
* **Sincronização de Diretório (`cd`):** Navegação nativa que atualiza automaticamente o diretório de trabalho no backend e na interface.
* **Resiliência e Interrupção:** Atalho nativo `Ctrl+C` para cancelamento rápido de comandos em execução e timeout de segurança de 30 segundos para evitar travamento de processos.

### 🤖 Agente de IA Integrado (Google Gemini)
* **Consciência de Contexto:** A IA recebe o caminho atual, o shell selecionado, o histórico da conversa e os últimos 1500 caracteres de output do terminal.
* **Extração Automática de Comandos:** O agente extrai comandos sugeridos formatados em blocos de código Markdown (ex: \`\`\`bash) e os exibe como botões clicáveis de execução rápida.
* **Diagnóstico Ativo:** Ideal para explicar mensagens de erro, sugerir sequências de build ou automatizar tarefas repetitivas.

### ⚙️ Arquitetura Integrada
* **Gerenciamento Nativo de Processo (Rust):** O backend Python (FastAPI + Uvicorn) é iniciado automaticamente pela camada nativa Rust do Tauri durante o boot da aplicação e finalizado de forma limpa quando o app é fechado.
* **Comunicação Segura:** CORS restrito às portas internas do Tauri (`localhost:1420` e `tauri://localhost`).
* **Indicador de Conexão:** Barra de status com monitoramento de conexão com o backend e botão para reconectar em caso de quedas.

---

## 📐 Estrutura do Projeto

```text
terminal-ai/
├── src/                          # Frontend React (TypeScript)
│   ├── components/               
│   │   ├── AgentPanel/           # Painel de chat da IA e histórico
│   │   └── TerminalPane/         # Componente de abas, terminal (xterm) e cabeçalhos
│   ├── hooks/                    # Gerenciadores de estado (chat, histórico, tabs e terminal)
│   ├── services/                 # Clientes de API para comunicação com o backend
│   ├── types/                    # Tipagens globais do sistema
│   ├── App.tsx                   # Layout principal e montagem dos painéis
│   └── main.tsx
├── src-tauri/                    # Camada Desktop Nativa (Rust)
│   ├── src/
│   │   ├── lib.rs                # Lifecycle do app e controle de subprocesso Python
│   │   └── main.rs
│   └── tauri.conf.json           # Configurações de build e permissões do Tauri
└── backend/                      # API de Execução e IA (Python / FastAPI)
    ├── main.py                   # Endpoints de execução de comandos, shells e API Gemini
    ├── requirements.txt          # Dependências Python (fastapi, uvicorn, google-generativeai)
    └── .env.example              # Modelo de variáveis de ambiente
```

---

## 🛠️ Pré-requisitos

Certifique-se de possuir instalado em sua máquina:
* **Node.js** (v18 ou superior) & `npm`
* **Rust** & **Cargo** (necessários para compilar o Tauri)
* **Python** (3.10 ou superior) com `pip`

---

## 🚀 Como Executar

### 1. Clonar o repositório
```bash
git clone https://github.com/Ed7-gamedev/TerminalAI.git
cd terminal-ai
```

### 2. Configurar o backend
Navegue até o diretório backend, configure o ambiente virtual e instale as dependências:
```bash
cd backend
python -m venv .venv

# No Windows (PowerShell):
.venv\Scripts\Activate.ps1
# No Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

#### Configurando a API Key do Gemini:
Crie um arquivo `.env` dentro da pasta `backend` com base no `.env.example`:
```env
GEMINI_API_KEY=sua_chave_do_google_gemini_aqui
```
*Obtenha sua chave gratuita no [Google AI Studio](https://aistudio.google.com/app/apikey).*

### 3. Configurar o frontend
Volte para a raiz do projeto e instale as dependências do Node:
```bash
cd ..
npm install
```

### 4. Executar em modo Desenvolvimento
Para rodar a aplicação em modo de desenvolvimento (o Tauri abrirá a janela desktop e iniciará automaticamente o servidor Python):
```bash
npm run tauri dev
```

---

## ⌨️ Scripts Disponíveis

Na raiz do projeto, você pode rodar os seguintes comandos:

| Comando | Descrição |
|---|---|
| `npm run dev` | Inicia o servidor Vite local para desenvolvimento do frontend no navegador. |
| `npm run dev:backend` | Inicia o servidor FastAPI localmente no endereço `http://127.0.0.1:8000`. |
| `npm run all` | Inicia concorrentemente o frontend (Vite) e o backend (FastAPI) no console. |
| `npm run tauri dev` | Inicia o ambiente integrado desktop compilando e gerenciando o backend. |
| `npm run build` | Compila o frontend React com TypeScript em código otimizado de produção. |

---

## 🗺️ Progresso do Projeto & Roadmap

### 🏁 Fase 1: Estabilização (Concluída)
- [x] Criação do `backend/requirements.txt`
- [x] Restrição e correção de CORS para conexões de origem exclusiva do Tauri
- [x] Inicialização e encerramento automatizados do backend Python pela camada Rust no ciclo do app
- [x] Tratamento de erros de conexão com banner de status interativo na UI
- [x] Correção do layout (implementação de CSS Grid dinâmico e flexbox)
- [x] Timeout de execução no backend e no frontend
- [x] Suporte a `Ctrl+C` para interrupção de entrada
- [x] Temas visuais dinâmicos via CSS Variables

### 🏗️ Fase 2: Refatoração de Código (Próxima)
- [ ] Modularização do `App.tsx` em componentes focados
- [ ] Criação de hooks especializados (`useTerminal`, `useAgent`)
- [ ] Migração do tráfego HTTP para invokes nativos do Tauri em Rust (Opção A da arquitetura)

### 🤖 Fase 3: Evolução do Agente
- [ ] Streaming de texto nas respostas do Gemini (UX mais fluida)
- [ ] Histórico estendido e persistência de chats locais
- [ ] Auto-execução guiada de comandos com consentimento prévio do usuário

---

## 📄 Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.
