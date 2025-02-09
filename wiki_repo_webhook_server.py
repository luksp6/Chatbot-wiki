from flask import Flask, request, jsonify
import os
import subprocess
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from markdown import markdown
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore")

REPO_NAME = os.getenv('REPO_NAME', 'FS-WIKI-prueba-')
DB_PATH = os.getenv('DB_PATH', 'wiki_db')
MODEL_NAME = os.getenv('MODEL_NAME', 'sentence-transformers/all-mpnet-base-v2')
MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', 166))
PORT = int(os.getenv('WEBHOOK_PORT', 5000))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 500))

app = Flask(__name__)

# Inicializar embeddings
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

def load_markdown(filepath):
    # Cargar y procesar el archivo markdown
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    # Convertir el Markdown a HTML
    html_content = markdown(content)
    
    # Parsear el HTML para que sea más fácil extraer la información
    soup = BeautifulSoup(html_content, 'html.parser')

    # Solo extraemos el texto
    text_content = soup.get_text()
    
    return text_content

def update_repo():
    """Actualiza el repositorio local con los últimos cambios de GitHub."""
    print("Actualizando el repositorio desde GitHub...")
    subprocess.run(["git", "-C", REPO_NAME, "pull"], check=True)

def update_vectors():
    """Actualiza solo los archivos modificados en la base de datos de Chroma."""
    print("Actualizando vectores en Chroma (solo cambios detectados)...")

    # Cargar documentos actuales en la base de datos
    db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings, collection_name="db_wiki")

    existing_docs = {metadata["source"] for metadata in db.get()["metadatas"]}  # Archivos existentes en la DB
    new_docs = set(os.listdir(REPO_NAME))  # Archivos en la carpeta actual

    # Archivos eliminados
    deleted_files = existing_docs - new_docs
    if deleted_files:
        print(f"Eliminando {len(deleted_files)} documentos obsoletos de la base de datos...")
        db.delete([f for f in deleted_files])  # Elimina los documentos

    # Archivos nuevos o modificados
    modified_files = new_docs - existing_docs
    if len(modified_files) > 1:
        print(f"Añadiendo {len(modified_files)} documentos nuevos...")
        documents = []
        for filename in modified_files:
            if filename.endswith(".md"):
                filepath = os.path.join(REPO_NAME, filename)
                text = load_markdown(filepath)                
                doc = Document(page_content=text, metadata={"source": filename})
                documents.append(doc)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        docs_chunked = text_splitter.split_documents(documents)

         # Insertar en lotes para evitar errores de tamaño
        if docs_chunked:
            for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
                batch = docs_chunked[i : i + MAX_BATCH_SIZE]
                db.add_documents(batch)
                print(f"Insertado batch {i // MAX_BATCH_SIZE + 1} de {len(docs_chunked) // MAX_BATCH_SIZE + 1}")

    db.persist()
    print("Vectores actualizados correctamente.")

@app.route("/github-webhook", methods=["POST"])
def github_webhook():
    """Maneja los eventos del webhook de GitHub."""
    data = request.get_json()

    if "ref" in data and data["ref"] == "refs/heads/main":
        print("Cambio detectado en la rama principal. Actualizando...")
        try:
            update_repo()
            update_vectors()
            return jsonify({"status": "success", "message": "Repositorio y vectores actualizados."}), 200
        except Exception as e:
            print(f"Error al actualizar: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        return jsonify({"status": "ignored", "message": "Evento no relevante."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
