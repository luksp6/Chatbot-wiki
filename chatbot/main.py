from constants import load_environment_variables, DB_PATH, PORT, WEBHOOK_ROUTE
from aux_classes import QueryRequest, GitHubWebhookData
from model_handler import get_response, init_model
from data_handler import update_repo, update_vectors, rebuild_database

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import os
from http.client import HTTPException
import warnings
warnings.filterwarnings("ignore")


app = FastAPI()
init_model()

@app.get("/")
def root():
    return {"message": "Servidor del Chatbot activo 🚀"}

@app.post("/query")
def query_db(request: QueryRequest):
    # Verificar si la base de datos vectorial existe
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="La base de datos no existe. Indexa los documentos primero.")

    return StreamingResponse(get_response(request), media_type="text/plain")

@app.post(WEBHOOK_ROUTE)
def update_db(data: GitHubWebhookData):
    """Maneja los eventos del webhook de GitHub."""
    if data.ref == "refs/heads/main":
        print("Cambio detectado en la rama principal. Actualizando...")
        try:
            update_repo()
            update_vectors()
            init_model()
            return {"status": "success", "message": "Repositorio y vectores actualizados."}
        except Exception as e:
            print(f"Error al actualizar: {e}")
            return {"status": "error", "message": str(e)}, 500
    return {"status": "ignored", "message": "Evento no relevante."}

@app.get("/change-model-variables")
def change_variables():
    print("Variables de entorno del modelo modificadas. Actualizando...")
    try:
        load_environment_variables()
        update_repo()
        rebuild_database()
        init_model()
        return {"status": "success", "message": "Modelo recargado."}
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return {"status": "error", "message": str(e)}, 500