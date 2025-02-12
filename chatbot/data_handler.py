import shutil
from constants import REPO_NAME, GITHUB_TOKEN, REPO_OWNER, DB_PATH, COLLECTION_NAME, MODEL_NAME, MAX_BATCH_SIZE, CHUNK_SIZE, CHUNK_OVERLAP

import os
import subprocess
import re
import hashlib
import chromadb.api
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from markdown import markdown
from bs4 import BeautifulSoup
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

def load_markdown(filepath):
    """
    Carga un archivo Markdown y aplica preprocesamiento para mejorar la calidad del texto.
    - Elimina YAML Front Matter
    - Convierte Markdown a texto limpio
    - Conserva encabezados y estructura semántica
    - Elimina imágenes y enlaces sin texto descriptivo
    """
    
    # Cargar el archivo Markdown
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    # Eliminar YAML Front Matter (encabezado entre '---')
    content = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)

    # Convertir Markdown a HTML
    html_content = markdown(content)

    # Parsear HTML con BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Eliminar imágenes y enlaces sin texto descriptivo
    for img in soup.find_all("img"):
        img.decompose()  # Elimina la etiqueta <img>

    for a in soup.find_all("a"):
        if not a.text.strip():  # Si el enlace no tiene texto visible, eliminarlo
            a.decompose()

    # Convertir tablas a texto plano (manteniendo formato)
    for table in soup.find_all("table"):
        rows = []
        for row in table.find_all("tr"):
            cols = [col.get_text(strip=True) for col in row.find_all(["td", "th"])]
            rows.append(" | ".join(cols))
        table_text = "\n".join(rows)
        table.replace_with(table_text)  # Reemplazar la tabla con texto formateado

    # Extraer el texto limpio manteniendo estructura
    text_content = soup.get_text(separator="\n")

    # Eliminar espacios en blanco innecesarios
    text_content = re.sub(r'\n\s*\n', '\n', text_content)  # Quita líneas en blanco extras

    return text_content

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

def load_documents_from_repo():
    """Carga y preprocesa todos los documentos Markdown del repositorio con sus hashes."""
    repo_path = get_repo_path()
    documents = []

    for filename in os.listdir(repo_path):
        if filename.endswith(".md"):
            filepath = os.path.join(repo_path, filename)
            file_hash = get_file_hash(filepath)
            text = load_markdown(filepath)
            documents.append(Document(page_content=text, metadata={"source": filename, "hash": file_hash}))

    return documents

def get_docs_chunked(documents):
    return RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP).split_documents(documents)

def update_vectors():
    """Actualiza la base de datos vectorial en Chroma detectando archivos nuevos, eliminados y modificados."""
    print("Actualizando vectores en Chroma...")

    existing_docs = {metadata["source"]: metadata.get("hash", "") for metadata in db.get()["metadatas"]}
    repo_docs = {doc.metadata["source"]: doc.metadata["hash"] for doc in load_documents_from_repo()}

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
            text = load_markdown(filepath)
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

    documents = load_documents_from_repo()
    if not documents:
        print("No se encontraron documentos Markdown en el repositorio.")

    docs_chunked = get_docs_chunked(documents)
    for i in range(0, len(docs_chunked), MAX_BATCH_SIZE):
        db.add_documents(docs_chunked[i : i + MAX_BATCH_SIZE])
        print(f"Insertado batch {i // MAX_BATCH_SIZE + 1}/{(len(docs_chunked) // MAX_BATCH_SIZE) + 1}")

    db.persist()
    print(f"Base de datos reconstruida con {len(docs_chunked)} fragmentos.")