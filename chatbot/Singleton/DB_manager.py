import shutil
from constants import DB_PATH, COLLECTION_NAME, EMBEDDING_NAME, MAX_BATCH_SIZE

import os
import subprocess
import hashlib
import json
import chromadb.api
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import warnings
warnings.filterwarnings("ignore")

class DB_manager(Singleton, Observer):

    _db = None
    _embeddings = None
    _persist_dir = None
    _collection_name = None

    def notify(self):
        self._delete_database()
        self._build_database()

    def connect(self):
        if self._db is None:
                    self._persist_dir = DB_PATH
                    self._collection_name = COLLECTION_NAME
                    self._embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_NAME)
                    self._db = Chroma(persist_directory=self._persist_dir, embedding_function=self._embeddings, collection_name=self._collection_name)
    
    def __init__(self):
        self.connect()

    def get_retriever(self, k):
        return self._db.as_retriever(search_kwargs={'k': k})

    def exists():
        return os.path.exists(self._persist_dir)

    def delete_vector(self, delete_query):
        self._db.delete(delete_query)

    def add_vector(self, add_query):
        self._db.add_documents(add_query)

    def update_vectors(self):
    """Actualiza la base de datos vectorial en Chroma detectando archivos nuevos, eliminados y modificados."""
        print("Actualizando vectores en Chroma...")

        doc_manager = Documents_manager()
        existing_docs = {metadata["source"]: metadata.get("hash", "") for metadata in self._db.get()["metadatas"]}
        repo_docs = {doc.metadata["source"]: doc.metadata["hash"] for doc in doc_manager.load_documents()}

        # Archivos eliminados
        deleted_files = set(existing_docs) - set(repo_docs)
        if deleted_files:
            print(f"Eliminando {len(deleted_files)} documentos obsoletos...")
            self.delete_vector(list(deleted_files))

        # Archivos modificados o nuevos
        updated_documents = []
        modified_files = []
        for filename, file_hash in repo_docs.items():
            if filename not in existing_docs or existing_docs[filename] != file_hash:
                modified_files.append(filename)
                doc = doc_manager.get_document(filename)
                updated_documents.append(doc)

        # Eliminar las versiones antiguas de los archivos modificados antes de reindexarlos
        if modified_files:
            print(f"Eliminando {len(modified_files)} documentos modificados antes de reindexarlos...")
            for file in modified_files:
                self.delete_vector(where={"source": file})
            print(f"{len(modified_files)} documentos obsoletos eliminados.")

        # Reindexar archivos nuevos o modificados
        if updated_documents:
            print(f"Indexando {len(updated_documents)} documentos nuevos o modificados...")
            docs_chunked = doc_manager.get_docs_chunked(updated_documents)

            for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
                self.add_vector(docs_chunked[i : i + MAX_BATCH_SIZE])
                print(f"Insertado batch {i // MAX_BATCH_SIZE + 1}/{(len(docs_chunked) // MAX_BATCH_SIZE) + 1}")

        print("Vectores actualizados correctamente.")

    def _delete_database(self):
    """Elimina completamente la base de datos de Chroma."""
        print("Reconstruyendo base de datos desde cero...")
        self._db = None
        self._embeddings = None
        chromadb.api.client.SharedSystemClient.clear_system_cache()
        if os.path.exists(DB_PATH):
            shutil.rmtree(DB_PATH)
            print("Base de datos eliminada.")
        else:
            print("La base de datos no existe.")

    def _build_database(self):
    """Construye completamente la base de datos de Chroma."""
        print("Construyendo base de datos desde cero...")

        # Asegurarse de que el directorio de persistencia se crea nuevamente
        os.makedirs(DB_PATH, exist_ok=True)
        self.connect()

        doc_manager = Documents_manager()
        documents = doc_manager.load_documents()

        docs_chunked = doc_manager.get_docs_chunked(documents)
        for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
            self._db.add_vector(docs_chunked[i : i + MAX_BATCH_SIZE])
            print(f"Insertado batch {i // MAX_BATCH_SIZE + 1}/{(len(docs_chunked) // MAX_BATCH_SIZE) + 1}")

        print(f"Base de datos construida con {len(docs_chunked)} fragmentos.")