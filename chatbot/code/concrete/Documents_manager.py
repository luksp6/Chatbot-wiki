from abstract.Singleton.Singleton import Singleton
from abstract.Observer.Observer import Observer

from concrete.Constants_manager import Constants_manager

from git import Repo
from git.remote import Remote
import os
import asyncio
import hashlib
import json
import warnings
warnings.filterwarnings("ignore")

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class Documents_manager(Singleton, Observer):

    def __init__(self):
        self._repo_path = None
        self._repo_url = None
        self._repo = None
        self._remote = None

    async def start(self):
        const = Constants_manager.get_instance(Constants_manager)
        self._repo_path = os.path.join(os.getcwd(), const.RESOURCES_PATH, const.REPO_NAME)
        self._repo_url = f"https://{const.GITHUB_TOKEN}:x-oauth-basic@github.com/{const.REPO_OWNER}/{const.REPO_NAME}.git"
        await asyncio.to_thread(self.update_repo)
         

    async def notify(self):
        os.rmdir(self._repo_path)
        self._repo_path = None
        self._repo_url = None
        self._repo = None
        self._remote = None
        await self.start()

    def _get_file_hash(self, filepath):
        """Calcula un hash MD5 del contenido de un archivo."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def update_repo(self):
        """Actualiza el repositorio local con los últimos cambios de GitHub."""
        print("Actualizando el repositorio desde GitHub...")
        const = Constants_manager.get_instance(Constants_manager)
        if os.path.exists(os.path.join(self._repo_path, ".git")):
            print(f"El repositorio {const.REPO_NAME} ya existe. Haciendo pull...")
            self._repo = Repo(self._repo_path)
            if self._remote is None:
                self._remote = Remote(self._repo, "origin")
                self._remote.set_url(self._repo_url)
            self._remote.pull()
        else:
            print(f"El repositorio {const.REPO_NAME} no existe. Clonando el repositorio...")
            self._repo = Repo.clone_from(self._repo_url, self._repo_path)
            self._remote = Remote(self._repo, const.REPO_NAME)


    def _open_json(self, filepath):
        """Carga un archivo json y retorna su contenido"""
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)


    def load_documents(self):
        """Carga y preprocesa todos los documentos repositorio con sus hashes."""
        print("Cargando documentos...")
        documents = []
        for filename in os.listdir(self._repo_path):
            if filename.endswith(".json"):
                doc = self.get_document(filename)
                documents.append(doc)
        if not documents:
            print("No se encontraron documentos Json en el repositorio.")
        return documents


    def get_document(self, filename):
        filepath = os.path.join(self._repo_path, filename)
        file_hash = self._get_file_hash(filepath)
        content = json.dumps(self._open_json(filepath), ensure_ascii=False, indent=4)
        return Document(page_content=content, metadata={"source": filename, "hash": file_hash})


    def get_docs_chunked(self, documents):
        const = Constants_manager.get_instance(Constants_manager)
        return RecursiveCharacterTextSplitter(chunk_size=const.CHUNK_SIZE, chunk_overlap=const.CHUNK_OVERLAP).split_documents(documents)
