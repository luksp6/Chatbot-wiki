from aux_classes import QueryRequest, GitHubWebhookData

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import os
from http.client import HTTPException
import warnings
warnings.filterwarnings("ignore")

app = FastAPI()
chatbot = Chatbot()

@app.get("/")
def root():
    return {"message": "Servidor del Chatbot activo 🚀"}

@app.post("/query")
def query_db(request: QueryRequest):
    # Verificar si la base de datos vectorial existe
    if not chatbot.db.exists():
        raise HTTPException(status_code=500, detail="La base de datos no existe. Indexa los documentos primero.")

    return StreamingResponse(chatbot.chat(request), media_type="text/plain")

@app.post(WEBHOOK_ROUTE)
def update_db(data: GitHubWebhookData):
    """Maneja los eventos del webhook de GitHub."""
    if data.ref == "refs/heads/main":
        print("Cambio detectado en la rama principal. Actualizando...")
        try:
            chatbot.update_documents()
            return {"status": "success", "message": "Repositorio y vectores actualizados."}
        except Exception as e:
            print(f"Error al actualizar: {e}")
            return {"status": "error", "message": str(e)}, 500
    return {"status": "ignored", "message": "Evento no relevante."}

@app.get("/change-model-variables")
def change_variables():
    print("Variables de entorno del modelo modificadas. Actualizando...")
    try:
        chatbot.reload()
        return {"status": "success", "message": "Modelo recargado."}
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return {"status": "error", "message": str(e)}, 500