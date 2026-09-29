import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from server.app import config
from server.app.registry import registry

app = FastAPI(
    title="AI Duo Multi-Model Gateway & Application Image",
    description="Adaptive multi-model gateway supporting OpenAI, Nous Hermes, Ollama, Groq, and Pollinations",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for OpenAI compatibility
class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = ""
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o-mini"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
    max_tokens: Optional[int] = None

@app.get("/healthz")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "aiduo-gateway",
        "version": "2.0.0",
        "providers": registry.get_providers_status()
    }

@app.get("/v1/models")
async def list_models():
    return registry.list_models()

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    adapter, model_cfg = registry.resolve(req.model)
    msg_dicts = [m.model_dump(exclude_none=True) for m in req.messages]

    extra_kwargs = {
        "temperature": req.temperature,
        "tools": req.tools,
        "tool_choice": req.tool_choice,
        "max_tokens": req.max_tokens
    }

    if req.stream:
        async def event_generator():
            async for chunk in adapter.stream(msg_dicts, model_cfg, **extra_kwargs):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        result = await adapter.complete(msg_dicts, model_cfg, **extra_kwargs)
        return JSONResponse(content=result)

@app.get("/api/hud/stats")
async def hud_stats():
    providers_status = registry.get_providers_status()
    agents = []
    if config.AGENTS_FILE.exists():
        try:
            with open(config.AGENTS_FILE, "r", encoding="utf-8") as f:
                agents_data = json.load(f)
                agents = agents_data.get("agents", {})
        except Exception:
            pass

    return {
        "version": "2.0.0",
        "providers": providers_status,
        "agents": agents,
        "models": registry.list_models()
    }

@app.get("/api/agents")
async def get_agents():
    if config.AGENTS_FILE.exists():
        try:
            with open(config.AGENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"default_agent": "developer", "agents": {}}

# Static route helper for index files
@app.get("/chat")
async def serve_chat():
    chat_index = config.AI_CHAT_DIR / "index.html"
    if chat_index.exists():
        return FileResponse(chat_index)
    raise HTTPException(status_code=404, detail="AI Chat UI not found")

@app.get("/hud")
async def serve_hud():
    hud_index = config.HUD_DIR / "index.html"
    if hud_index.exists():
        return FileResponse(hud_index)
    raise HTTPException(status_code=404, detail="HUD UI not found")

# Mount static asset directories
if config.AI_CHAT_DIR.exists():
    app.mount("/chat", StaticFiles(directory=str(config.AI_CHAT_DIR), html=True), name="chat_static")

if config.HUD_DIR.exists():
    app.mount("/hud", StaticFiles(directory=str(config.HUD_DIR), html=True), name="hud_static")

if config.PORTAL_DIR.exists():
    app.mount("/", StaticFiles(directory=str(config.PORTAL_DIR), html=True), name="portal_static")
