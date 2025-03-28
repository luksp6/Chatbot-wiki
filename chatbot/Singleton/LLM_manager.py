from aux_classes import QueryRequest

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

import asyncio

class LLM_manager(Singleton, Observer):
{
    _llm = None
    _retriever = None
    _prompt = None

    async def notify(self):
        await self.start()

    async def start(self):
        db_manager = DB_manager()
        const = Constants_manager()
        self._llm = OllamaLLM(model=const.LLM_NAME, streaming=True, temperature=const.TEMPERATURE, max_tokens=const.MAX_TOKENS)
        self._retriever = await asyncio.to_thread(db_manager.get_retriever, K)
        self._prompt = PromptTemplate(template=const.PROMPT, input_variables=['context', 'question'])

    def __init__(self):
        self.start()

    async def get_response(self, request: QueryRequest)
        try:
            const = Constants_manager()
            qa = RetrievalQA.from_chain_type(
                llm=self._llm, 
                chain_type=const.CHAIN_TYPE, 
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