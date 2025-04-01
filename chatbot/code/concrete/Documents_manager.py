from abstract.Singleton.Singleton import Singleton
from abstract.Observer.Observer import Observer

from concrete.Constants_manager import Constants_manager

import shutil
import os
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import warnings
warnings.filterwarnings("ignore")

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class Documents_manager(Singleton, Observer):

    async def notify(self):
        await self.update_repo()

    def _get_repo_path(self):
        """Devuelve la ruta local del repositorio."""
        const = Constants_manager.get_instance(Constants_manager)
        return os.path.join(os.getcwd(), const.RESOURCES_PATH, const.REPO_NAME)

    def _get_file_hash(self, filepath):
        """Calcula un hash MD5 del contenido de un archivo."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    async def update_repo(self):
        """Actualiza el repositorio local con los últimos cambios de GitHub."""
        print("Actualizando el repositorio desde GitHub...")

        const = Constants_manager.get_instance(Constants_manager)
        repo_url = f"https://{const.GITHUB_TOKEN}:x-oauth-basic@github.com/{const.REPO_OWNER}/{const.REPO_NAME}.git"
        repo_path = self._get_repo_path()

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()

        if not os.path.isdir(repo_path):
            print(f"El directorio {repo_path} no existe. Clonando el repositorio...")
            await loop.run_in_executor(executor, subprocess.run, ["git", "clone", repo_url, repo_path], None, None, True)

        else:
            print(f"El directorio {repo_path} ya existe. Haciendo pull...")
            await loop.run_in_executor(executor, subprocess.run, ["git", "-C", repo_path, "pull"], None, None, True)


        # Configurar la URL remota por si cambia el token
        await loop.run_in_executor(executor, subprocess.run, ["git", "-C", repo_path, "remote", "set-url", "origin", repo_url], None, None, True)

    def _open_json(self, filepath):
        """Carga un archivo json y retorna su contenido"""
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)

    def load_documents(self):
        """Carga y preprocesa todos los documentos repositorio con sus hashes."""
        print("Cargando documentos...")
        documents = []
        for filename in self._get_repo_path():
            if filename.endswith(".json"):
                doc = self.get_document(filename)
                documents.append(doc)
        if not documents:
            print("No se encontraron documentos Json en el repositorio.")
        return documents

    def get_document(self, filename):
        repo_path = self._get_repo_path()
        filepath = os.path.join(repo_path, filename)
        file_hash = self._get_file_hash(filepath)
        content = json.dumps(self._open_json(filepath), ensure_ascii=False, indent=4)
        return Document(page_content=content, metadata={"source": filename, "hash": file_hash})

    def get_docs_chunked(self, documents):
        const = Constants_manager.get_instance(Constants_manager)
        return RecursiveCharacterTextSplitter(chunk_size=const.CHUNK_SIZE, chunk_overlap=const.CHUNK_OVERLAP).split_documents(documents)
