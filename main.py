from fastapi.responses import HTMLResponse
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
    mensaje = user_message.lower()

    # 🧠 Memoria reciente
    recuerdos = ""
    if memory["memories"]:
        ultimos = memory["memories"][-3:]
        recuerdos = "Recuerdo reciente: " + "; ".join([m["content"] for m in ultimos])

    # 🎯 Respuestas inteligentes por contexto
    if "hola" in mensaje:
        return f"Hola. Soy Ámatis. {recuerdos} ¿Qué necesitas resolver?"

    elif "negocio" in mensaje or "dinero" in mensaje:
        return f"""
Análisis rápido:

1. Revisa ingresos vs gastos
2. Identifica dónde estás perdiendo dinero
3. Mejora ventas o reduce costos

{recuerdos}

Acción: dime tu situación exacta y te doy un plan.
"""

    elif "idea" in mensaje:
        return f"""
Las ideas no valen nada sin ejecución.

Paso 1: valida si alguien pagaría por eso  
Paso 2: prueba rápido  
Paso 3: ajusta según resultados  

{recuerdos}
"""

    elif "problema" in mensaje:
        return f"""
Todo problema se resuelve así:

1. Define el problema real  
2. Elimina lo irrelevante  
3. Ejecuta una solución simple  

{recuerdos}
"""

    else:
        return f"""
Estoy analizando tu mensaje:

"{user_message}"

{recuerdos}

No voy a darte una respuesta genérica.

Explícame mejor el contexto y te doy una respuesta más precisa.
"""
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

@app.get("/",response_class=HTMLResponse)
def home():
    return HTMLResponse(content="""
    <html>
    <body style='font-family:Arial; max-width:600px; margin:40px auto;'>
        <h1>Ámatis IA</h1>
        <textarea id='msg' style='width:100%; height:100px;' placeholder='Escribe tu mensaje...'></textarea>
        <br><br>
        <button onclick='send()'>Enviar</button>
        <pre id='res'></pre>

        <script>
        async function send() {
            const message = document.getElementById('msg').value;
            const r = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message, user: 'Carlos Iván'})
            });
            const data = await r.json();
            document.getElementById('res').textContent = JSON.stringify(data, null, 2);
        }
        </script>
    </body>
    </html>
    """)


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
