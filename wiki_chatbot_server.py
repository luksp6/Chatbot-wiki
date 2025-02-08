from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
import uvicorn
import os
import warnings
warnings.filterwarnings("ignore")

REPO_PATH = os.getenv('REPO_PATH', 'FS-WIKI-prueba-')
DB_PATH = os.getenv('DB_PATH', 'wiki_db')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'wiki_db')
MODEL_NAME = os.getenv('MODEL_NAME', 'sentence-transformers/all-mpnet-base-v2')
LLM_NAME = os.getenv('LLM_NAME', 'llama3.2')
MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', 166))
PORT = int(os.getenv('CHATBOT_PORT', 6000))
PROMPT = os.getenv('PROMPT', """Usa la siguiente información para responder a la pregunta del usuario.
    Si no sabes la respuesta, simplemente di que no lo sabes, no intentes inventar una respuesta.

    Contexto: {context}
    Pregunta: {question}

    Solo devuelve la respuesta útil a continuación y nada más. Responde siempre en español.

    Respuesta útil:
    """)

# Cargar embeddings
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

# Iniciar FastAPI
app = FastAPI()

# Inicializar el modelo LLM
LLM = Ollama(model=LLM_NAME)  # Cambia el modelo según disponibilidad

# Modelo de consulta
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3  # Número de respuestas a recuperar

@app.get("/")
def root():
    return {"message": "Servidor del Chatbot activo 🚀"}

@app.post("/query")
def query_db(request: QueryRequest):
    # Verificar si la base de datos vectorial existe
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="La base de datos no existe. Indexa los documentos primero.")

    # Cargar la base de datos vectorial
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings, collection_name=COLLECTION_NAME)
    retriever = vectorstore.as_retriever(search_kwargs={'k': request.top_k})

    prompt = PromptTemplate(template=PROMPT, input_variables=['context', 'question'])

    # Configurar la cadena QA
    qa = RetrievalQA.from_chain_type(llm=LLM, chain_type="stuff", retriever=retriever, return_source_documents=True, chain_type_kwargs={"prompt": prompt})

    # Obtener la respuesta del modelo
    response = qa.invoke({"query": request.query})

    return {"query": request.query, "results": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
