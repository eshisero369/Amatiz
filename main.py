from supabase_client import supabase
import json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Ámatis IA")

CONFIG_PATH = Path("amatis_config.json")
MEMORY_PATH = Path("amatis_memory.json")


class ChatRequest(BaseModel):
    message: str
    user: str = "Carlos Iván"


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"ia_name": "Ámatis"}


def load_memory():
    if MEMORY_PATH.exists():
        with open(MEMORY_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"memories": []}


def save_memory(memory):
    with open(MEMORY_PATH, "w", encoding="utf-8") as file:
        json.dump(memory, file, ensure_ascii=False, indent=2)


def should_remember(text: str):
    important_words = [
        "quiero",
        "proyecto",
        "negocio",
        "recordar",
        "idea",
        "robot",
        "estrategia",
        "objetivo",
        "plan"
    ]
    return any(word in text.lower() for word in important_words)


def create_response(user_message: str, config, memory):
    ia_name = config.get("ia_name", "Ámatis")
    identity = config.get(
        "identity_phrase",
        "Soy Ámatis, una IA estratégica."
    )

    memories_text = ""
    if memory["memories"]:
        last_memories = memory["memories"][-5:]
        memories_text = "Recuerdo esto de ti: " + "; ".join(
            item["content"] for item in last_memories
        )

    response = f"""
{identity}

Analizando tu mensaje:
"{user_message}"

Respuesta estratégica:
Voy a responder con lógica, visión práctica y criterio estratégico. 
{memories_text}

Mi recomendación inicial es ordenar la idea, separar lo importante de lo secundario y convertirlo en un plan accionable.
"""

    return response.strip()


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Ámatis está activa en Render."
    }


@app.post("/chat")
def chat(request: ChatRequest):

supabase.table("Memory").insert({
    "user": request.user,
    "content": request.message
}).execute()

    config = load_config()
    memory = load_memory()

    if should_remember(request.message):
        memory["memories"].append({
            "user": request.user,
            "content": request.message,
            "created_at": datetime.now().isoformat(),
            "importance": "medium"
        })
        save_memory(memory)

    response = create_response(request.message, config, memory)

    return {
        "ia": config.get("ia_name", "Ámatis"),
        "user": request.user,
        "response": response,
        "memory_saved": should_remember(request.message)
}
