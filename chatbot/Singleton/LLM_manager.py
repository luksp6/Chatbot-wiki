from constants import LLM_NAME, K, CHAIN_TYPE, TEMPERATURE, MAX_TOKENS, PROMPT
from aux_classes import QueryRequest

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

class LLM_manager(Singleton, Observer):
{
    _llm = None
    _retriever = None
    _prompt = None

    def notify(self):
        self.start()

    def start(self):
        db_manager = DB_manager()
        self._llm = OllamaLLM(model=LLM_NAME, streaming=True, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)
        self._retriever = db_manager.get_retriever(K)
        self._prompt = PromptTemplate(template=PROMPT, input_variables=['context', 'question'])

    def __init__(self):
        self.start()

    def get_response(self, request: QueryRequest)
        try:
            qa = RetrievalQA.from_chain_type(
                llm=self._llm, 
                chain_type=CHAIN_TYPE, 
                retriever=self._retriever, 
                return_source_documents=True,
                chain_type_kwargs={"prompt": self._prompt}
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
}