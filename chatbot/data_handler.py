import shutil
from constants import REPO_NAME, GITHUB_TOKEN, REPO_OWNER, DB_PATH, COLLECTION_NAME, EMBEDDING_NAME, MAX_BATCH_SIZE, CHUNK_SIZE, CHUNK_OVERLAP

import os
import subprocess
import hashlib
import json
import chromadb.api

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import warnings
warnings.filterwarnings("ignore")

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_NAME)
db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings, collection_name=COLLECTION_NAME)

def get_repo_path():
    """Devuelve la ruta local del repositorio."""
    return os.path.join(os.getcwd(), REPO_NAME)

def get_file_hash(filepath):
    """Calcula un hash MD5 del contenido de un archivo."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def update_repo():
    """Actualiza el repositorio local con los últimos cambios de GitHub."""
    print("Actualizando el repositorio desde GitHub...")

    repo_url = f"https://{GITHUB_TOKEN}:x-oauth-basic@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    repo_path = get_repo_path()


    if not os.path.isdir(repo_path):
        print(f"El directorio {repo_path} no existe. Clonando el repositorio...")
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
    else:
        print(f"El directorio {repo_path} ya existe. Haciendo pull...")
        subprocess.run(["git", "-C", repo_path, "pull"], check=True)

    # Configurar la URL remota por si cambia el token
    subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", repo_url], check=True)

def load_json(filepath):
    """Carga un archivo json y retorna su contenido"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_documents():
    """Carga y preprocesa todos los documentos repositorio con sus hashes."""
    print("Cargando documentos...")
    repo_path = get_repo_path()
    documents = []

    for filename in os.listdir(repo_path):
        if filename.endswith(".json"):
            filepath = os.path.join(repo_path, filename)
            file_hash = get_file_hash(filepath)
            content = json.dumps(load_json(filepath), ensure_ascii=False, indent=4)
            #content = load_json(filepath)
            documents.append(Document(page_content=content, metadata={"source": filename, "hash": file_hash}))

    return documents

def get_docs_chunked(documents):
    return RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP).split_documents(documents)

def update_vectors():
    """Actualiza la base de datos vectorial en Chroma detectando archivos nuevos, eliminados y modificados."""
    print("Actualizando vectores en Chroma...")

    existing_docs = {metadata["source"]: metadata.get("hash", "") for metadata in db.get()["metadatas"]}
    repo_docs = {doc.metadata["source"]: doc.metadata["hash"] for doc in load_documents()}

    # Archivos eliminados
    deleted_files = set(existing_docs) - set(repo_docs)
    if deleted_files:
        print(f"Eliminando {len(deleted_files)} documentos obsoletos...")
        db.delete(list(deleted_files))

    # Archivos modificados o nuevos
    updated_documents = []
    modified_files = []
    
    repo_path = get_repo_path()

    for filename, file_hash in repo_docs.items():
        if filename not in existing_docs or existing_docs[filename] != file_hash:
            modified_files.append(filename)
            filepath = os.path.join(repo_path, filename)
            content = json.dumps(load_json(filepath), ensure_ascii=False, indent=4)
            updated_documents.append(Document(page_content=content, metadata={"source": filename, "hash": file_hash}))

    # Eliminar las versiones antiguas de los archivos modificados antes de reindexarlos
    if modified_files:
        print(f"Eliminando {len(modified_files)} documentos modificados antes de reindexarlos...")
        for file in modified_files:
            db.delete(where={"source": file})
        print(f"{len(modified_files)} documentos obsoletos eliminados.")

    # Reindexar archivos nuevos o modificados
    if updated_documents:
        print(f"Indexando {len(updated_documents)} documentos nuevos o modificados...")
        docs_chunked = get_docs_chunked(updated_documents)

        for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
            db.add_documents(docs_chunked[i : i + MAX_BATCH_SIZE])
            print(f"Insertado batch {i // MAX_BATCH_SIZE + 1}/{(len(docs_chunked) // MAX_BATCH_SIZE) + 1}")

    print("Vectores actualizados correctamente.")

def rebuild_database():
    global db, embeddings
    """Elimina y reconstruye completamente la base de datos de Chroma."""
    print("Reconstruyendo base de datos desde cero...")

    chromadb.api.client.SharedSystemClient.clear_system_cache()
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        print("Base de datos eliminada.")
    
    # Asegurarse de que el directorio de persistencia se crea nuevamente
    os.makedirs(DB_PATH, exist_ok=True)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_NAME)
    db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings, collection_name=COLLECTION_NAME)

    documents = load_documents()
    if not documents:
        print("No se encontraron documentos Markdown en el repositorio.")

    docs_chunked = get_docs_chunked(documents)
    for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
        db.add_documents(docs_chunked[i : i + MAX_BATCH_SIZE])
        print(f"Insertado batch {i // MAX_BATCH_SIZE + 1}/{(len(docs_chunked) // MAX_BATCH_SIZE) + 1}")

    print(f"Base de datos reconstruida con {len(docs_chunked)} fragmentos.")