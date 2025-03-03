import shutil
from constants import DB_PATH, COLLECTION_NAME, EMBEDDING_NAME, MAX_BATCH_SIZE, CHUNK_SIZE, CHUNK_OVERLAP
from data_handler import load_documents, get_repo_docs

import os
import chromadb.api

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
import warnings
warnings.filterwarnings("ignore")

def init_db():
    global db, embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_NAME)
    db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings, collection_name=COLLECTION_NAME)

def get_docs_chunked(documents):
    return RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP).split_documents(documents)

def update_vectors():
    """Actualiza la base de datos vectorial en Chroma detectando archivos nuevos, eliminados y modificados."""
    print("Actualizando vectores en Chroma...")
    existing_docs = {metadata["source"]: metadata.get("hash", "") for metadata in db.get()["metadatas"]}
    repo_docs = get_repo_docs()

    # Archivos eliminados
    deleted_files = set(existing_docs) - set(repo_docs)
    if deleted_files:
        print(f"Eliminando {len(deleted_files)} documentos obsoletos...")
        db.delete(list(deleted_files))

    # Archivos modificados o nuevos
    modified_files = [filename for filename, file_hash in repo_docs.items()
                      if filename not in existing_docs or existing_docs[filename] != file_hash]
      
    if modified_files:
        print(f"Eliminando {len(modified_files)} documentos modificados antes de reindexarlos...")
        db.delete(where={"source": {"$in": modified_files}})
        print(f"{len(modified_files)} documentos obsoletos eliminados.")

    updated_documents = load_documents(modified_files)

    # Reindexar archivos nuevos o modificados
    if updated_documents:
        print(f"Indexando {len(updated_documents)} documentos nuevos o modificados...")
        docs_chunked = get_docs_chunked(updated_documents)

        for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
            db.add_documents(docs_chunked[i: i + MAX_BATCH_SIZE])
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
    init_db()

    documents = load_documents()
    if not documents:
        print("No se encontraron documentos Markdown en el repositorio.")

    docs_chunked = get_docs_chunked(documents)
    for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
        db.add_documents(docs_chunked[i : i + MAX_BATCH_SIZE])
        print(f"Insertado batch {i // MAX_BATCH_SIZE + 1}/{(len(docs_chunked) // MAX_BATCH_SIZE) + 1}")

    print(f"Base de datos reconstruida con {len(docs_chunked)} fragmentos.")