from aux_classes import QueryRequest, GitHubWebhookData

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import os
from http.client import HTTPException
import asyncio
import warnings
warnings.filterwarnings("ignore")

app = FastAPI()
chatbot = Chatbot()

@app.get("/")
async def root():
    return {"message": "Servidor del Chatbot activo 🚀"}

@app.post("/query")
async def query_db(request: QueryRequest):
    # Verificar si la base de datos vectorial existe
    if not chatbot.db.exists():
        raise HTTPException(status_code=500, detail="La base de datos no existe. Indexa los documentos primero.")

    return StreamingResponse(await chatbot.chat(request), media_type="text/plain")

@app.post(WEBHOOK_ROUTE)
async def update_db(data: GitHubWebhookData):
    """Maneja los eventos del webhook de GitHub."""
    if data.ref == "refs/heads/main":
        print("Cambio detectado en la rama principal. Actualizando...")
        try:
            await chatbot.update_documents()
            return {"status": "success", "message": "Repositorio y vectores actualizados."}
        except Exception as e:
            print(f"Error al actualizar: {e}")
            return {"status": "error", "message": str(e)}, 500
    return {"status": "ignored", "message": "Evento no relevante."}

@app.get("/change-model-variables")
async def change_variables():
    print("Variables de entorno del modelo modificadas. Actualizando...")
    try:
        await chatbot.reload()
        return {"status": "success", "message": "Modelo recargado."}
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return {"status": "error", "message": str(e)}, 500