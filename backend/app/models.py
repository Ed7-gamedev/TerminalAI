from pydantic import BaseModel

class CommandRequest(BaseModel):
    cmd: str


class ShellRequest(BaseModel):
    shell: str


class AiChatRequest(BaseModel):
    message: str
    shell: str = "powershell"
    cwd: str = "~"
    last_output: str = ""          # últimas linhas do output do terminal
    # histórico de mensagens anteriores (alternado user/ai)
    history: list[str] = []
    model: str = "gemini-2.5-flash"  # Modelo selecionado


class AiChatResponse(BaseModel):
    reply: str
    commands: list[str] = []       # comandos sugeridos extraídos do markdown
    error: str = ""
    active_model: str = ""         # Modelo que efetivamente respondeu (pode ser fallback)


class SyncSessionRequest(BaseModel):
    shell: str
    cwd: str


class RiskRequest(BaseModel):
    cmd: str
    model: str = "gemini-2.5-flash"


class RiskResponse(BaseModel):
    risk_level: str       # "low" | "medium" | "high" | "critical"
    impact: list[str]
    requires_approval: bool

