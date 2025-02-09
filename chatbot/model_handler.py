from constants import DB_PATH, COLLECTION_NAME, LLM_NAME, MODEL_NAME, PROMPT
from aux_classes import QueryRequest

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# Inicializar el modelo LLM
LLM = OllamaLLM(model=LLM_NAME)  # Cambia el modelo según disponibilidad

def get_response(request: QueryRequest):
    # Cargar la base de datos vectorial
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=HuggingFaceEmbeddings(model_name=MODEL_NAME), collection_name=COLLECTION_NAME)
    retriever = vectorstore.as_retriever(search_kwargs={'k': request.top_k})

    prompt = PromptTemplate(template=PROMPT, input_variables=['context', 'question'])

    # Configurar la cadena QA
    qa = RetrievalQA.from_chain_type(llm=LLM, chain_type="stuff", retriever=retriever, return_source_documents=True, chain_type_kwargs={"prompt": prompt})

    # Obtener la respuesta del modelo
    response = qa.invoke({"query": request.query})

    return response