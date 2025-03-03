from constants import REPO_NAME, GITHUB_TOKEN, REPO_OWNER

import os
import subprocess
import hashlib
import re
import pdfplumber
from markdown_pdf import MarkdownPdf, Section
from langchain.schema import Document

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

def load_md(filepath):
    """Carga un archivo json y retorna su contenido"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def extract_title(md_content):
    title_match = re.search(r"title:\s*(.+)", md_content)
    title = title_match.group(1) if title_match else "Título Desconocido"
    return title

def parse_to_pdf(filename, md_content):
    extract_title(md_content)
    pdf = MarkdownPdf()
    pdf.meta["title"] = extract_title(md_content)
    pdf.add_section(Section(md_content, toc=False))
    pdf.save(os.path.splitext(filename)[0] + ".pdf")
    return pdf

def pdf_to_text(pdf):
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    return text

def process_repo_files(process_content=False, selected_files=None):
    """
    Recorre el repositorio y devuelve un diccionario con nombres de archivos y sus hashes.
    Si process_content=True, también devuelve el contenido procesado de los archivos.
    """
    repo_path = get_repo_path()
    repo_docs = {}
    documents = []

    if selected_files is None:
        selected_files = os.listdir(repo_path)

    for filename in selected_files:
        if filename.endswith(".md"):
            filepath = os.path.join(repo_path, filename)
            file_hash = get_file_hash(filepath)
            repo_docs[filename] = file_hash  # Guardamos el nombre del archivo y su hash

            if process_content:  # Solo procesamos contenido si es necesario
                content = parse_to_pdf(filename, load_md(filepath))
                content = pdf_to_text(content)
                documents.append(Document(page_content=content, metadata={"source": filename, "hash": file_hash}))

    return (repo_docs, documents) if process_content else repo_docs


def load_documents(files=None):
    print("Cargando documentos...")
    _, documents = process_repo_files(process_content=True, selected_files=files)
    return documents

def get_repo_docs():
    return process_repo_files(process_content=False)