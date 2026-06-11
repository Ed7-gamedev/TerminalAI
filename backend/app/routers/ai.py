import os
import re
import asyncio
from fastapi import APIRouter
import google.generativeai as genai
from app import config, models

router = APIRouter()

@router.get("/ai/status")
def ai_status():
    """Verifica se a integração com IA está disponível (Gemini ou Groq)."""
    has_gemini = config._AI_READY and config._GEMINI_MODEL is not None
    has_groq = config._GROQ_CLIENT is not None
    available = has_gemini or has_groq
    
    # Modelo padrão ou ativo
    default_model = None
    if has_gemini:
        default_model = "gemini-2.5-flash"
    elif has_groq:
        groq_models = [m["key"] for m in config.SUPPORTED_MODELS if m["provider"] == "groq"]
        if groq_models:
            default_model = groq_models[0]
            
    reason = None
    if not available:
        gemini_missing = not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here"
        groq_missing = not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here"
        
        if gemini_missing and groq_missing:
            reason = "API keys do Gemini e Groq não configuradas. Edita backend/.env e reinicia."
        else:
            reason = "Instala as dependências necessárias (groq, google-generativeai, python-dotenv)."
            
    return {
        "available": available,
        "model": default_model,
        "reason": reason,
    }


@router.get("/ai/models")
def get_models():
    """Retorna a lista de modelos suportados e sua disponibilidade."""
    available_models = []
    for m in config.SUPPORTED_MODELS:
        available = False
        if m["provider"] == "gemini":
            available = config._AI_READY and config._GEMINI_MODEL is not None
        elif m["provider"] == "groq":
            available = config._GROQ_CLIENT is not None
        
        available_models.append({
            "key": m["key"],
            "name": m["name"],
            "provider": m["provider"],
            "available": available
        })
    return {"models": available_models}

@router.post("/ai/chat")
async def ai_chat(request: models.AiChatRequest):
    """
    Envia uma mensagem ao agente IA com contexto do terminal.
    Suporta múltiplos modelos e fallback automático caso o selecionado falhe.
    Retorna resposta em texto + lista de comandos sugeridos extraídos.
    """
    has_gemini = config._AI_READY and config._GEMINI_MODEL is not None
    has_groq = config._GROQ_CLIENT is not None
    if not (has_gemini or has_groq):
        return models.AiChatResponse(
            reply="⚠️ Nenhum Agente IA configurado.\n\nEdita `backend/.env` com a tua GEMINI_API_KEY ou GROQ_API_KEY e reinicia o backend.",
            commands=[],
            error="AI_NOT_CONFIGURED",
        )

    # ── Detectar contexto do projeto ────────────────────────────
    project_techs = []
    cwd_to_check = request.cwd
    if cwd_to_check == "~":
        cwd_to_check = os.path.expanduser("~")

    if os.path.isdir(cwd_to_check):
        try:
            files = os.listdir(cwd_to_check)
            if "package.json" in files:
                project_techs.append("Node.js (package.json)")
            if "requirements.txt" in files or "pyproject.toml" in files or "Pipfile" in files:
                project_techs.append("Python (requirements.txt/pyproject.toml)")
            if "Cargo.toml" in files:
                project_techs.append("Rust (Cargo.toml)")
            if "docker-compose.yml" in files or "docker-compose.yaml" in files or "Dockerfile" in files:
                project_techs.append("Docker (docker-compose/Dockerfile)")
            if "pom.xml" in files or "build.gradle" in files:
                project_techs.append("Java (Maven/Gradle)")
            if ".git" in files or os.path.exists(os.path.join(cwd_to_check, ".git")):
                project_techs.append("Git Repository")
        except Exception:
            pass

    context_tech_str = ""
    if project_techs:
        context_tech_str = f"\n- Ecossistema do Projeto: {', '.join(project_techs)}"

    # ── Monta o system prompt com contexto do terminal ──────────
    shell_name = config.SHELL_CONFIGS.get(
        request.shell, {}).get("name", request.shell)
    last_out_section = ""
    if request.last_output.strip():
        # Trunca para não explodir o contexto
        truncated = request.last_output[-1500:].strip()
        last_out_section = f"\n\nÚltimo output do terminal:\n```\n{truncated}\n```"

    system_prompt = f"""Você é um assistente de terminal especialista e conciso.
Contexto atual:
- Shell: {shell_name}
- Diretório: {request.cwd}{context_tech_str}{last_out_section}

Regras:
1. Responda SEMPRE em português do Brasil.
2. Seja direto e prático. Priorize exemplos de comandos.
3. Quando sugerir comandos, coloque-os em blocos de código markdown: ```bash ou ```powershell ou ```python etc.
4. Se o utilizador pedir para executar algo, sugira o comando exato no bloco de código.
5. Não repita o contexto de volta ao utilizador.
6. Máximo 300 palavras por resposta.
7. Quando detectar tecnologias de projeto específicas, personalize as sugestões para usar os gerenciadores de pacote ou ferramentas correspondentes (ex: npm, pip, cargo, etc.)."""

    # ── Ordenar modelos por tentativa (Solicitado -> Outros disponíveis) ──
    requested_key = request.model if request.model else "gemini-2.5-flash"
    
    def is_model_available(m):
        if m["provider"] == "gemini":
            return config._AI_READY and config._GEMINI_MODEL is not None
        elif m["provider"] == "groq":
            return config._GROQ_CLIENT is not None
        return False

    requested_model_entry = next((m for m in config.SUPPORTED_MODELS if m["key"] == requested_key), None)
    
    try_models = []
    if requested_model_entry and is_model_available(requested_model_entry):
        try_models.append(requested_model_entry)
        
    for m in config.SUPPORTED_MODELS:
        if m["key"] != requested_key and is_model_available(m):
            try_models.append(m)
            
    if not try_models:
        return models.AiChatResponse(
            reply="⚠️ Nenhum modelo de IA disponível. Verifique as chaves no backend/.env.",
            commands=[],
            error="NO_MODELS_AVAILABLE",
        )

    # ── Execução em Cascata (Fallback) ───────────────────────────
    reply_text = None
    active_model_key = None
    last_error_msg = ""
    
    for model_entry in try_models:
        model_name = model_entry["key"]
        provider = model_entry["provider"]
        try:
            print(f"[AI Chat] Tentando modelo {model_name} ({provider})...")
            if provider == "gemini":
                # Configura histórico para Gemini
                history_parts = []
                for i, msg in enumerate(request.history[-10:]):
                    role = "user" if i % 2 == 0 else "model"
                    history_parts.append({"role": role, "parts": [msg]})
                
                model_obj = config._GEMINI_MODEL
                if model_obj is None:
                    model_obj = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config=genai.GenerationConfig(
                            temperature=0.4,
                            max_output_tokens=1024,
                        ),
                    )
                
                chat = model_obj.start_chat(history=history_parts)
                if not history_parts:
                    user_msg = f"{system_prompt}\n\n---\n\nUtilizador: {request.message}"
                else:
                    user_msg = request.message
                
                response = await chat.send_message_async(user_msg)
                reply_text = response.text
                
            elif provider == "groq":
                if config._GROQ_CLIENT is None:
                    raise ValueError("Cliente Groq não inicializado")
                
                # Configura histórico para Groq (OpenAI format)
                messages = [{"role": "system", "content": system_prompt}]
                for i, msg in enumerate(request.history[-10:]):
                    role = "user" if i % 2 == 0 else "assistant"
                    messages.append({"role": role, "content": msg})
                messages.append({"role": "user", "content": request.message})
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: config._GROQ_CLIENT.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=0.4,
                        max_tokens=1024,
                    )
                )
                reply_text = response.choices[0].message.content
            
            if reply_text:
                active_model_key = model_name
                print(f"[AI Chat] Sucesso com o modelo {model_name}!")
                break
                
        except Exception as e:
            err_msg = f"Erro no modelo {model_name}: {str(e)}"
            print(f"[AI Chat] {err_msg}")
            last_error_msg = err_msg

    if not reply_text:
        return models.AiChatResponse(
            reply="",
            commands=[],
            error=f"Todos os modelos falharam. Último erro: {last_error_msg}",
        )

    # ── Extrai comandos dos blocos de código markdown ───────────
    code_block_pattern = re.compile(
        r"```(?:bash|sh|powershell|ps1|cmd|python|py|javascript|js|typescript|ts|node)?\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    commands = []
    for match in code_block_pattern.finditer(reply_text):
        block = match.group(1).strip()
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(line)

    return models.AiChatResponse(
        reply=reply_text,
        commands=commands,
        active_model=active_model_key,
    )


@router.post("/ai/check-risk", response_model=models.RiskResponse)
def check_risk(request: models.RiskRequest):
    cmd = request.cmd.strip()
    if not cmd:
        return models.RiskResponse(
            risk_level="low",
            impact=["Comando vazio."],
            requires_approval=False
        )

    cmd_lower = cmd.lower()

    # 1. Regras locais imediatas
    # Risco Crítico
    if any(p in cmd_lower for p in ["rm -rf", "del /f", "rmdir /s", "format ", "mkfs"]):
        return models.RiskResponse(
            risk_level="critical",
            impact=[
                "Exclui arquivos ou diretórios permanentemente.",
                "Pode danificar o sistema operacional ou apagar dados importantes de trabalho."
            ],
            requires_approval=True
        )

    # Risco Alto
    if any(p in cmd_lower for p in ["git reset --hard", "git clean", "git push", "docker compose down", "docker compose rm", "docker rm", "docker kill", "docker rmi"]):
        return models.RiskResponse(
            risk_level="high",
            impact=[
                "Altera o estado do Git (podendo descartar alterações locais não salvas) ou interage com servidores remotos.",
                "Para, remove ou altera containers/imagens Docker ativos."
            ],
            requires_approval=True
        )

    # Risco Médio
    if any(p in cmd_lower for p in ["npm install", "npm run", "pip install", "cargo build", "cargo run", "docker run", "docker compose up"]):
        return models.RiskResponse(
            risk_level="medium",
            impact=[
                "Instala dependências, inicia servidores locais ou executa builds no ambiente.",
                "Pode consumir largura de banda ou CPU temporariamente."
            ],
            requires_approval=True
        )

    # Risco Baixo (Leitura / Navegação / Git local seguro)
    safe_commands = ["ls", "dir", "pwd", "git status", "git branch", "git diff", "git log", "whoami", "hostname", "echo", "cat", "type"]
    is_safe = any(cmd_lower == s or cmd_lower.startswith(s + " ") for s in safe_commands)
    if is_safe:
        return models.RiskResponse(
            risk_level="low",
            impact=["Comando de leitura ou consulta seguro."],
            requires_approval=False
        )

    # 2. IA Fallback para comandos arbitrários se configurada
    available_risk_models = []
    preferred_model = None
    for m in config.SUPPORTED_MODELS:
        is_available = False
        if m["provider"] == "gemini" and config._AI_READY and config._GEMINI_MODEL is not None:
            is_available = True
        elif m["provider"] == "groq" and config._GROQ_CLIENT is not None:
            is_available = True
            
        if is_available:
            if m["key"] == request.model:
                preferred_model = m
            else:
                available_risk_models.append(m)
                
    if preferred_model:
        available_risk_models.insert(0, preferred_model)
        
    for model_entry in available_risk_models:
        model_name = model_entry["key"]
        provider = model_entry["provider"]
        try:
            import json
            prompt = f"""Analise o seguinte comando de terminal e classifique o seu risco de execução local:
Comando: {cmd}

Responda APENAS em formato JSON correspondente ao seguinte esquema:
{{
  "risk_level": "low" | "medium" | "high" | "critical",
  "impact": ["motivo 1", "motivo 2"],
  "requires_approval": true | false
}}

Considere:
- "critical": comandos destrutivos perigosos (exclusão de arquivos cruciais, formatação, etc.).
- "high": comandos que alteram significativamente o estado do git remoto, containers docker importantes ou rede.
- "medium": comandos de escrita ou instalação de pacotes.
- "low": leitura, listagem, navegação (cd) e status."""

            text = None
            if provider == "gemini":
                response = config._GEMINI_MODEL.generate_content(prompt)
                text = response.text.strip()
            elif provider == "groq":
                messages = [
                    {"role": "system", "content": "Você é um classificador de segurança de comandos de terminal. Responda APENAS em formato JSON válido, sem comentários ou explicações extras."},
                    {"role": "user", "content": prompt}
                ]
                response = config._GROQ_CLIENT.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.1,
                )
                text = response.choices[0].message.content.strip()
                
            if text:
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                data = json.loads(text)
                return models.RiskResponse(
                    risk_level=data.get("risk_level", "medium"),
                    impact=data.get("impact", ["Executa o comando no ambiente."]),
                    requires_approval=data.get("requires_approval", True)
                )
        except Exception as e:
            print(f"[Risk Check] Erro com o modelo {model_name}: {e}")
            continue

    # Fallback genérico (Risco Médio por padrão)
    return models.RiskResponse(
        risk_level="medium",
        impact=["Executa o comando no terminal local."],
        requires_approval=True
    )


