from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import shell, ai

app = FastAPI(title="Terminal-AI Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Terminal-AI API v0.2.0"}

# Incluindo os routers separados
app.include_router(shell.router)
app.include_router(ai.router)
