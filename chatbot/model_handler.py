from constants import DB_PATH, COLLECTION_NAME, LLM_NAME, MODEL_NAME, K, CHAIN_TYPE, TEMPERATURE, MAX_TOKENS, PROMPT
from aux_classes import QueryRequest
from data_handler import embeddings

from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

def init_model():
    global LLM, vectorstore, retriever
    LLM = OllamaLLM(model=LLM_NAME, streaming=True, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings, collection_name=COLLECTION_NAME)
    retriever = vectorstore.as_retriever(search_kwargs={'k': K})

init_model()

def get_response(request: QueryRequest):
    try:
        prompt = PromptTemplate(template=PROMPT, input_variables=['context', 'question'])
        qa = RetrievalQA.from_chain_type(
            llm=LLM, 
            chain_type=CHAIN_TYPE, 
            retriever=retriever, 
            return_source_documents=True, 
            chain_type_kwargs={"prompt": prompt}
        )
        sources = set()
        for chunk in qa.stream({"query": request.query}):
            for doc in chunk.get("source_documents", []):
                sources.add(doc.metadata.get("source", "Desconocido"))
            yield chunk["result"]
        if sources:
            yield f"\nFuentes: {', '.join(sources)}"
    except Exception as e:
        print(f"Error en la generación del stream: {e}")
        yield "Error interno en el servidor. Intenta de nuevo más tarde."