from aux_classes import QueryRequest
from Singleton.Singleton import Singleton
from Singleton.Constants_manager import Constants_manager
from Observer.Observer import Observer
from Composite.Compound_service import Compound_service
from Composite.DB_manager import DB_manager
from Composite.Cache_manager import Cache_manager

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.globals import set_llm_cache

import asyncio

class LLM_manager(Singleton, Observer, Compound_service):

    def __init__(self, services_to_wait=[]):
        Compound_service.__init__(self, services_to_wait)

    async def notify(self):
        await self.disconnect()
        await self.connect()
        await self.wait_for_connection()

    async def _connect(self):
        if self._service is None:
            db_manager = DB_manager()
            const = Constants_manager()
            cache = Cache_manager()
            set_llm_cache(cache.get_instance())
            self._service = OllamaLLM(
                model=const.LLM_NAME,
                streaming=True,
                temperature=const.TEMPERATURE,
                max_tokens=const.MAX_TOKENS
            )
            self._retriever = db_manager.get_retriever(const.K)
            self._prompt = PromptTemplate(template=const.PROMPT, input_variables=['context', 'question'])
            self._connected.set()


    async def _disconnect(self):
        if self._service:
            self._service = None
            self._retriever = None
            self._prompt = None

    
    async def get_response(self, request: QueryRequest):
        """Genera respuestas de manera asíncrona con streaming."""
        try:
            const = Constants_manager()
            qa = RetrievalQA.from_chain_type(
                llm=self._service,
                chain_type=const.CHAIN_TYPE,
                retriever=self._retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": self._prompt}
            )

            sources = set()
            
            async for chunk in qa.astream({"query": request.query}):  # Usa la versión asíncrona
                for doc in chunk.get("source_documents", []):
                    sources.add(doc.metadata.get("source", "Desconocido"))
                yield chunk["result"]

            if sources:
                yield f"\nFuentes: {', '.join(sources)}"
                
        except Exception as e:
            print(f"Error en la generación del stream: {e}")
            yield "Error interno en el servidor. Intenta de nuevo más tarde."