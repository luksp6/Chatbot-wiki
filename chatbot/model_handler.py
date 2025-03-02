from constants import COLLECTION_NAME, LLM_NAME, K, CHAIN_TYPE, TEMPERATURE, MAX_TOKENS, PROMPT
from aux_classes import QueryRequest
from data_handler import db_client, embedding_model

import weaviate
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

def init_model():
    global LLM
    LLM = OllamaLLM(model=LLM_NAME, streaming=True, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)

def weaviate_retriever(query, top_k=K):
    query_embedding = embedding_model.encode(query)

    results = db_client.query.get(COLLECTION_NAME, ["title", "content", "source"]) \
        .with_near_vector(query_embedding.tolist()) \
        .with_limit(top_k) \
        .do()

    retrieved_docs = []
    for doc in results.get("data", {}).get("Get", {}).get(COLLECTION_NAME, []):
        retrieved_docs.append({
            "page_content": doc["content"],
            "metadata": {"source": doc["source"]}
        })
    
    return retrieved_docs

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