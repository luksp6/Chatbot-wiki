from dotenv import load_dotenv
import os

# Construir la ruta al archivo .env
ENV_PATH = os.path.join(os.getcwd(), ".env")

def load_environment_variables():
    """Carga las variables de entorno desde el archivo .env."""
    load_dotenv(ENV_PATH, override=True)  # Cargar las variables y sobrescribir las existentes

    global REPO_NAME, GITHUB_TOKEN, REPO_OWNER, DB_PATH, COLLECTION_NAME, MODEL_NAME
    global MAX_BATCH_SIZE, CHUNK_SIZE, CHUNK_OVERLAP, LLM_NAME, WEBHOOK_ROUTE, PORT, PROMPT

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

# Cargar variables al inicio
load_environment_variables()