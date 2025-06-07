import requests
import json
from typing import Dict, List, Optional

class OllamaClient:
    """Cliente para interactuar con Ollama y Llama 3.2"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama3.2:latest"
    
    def is_available(self) -> bool:
        """Verificar si Ollama está disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_models(self) -> List[Dict]:
        """Obtener lista de modelos disponibles"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            return []
        except:
            return []
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """Enviar mensaje al modelo y obtener respuesta"""
        try:
            payload = {
                "model": self.model,
                "messages": [],
                "stream": False
            }
            
            # Agregar prompt del sistema si se proporciona
            if system_prompt:
                payload["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Agregar mensaje del usuario
            payload["messages"].append({
                "role": "user",
                "content": message
            })
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return "Error: La solicitud tardó demasiado tiempo."
        except Exception as e:
            return f"Error al comunicarse con Ollama: {str(e)}"
    
    def stream_chat(self, message: str, system_prompt: Optional[str] = None):
        """Chat con streaming de respuesta"""
        try:
            payload = {
                "model": self.model,
                "messages": [],
                "stream": True
            }
            
            if system_prompt:
                payload["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })
            
            payload["messages"].append({
                "role": "user",
                "content": message
            })
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=60
            )
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            yield f"Error: {str(e)}"
