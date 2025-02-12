import shutil
from constants import REPO_NAME, GITHUB_TOKEN, REPO_OWNER, DB_PATH, COLLECTION_NAME, MODEL_NAME, MAX_BATCH_SIZE, CHUNK_SIZE, CHUNK_OVERLAP

import os
import subprocess
import re
import hashlib
import json
import chromadb.api
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import warnings
warnings.filterwarnings("ignore")

embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings, collection_name=COLLECTION_NAME)

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

def load_markdown(filepath):
    """Carga un archivo Markdown y retorna su contenido"""
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def extract_title(md_content):
    """Extrae el título del documento desde el YAML Front Matter o el primer encabezado."""
    title = None
    yaml_title_match = re.search(r"^title:\s*(.*)", md_content, re.MULTILINE)
    if yaml_title_match:
        title = yaml_title_match.group(1).strip()    
    return title

def extract_text(md_content):
    """Extrae solo el texto principal del archivo Markdown sin formato adicional."""
    # Eliminar metadatos YAML (encabezado del archivo Markdown)
    md_content = re.sub(r"^---.*?---\s*", '', md_content, flags=re.DOTALL)
    # Eliminar imagenes
    text_content = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)
    # Eliminar encabezados de tablas
    text_content = re.sub(r'\*\*.*?\*\*', '', text_content)
     # Eliminar <br /> (etiqueta HTML de salto de línea)
    text_content = re.sub(r'<br\s*/?>', '', text_content)    
    # Eliminar #
    text_content = re.sub(r'\#', '', text_content)    
    # Eliminar |
    text_content = re.sub(r'\|', '', text_content)
    # Eliminar las ocurrencias de ---
    text_content = re.sub(r'-', '', text_content)
    # Limpiar espacios extras y saltos de línea innecesarios
    text_content = re.sub(r'\n+', ' ', text_content)  # Reemplazar saltos de línea múltiples por un espacio
    text_content = re.sub(r'\s{2,}', ' ', text_content)  # Reemplazar múltiples espacios por un solo espacio
    # Eliminar espacios al inicio y al final
    text_content = text_content.strip()
    return text_content

def extract_tables(md_content):
    """Extrae las tablas en Markdown conservando su estructura."""
    tables = []
    matches = re.findall(r"(\|.*?\|(?:\n\|.*?\|)*)", md_content)
    for match in matches:
        rows = [row.strip() for row in match.split("\n") if row.strip()]
        tables.append(rows)
    return tables

def process_markdown_to_json(filepath):
    """Convierte un archivo Markdown a JSON estructurado."""
    content = load_markdown(filepath)
    title = extract_title(content)
    main_text = extract_text(content)
    tables = extract_tables(content)

    # Construir el diccionario final
    json_data = {
        title: main_text,
        "tables": tables
    }

    # Guardar el archivo JSON
    os.makedirs("processed_files", exist_ok=True)
    json_filename = os.path.splitext(os.path.basename(filepath))[0] + ".json"
    json_filepath = os.path.join("processed_files", json_filename)
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    return json_data

def load_documents():
    """Carga y preprocesa todos los documentos Markdown del repositorio con sus hashes."""
    print("Cargando documentos...")
    repo_path = get_repo_path()
    documents = []

    for filename in os.listdir(repo_path):
        if filename.endswith(".md"):
            filepath = os.path.join(repo_path, filename)
            file_hash = get_file_hash(filepath)
            content = json.dumps(process_markdown_to_json(filepath), ensure_ascii=False, indent=4)
            documents.append(Document(page_content=content, metadata={"source": filename, "hash": file_hash}))

    return documents

def get_docs_chunked(documents):
    return RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP).split_documents(documents)

def update_vectors():
    """Actualiza la base de datos vectorial en Chroma detectando archivos nuevos, eliminados y modificados."""
    print("Actualizando vectores en Chroma...")

    existing_docs = {metadata["source"]: metadata.get("hash", "") for metadata in db.get()["metadatas"]}
    repo_docs = {doc.metadata["source"]: doc.metadata["hash"] for doc in load_documents()}

    # Archivos eliminados
    deleted_files = set(existing_docs) - set(repo_docs)
    if deleted_files:
        print(f"Eliminando {len(deleted_files)} documentos obsoletos...")
        db.delete(list(deleted_files))

    # Archivos modificados o nuevos
    updated_documents = []
    modified_files = []

    for filename, file_hash in repo_docs.items():
        if filename not in existing_docs or existing_docs[filename] != file_hash:
            modified_files.append(filename)
            filepath = os.path.join(get_repo_path(), filename)
            text = load_documents(filepath)
            updated_documents.append(Document(page_content=text, metadata={"source": filename, "hash": file_hash}))

    # Eliminar las versiones antiguas de los archivos modificados antes de reindexarlos
    if modified_files:
        print(f"🔄 Eliminando {len(modified_files)} archivos modificados antes de reindexarlos...")
        db.delete(modified_files)

    # Reindexar archivos nuevos o modificados
    if updated_documents:
        print(f"Indexando {len(updated_documents)} documentos nuevos o modificados...")
        docs_chunked = get_docs_chunked(updated_documents)

        for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
            db.add_documents(docs_chunked[i : i + MAX_BATCH_SIZE])
            print(f"Insertado batch {i // MAX_BATCH_SIZE + 1}/{(len(docs_chunked) // MAX_BATCH_SIZE) + 1}")

    db.persist()
    print("Vectores actualizados correctamente.")

def rebuild_database():
    global db
    """Elimina y reconstruye completamente la base de datos de Chroma."""
    print("Reconstruyendo base de datos desde cero...")

    chromadb.api.client.SharedSystemClient.clear_system_cache()
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        print("Base de datos eliminada.")
    
    # Asegurarse de que el directorio de persistencia se crea nuevamente
    os.makedirs(DB_PATH, exist_ok=True)
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings, collection_name=COLLECTION_NAME)

    documents = load_documents()
    if not documents:
        print("No se encontraron documentos Markdown en el repositorio.")

    docs_chunked = get_docs_chunked(documents)
    for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
        db.add_documents(docs_chunked[i : i + MAX_BATCH_SIZE])
        print(f"Insertado batch {i // MAX_BATCH_SIZE + 1}/{(len(docs_chunked) // MAX_BATCH_SIZE) + 1}")

    db.persist()
    print(f"Base de datos reconstruida con {len(docs_chunked)} fragmentos.")