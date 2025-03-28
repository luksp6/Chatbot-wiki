from aux_classes import QueryRequest, GitHubWebhookData

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import os
from http.client import HTTPException
import warnings
warnings.filterwarnings("ignore")

const = Constants_manager()
app = FastAPI()
docs = Documents_manager()
db = DB_manager()
llm = LLM_manager()

const.add_observer(docs)
const.add_observer(db)
const.add_observer(llm)

@app.get("/")
def root():
    return {"message": "Servidor del Chatbot activo 🚀"}

@app.post("/query")
def query_db(request: QueryRequest):
    # Verificar si la base de datos vectorial existe
    if not db.exists():
        raise HTTPException(status_code=500, detail="La base de datos no existe. Indexa los documentos primero.")

    return StreamingResponse(llm.get_response(request), media_type="text/plain")

@app.post(WEBHOOK_ROUTE)
def update_db(data: GitHubWebhookData):
    """Maneja los eventos del webhook de GitHub."""
    if data.ref == "refs/heads/main":
        print("Cambio detectado en la rama principal. Actualizando...")
        try:
            docs.update_repo()
            db.update_vectors()
            llm.start()
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
        docs.update_repo()
        db.delete_database()
        db.build_database()
        llm.start()
        return {"status": "success", "message": "Modelo recargado."}
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return {"status": "error", "message": str(e)}, 500