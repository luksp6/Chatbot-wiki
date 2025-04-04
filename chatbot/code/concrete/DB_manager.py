import shutil
from abstract.Singleton.Singleton import Singleton
from abstract.Observer.Observer import Observer
from abstract.Composite.Service import Service

from concrete.Documents_manager import Documents_manager
from concrete.Constants_manager import Constants_manager

import os
import asyncio

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class DB_manager(Singleton, Observer, Service):

    def __init__(self):
        """Inicializa la base de datos y la conexión a Chroma."""
        Service.__init__(self)
        self._embeddings = None
        self._persist_dir = None
        self._collection_name = None

    async def notify(self):
        await self.disconnect()
        await self._delete_database()
        await self.connect()
        await self.wait_for_connection()
        await self._build_database()

    async def _connect(self):
        if self._service is None:
            const = Constants_manager.get_instance(Constants_manager)
            self._persist_dir = os.path.join(os.getcwd(), const.RESOURCES_PATH, const.DB_PATH)
            self._collection_name = const.COLLECTION_NAME
            self._embeddings = await asyncio.to_thread(
                lambda: HuggingFaceEmbeddings(model_name=const.EMBEDDING_NAME, show_progress=True)
            )
            self._service = await asyncio.to_thread(
                lambda: Chroma(
                    persist_directory=self._persist_dir,
                    embedding_function=self._embeddings,
                    collection_name=self._collection_name
                )
            )
            self._connected.set()

    async def _disconnect(self):
        """Desconecta la base de datos liberando los recursos."""
        if self._service:
            self._service = None
            self._embeddings = None
            self._connected.clear()

    def get_retriever(self, k):
        return self._service.as_retriever(search_kwargs={'k': k})

    def get_embeddings(self):
        return self._embeddings

    def exists(self):
        return os.path.exists(self._persist_dir)

    def update_vectors(self):
        """Actualiza la base de datos vectorial en Chroma detectando archivos nuevos, eliminados y modificados."""
        print("Actualizando vectores en Chroma...")

        doc_manager = Documents_manager.get_instance(Documents_manager)
        existing_docs = {metadata["source"]: metadata.get("hash", "") for metadata in self._service.get()["metadatas"]}
        repo_docs = {doc.metadata["source"]: doc.metadata["hash"] for doc in doc_manager.load_documents()}

        # Archivos eliminados
        deleted_files = set(existing_docs) - set(repo_docs)
        if deleted_files:
            print(f"Eliminando {len(deleted_files)} documentos obsoletos...")
            self._service.delete(list(deleted_files))

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
                self._service.delete(where={"source": file})
            print(f"{len(modified_files)} documentos obsoletos eliminados.")
        
        # Reindexar archivos nuevos o modificados
        if updated_documents:
            print(f"Indexando {len(updated_documents)} documentos nuevos o modificados...")
            docs_chunked = doc_manager.get_docs_chunked(updated_documents)
            self.batched_insert(docs_chunked)

        print("Vectores actualizados correctamente.")

    async def _delete_database(self):
        """Elimina completamente la base de datos de Chroma."""
        print("Eliminando base de datos...")
        if self.exists():
            await asyncio.to_thread(shutil.rmtree, self._persist_dir)
            print("Base de datos eliminada.")
        else:
            print("La base de datos no existe.")

    async def _build_database(self):
        """Construye completamente la base de datos de Chroma."""
        print("Construyendo base de datos...")
        const = Constants_manager.get_instance(Constants_manager)

        # Asegurarse de que el directorio de persistencia se crea nuevamente
        os.makedirs(const.DB_PATH, exist_ok=True)

        doc_manager = Documents_manager.get_instance(Documents_manager)
        documents = await asyncio.to_thread(doc_manager.load_documents)

        docs_chunked = await asyncio.to_thread(doc_manager.get_docs_chunked, documents)
        asyncio.to_thread(self.batched_insert, docs_chunked)

        print(f"Base de datos construida con {len(docs_chunked)} fragmentos.")

    def batched_insert(self, documents):
        const = Constants_manager.get_instance(Constants_manager)
        for i in range(0, len(documents), const.MAX_BATCH_SIZE):
            self._service.add_documents(documents[i : i + const.MAX_BATCH_SIZE])
            print(f"Insertado batch {i // const.MAX_BATCH_SIZE + 1}/{(len(documents) // const.MAX_BATCH_SIZE) + 1}")