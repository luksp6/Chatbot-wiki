from constants import LLM_NAME, K, CHAIN_TYPE, TEMPERATURE, MAX_TOKENS, PROMPT
from aux_classes import QueryRequest
from data_handler import weaviate_retriever

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

def init_model():
    global LLM
    LLM = OllamaLLM(model=LLM_NAME, streaming=True, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)

def get_response(request: QueryRequest):
    try:
        prompt = PromptTemplate(template=PROMPT, input_variables=['context', 'question'])
        retrieved_docs = weaviate_retriever(request.query, K)

        context = "\n".join([doc["page_content"] for doc in retrieved_docs])
        sources = set(doc["metadata"]["source"] for doc in retrieved_docs)

        qa = RetrievalQA.from_chain_type(
            llm=LLM,
            chain_type=CHAIN_TYPE,
            retriever=None,
            return_source_documents=False,
            chain_type_kwargs={"prompt": prompt}
        )

        for chunk in qa.stream({"context": context, "question": request.query}):
            yield chunk["result"]
        if sources:
            yield f"\nFuentes: {', '.join(sources)}"
    except Exception as e:
        print(f"Error en la generación del stream: {e}")
        yield "Error interno en el servidor. Intenta de nuevo más tarde."