from constants import DB_PATH, PORT, WEBHOOK_ROUTE
from aux_classes import QueryRequest, GitHubWebhookData
from model_handler import get_response
from data_handler import update_data

from fastapi import FastAPI
import os
import uvicorn
from http.client import HTTPException
import warnings
warnings.filterwarnings("ignore")


# Iniciar FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Servidor del Chatbot activo 🚀"}

@app.post("/query")
def query_db(request: QueryRequest):
    # Verificar si la base de datos vectorial existe
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="La base de datos no existe. Indexa los documentos primero.")

    response = get_response(request)

    return {"query": request.query, "results": response}

@app.post(WEBHOOK_ROUTE)
async def update_db(data: GitHubWebhookData):
    """Maneja los eventos del webhook de GitHub."""
    if data.ref == "refs/heads/main":
        print("Cambio detectado en la rama principal. Actualizando...")
        try:
            await update_data()
            return {"status": "success", "message": "Repositorio y vectores actualizados."}
        except Exception as e:
            print(f"Error al actualizar: {e}")
            return {"status": "error", "message": str(e)}, 500
    return {"status": "ignored", "message": "Evento no relevante."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)