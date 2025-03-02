from constants import REPO_NAME, GITHUB_TOKEN, REPO_OWNER, DB_PATH, COLLECTION_NAME, EMBEDDING_NAME, MAX_BATCH_SIZE, CHUNK_SIZE, CHUNK_OVERLAP

import shutil
import os
import subprocess
import hashlib
import json
import weaviate
from weaviate.embedded import EmbeddedOptions
from sentence_transformers import SentenceTransformer

import warnings
warnings.filterwarnings("ignore")

def init_db():
    global db_client, embedding_model, schema
    db_client = weaviate.Client(embedded_options=EmbeddedOptions())
    embedding_model = SentenceTransformer(EMBEDDING_NAME)
    schema = {
        "classes": [{
            "class": COLLECTION_NAME,
            "vectorizer": "none",
            "properties": [
                {"name": "title", "dataType": ["text"]},
                {"name": "content", "dataType": ["text"]},
                {"name": "tables", "dataType": ["text[]"]},
                {"name": "hash", "dataType": ["text"]},
                {"name": "source", "dataType": ["text"]}
            ]
        }]
    }
    db_client.schema.delete_all()
    db_client.schema.create(schema)

def get_repo_path():
    """Devuelve la ruta local del repositorio."""
    return os.path.join(os.getcwd(), REPO_NAME)

def get_file_hash(filepath):
    """Calcula un hash MD5 del contenido de un archivo."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def update_repo():
    """Actualiza el repositorio local con los últimos cambios de GitHub."""
    print("Actualizando el repositorio desde GitHub...")

    repo_url = f"https://{GITHUB_TOKEN}:x-oauth-basic@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    repo_path = get_repo_path()


    if not os.path.isdir(repo_path):
        print(f"El directorio {repo_path} no existe. Clonando el repositorio...")
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
    else:
        print(f"El directorio {repo_path} ya existe. Haciendo pull...")
        subprocess.run(["git", "-C", repo_path, "pull"], check=True)

    # Configurar la URL remota por si cambia el token
    subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", repo_url], check=True)

def load_json(filepath):
    """Carga un archivo json y retorna su contenido"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_documents():
    """Carga y preprocesa todos los documentos repositorio con sus hashes."""
    print("Cargando documentos...")
    repo_path = get_repo_path()
    documents = []

    for filename in os.listdir(repo_path):
        if filename.endswith(".json"):
            filepath = os.path.join(repo_path, filename)
            doc = load_json(filepath)
            documents.append(doc)

    return documents

def update_vectors():
    """Actualiza la base de datos detectando archivos nuevos, eliminados y modificados."""
    print("Actualizando vectores en Weaviate...")

    documents = load_documents()

    existing_docs = {}
    results = db_client.query.get(COLLECTION_NAME, ["source", "hash"]).do()
    for doc in results.get("data", {}).get("Get", {}).get(COLLECTION_NAME, []):
        existing_docs[doc["source"]] = doc["hash"]

    deleted_files = set(existing_docs) - {doc["source"] for doc in documents}
    if deleted_files:
        for source in deleted_files:
            db_client.batch.delete_objects_by_filter(COLLECTION_NAME, f'source == "{source}"')

    with db_client.batch(batch_size=MAX_BATCH_SIZE) as batch:
        for doc in documents:
            if doc["source"] not in existing_docs or existing_docs[doc["source"]] != doc["hash"]:
                embedding = embedding_model.encode(doc["title"] + " ".join(doc["content"] + " ".join(doc["tables"])))
                
                batch.add_data_object(
                    properties=doc,
                    vector=embedding.tolist(),
                    class_name=COLLECTION_NAME
                )

    print("Vectores actualizados correctamente.")

def rebuild_database():
    """Elimina y reconstruye completamente la base de datos."""
    print("Reconstruyendo base de datos...")

    db_client.schema.delete_all()
    init_db()
    update_vectors()

    print(f"Base de datos reconstruida.")