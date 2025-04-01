from abstract.Singleton.Singleton import Singleton
from abstract.Observer.Observable import Observable

import os

from dotenv import load_dotenv

class Constants_manager(Singleton, Observable):

    def __init__(self):
        Observable.__init__(self)
        self._env_path = os.path.join(os.getcwd(), ".env")
        self.load_environment_variables()

    def load_environment_variables(self):
        """Carga las variables de entorno desde el archivo .env."""
        if os.path.exists(self._env_path):
            load_dotenv(self._env_path, override=True)

        self.RESOURCES_PATH = os.getenv('RESOURCES_PATH', 'Resources')
        self.REPO_NAME = os.getenv('REPO_NAME', 'FS-WIKI-JSON')
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
        self.REPO_OWNER = os.getenv("REPO_OWNER", "")
        self.DB_PATH = os.getenv('DB_PATH', 'wiki_db')
        self.COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'wiki_db')
        self.EMBEDDING_NAME = os.getenv('EMBEDDING_NAME', 'sentence-transformers/all-mpnet-base-v2')
        self.K = int(os.getenv("K", "3"))
        self.CHAIN_TYPE = os.getenv('CHAIN_TYPE')
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
        self.MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))
        self.MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "166"))
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "500"))
        self.LLM_NAME = os.getenv('LLM_NAME', 'llama3.2')
        self.WEBHOOK_ROUTE = os.getenv('WEBHOOK_ROUTE', "/update-db")
        self.PORT = int(os.getenv('CHATBOT_PORT', "6000"))
        self.PROMPT = os.getenv('PROMPT', """Usa la siguiente información para responder a la pregunta del usuario.
            Si no sabes la respuesta, simplemente di que no lo sabes, no intentes inventar una respuesta.

            Contexto: {context}
            Pregunta: {question}

            Solo devuelve la respuesta útil a continuación y nada más. Responde siempre en español.

            Respuesta útil:
            """)
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.CACHE_THRESHOLD = float(os.getenv("CACHE_THRESHOLD", "0.2"))
        self.CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
        self.notify_observers()