from constants import REPO_NAME, GITHUB_TOKEN, REPO_OWNER, DB_PATH, MODEL_NAME, MAX_BATCH_SIZE, CHUNK_SIZE, CHUNK_OVERLAP

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

    repo_url = f"https://{GITHUB_TOKEN}:x-oauth-basic@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    repo_path = os.path.join(os.getcwd(), REPO_NAME)


    if not os.path.isdir(repo_path):
        print(f"El directorio {repo_path} no existe. Clonando el repositorio...")
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
    else:
        print(f"El directorio {repo_path} ya existe. Haciendo pull...")
        subprocess.run(["git", "-C", repo_path, "pull"], check=True)


    # Configurar la URL remota por si cambia el token
    subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", repo_url], check=True)

def update_vectors():
    """Actualiza solo los archivos modificados en la base de datos de Chroma."""
    print("Actualizando vectores en Chroma (solo cambios detectados)...")

    # Cargar documentos actuales en la base de datos
    db = Chroma(persist_directory=DB_PATH, embedding_function=HuggingFaceEmbeddings(model_name=MODEL_NAME), collection_name="db_wiki")

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

def update_data():
    update_repo()
    update_vectors()