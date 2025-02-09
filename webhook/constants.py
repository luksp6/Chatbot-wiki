from dotenv import load_dotenv
import os

# Obtener el directorio padre
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Construir la ruta al archivo .env en el directorio padre
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Cargar el archivo .env desde la ruta correcta
load_dotenv(ENV_PATH)

CHATBOT_URL = str(os.getenv('CHATBOT_URL'))
CHATBOT_PORT = int(os.getenv('CHATBOT_PORT', 6000))
WEBHOOK_ROUTE = str(os.getenv('WEBHOOK_ROUTE'))
PORT =  int(os.getenv('WEBHOOK_PORT', 6000))