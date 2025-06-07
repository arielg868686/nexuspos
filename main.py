from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from ollama_client import OllamaClient
import json
from typing import Optional

app = FastAPI(title="Asistente AI Llama 3.2", version="1.0.0")

# Inicializar cliente de Ollama
ollama = OllamaClient()

# Configurar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatMessage(BaseModel):
    message: str
    system_prompt: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    status: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Servir la página principal"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Verificar el estado del servicio"""
    ollama_status = ollama.is_available()
    models = ollama.get_models() if ollama_status else []
    
    return {
        "status": "healthy" if ollama_status else "ollama_unavailable",
        "ollama_available": ollama_status,
        "models": models,
        "current_model": ollama.model
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """Endpoint para chat normal (sin streaming)"""
    try:
        if not ollama.is_available():
            raise HTTPException(status_code=503, detail="Ollama no está disponible")
        
        response = ollama.chat(
            message=chat_message.message,
            system_prompt=chat_message.system_prompt
        )
        
        return ChatResponse(response=response, status="success")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream_endpoint(chat_message: ChatMessage):
    """Endpoint para chat con streaming"""
    try:
        if not ollama.is_available():
            raise HTTPException(status_code=503, detail="Ollama no está disponible")
        
        def generate_response():
            for chunk in ollama.stream_chat(
                message=chat_message.message,
                system_prompt=chat_message.system_prompt
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: {\"done\": true}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_models():
    """Obtener modelos disponibles"""
    try:
        models = ollama.get_models()
        return {"models": models, "current": ollama.model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Asistente AI Llama 3.2...")
    print("📍 Interfaz web: http://localhost:8000")
    print("📋 API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
