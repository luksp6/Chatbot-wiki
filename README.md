# Chatbot Wiki

Este proyecto consiste en un chatbot basado en inteligencia artificial capaz de responder preguntas utilizando una base de conocimientos. Además, cuenta con un servicio de webhook que permite actualizar la base de datos del chatbot automáticamente cuando se detectan cambios en un repositorio de GitHub.

## Arquitectura

El proyecto se compone de dos partes principales:

1. **Chatbot (Dockerizado)**: Aplicación principal que gestiona las consultas y respuestas. Posee tres endpoints
   * POST "/query": Endpoint para consultas. Recibe como parámetro un diccionario con la forma { "query": <CONSULTA> }.
   * POST "/update-db": Endpoint encargado de actualizar la base de conocimientos del chatbot. Captura la notificación del GitHub Webhook y actualiza la copia local del repositorio, procesa la información y actualiza los vectores de la base de datos.
   * GET "/change-model-variables": Endpoint encargado de recargar las constantes del modelo definidas en el archivo .env. Elimina por completo la base de datos y la reconstruye en base a los nuevos parámetros. Es necesaria su invocación luego de realizar alguna modificación en el archivo .env.
3. **Webhook (Ejecutado localmente)**: Servicio encargado de recibir eventos desde GitHub y actualizar la base de conocimientos del chatbot mediante su endpoint dedicado.

---

## Instalación y ejecución

### 1️⃣ **Desplegar el Chatbot (Dockerizado)**
El chatbot está contenido en el directorio `chatbot` y se ejecuta dentro de un contenedor Docker. Para construir y ejecutar el servicio, sigue estos pasos en el directorio raíz del proyecto:

```sh
# Construir la imagen del chatbot
docker-compose build

# Levantar los contenedores
docker-compose up -d
```

> ⚠️ **Nota**: Asegúrate de que Docker y Docker Compose estén instalados en tu sistema antes de ejecutar estos comandos.


### 2️⃣ **Ejecutar el Webhook (Localmente)**
El webhook, que se encuentra en el directorio `webhook`, debe ejecutarse manualmente en la máquina local. Sigue estos pasos:

```sh
# Ir al directorio del webhook
cd webhook

# Crear un entorno virtual
python -m venv venv

# Activar el entorno virtual
# En Windows
venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate

# Instalar las dependencias
pip install -r requirements.txt

# Ejecutar el servicio del webhook
python -m __main__
```

Con el Webhook ejecutando, se debe colocar su dirección en el repositorio que contenga los archivos .md que conforman la wiki.

> **Nota**: Asegúrate de tener Python 3.10 instalado en tu sistema antes de ejecutar estos pasos.

---

## Variables de entorno

El proyecto utiliza un archivo `.env` en el directorio raíz para gestionar variables de entorno. Asegúrate de configurarlas correctamente antes de ejecutar el chatbot y el webhook.

Ejemplo de `.env`:
```ini
CHATBOT_URL=http://localhost
CHATBOT_PORT=6000
WEBHOOK_PORT=5000
WEBHOOK_ROUTE=/update-db
REPO_NAME=FS-WIKI-prueba-
GITHUB_TOKEN=tu_token_de_github
REPO_OWNER=luksp6
```

Las variables REPO_NAME, GITHUB_TOKEN y REPO_OWNER deben actualizarse con los datos del repositorio de producción de la wiki. 


