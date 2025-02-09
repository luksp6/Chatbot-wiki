from dotenv import load_dotenv
import os

# Obtener el directorio padre
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Construir la ruta al archivo .env en el directorio padre
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Cargar el archivo .env desde la ruta correcta
load_dotenv(ENV_PATH)

REPO_NAME = os.getenv('REPO_NAME', 'FS-WIKI-prueba-')
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
DB_PATH = os.getenv('DB_PATH', 'wiki_db')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'wiki_db')
MODEL_NAME = os.getenv('MODEL_NAME', 'sentence-transformers/all-mpnet-base-v2')
MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', 166))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 500))
LLM_NAME = os.getenv('LLM_NAME', 'llama3.2')
WEBHOOK_ROUTE = os.getenv('WEBHOOK_ROUTE')
PORT = int(os.getenv('CHATBOT_PORT', 6000))
PROMPT = os.getenv('PROMPT', """Usa la siguiente información para responder a la pregunta del usuario.
    Si no sabes la respuesta, simplemente di que no lo sabes, no intentes inventar una respuesta.

    Contexto: {context}
    Pregunta: {question}

    Solo devuelve la respuesta útil a continuación y nada más. Responde siempre en español.

    Respuesta útil:
    """)