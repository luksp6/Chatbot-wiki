from utils.aux_classes import QueryRequest

from abstract.Singleton.Singleton import Singleton
from abstract.Observer.Observer import Observer
from abstract.Composite.Compound_service import Compound_service

from concrete.Constants_manager import Constants_manager
from concrete.DB_manager import DB_manager
from concrete.Cache_manager import Cache_manager

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.globals import set_llm_cache

class LLM_manager(Singleton, Observer, Compound_service):

    def __init__(self, services_to_wait=[]):
        Compound_service.__init__(self, services_to_wait)

    async def notify(self):
        await self.disconnect()
        await self.connect()
        await self.wait_for_connection()

    async def _connect(self):
        if self._service is None:
            db = DB_manager.get_instance(DB_manager)
            const = Constants_manager.get_instance(Constants_manager)
            cache = Cache_manager.get_instance(Cache_manager)
            set_llm_cache(cache.get_cache_instance())
            self._service = OllamaLLM(
                model=const.LLM_NAME,
                streaming=True,
                temperature=const.TEMPERATURE,
                max_tokens=const.MAX_TOKENS
            )
            self._retriever = db.get_retriever(const.K)
            self._prompt = PromptTemplate(template=const.PROMPT, input_variables=['context', 'question'])
            self._qa = RetrievalQA.from_chain_type(
                llm=self._service,
                chain_type=const.CHAIN_TYPE,
                retriever=self._retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": self._prompt}
            )
            self._connected.set()


    async def _disconnect(self):
        if self._service:
            self._service = None
            self._retriever = None
            self._prompt = None
            self._qa = None

    
    async def warm_up(self):
        print("Calentando LLM...")
        response = ""
        async for chunk in self.get_response("Hola"):
            response += chunk
        print(f"Respuesta de calentamiento: {response}")

    
    async def get_response(self, query=""):
        """Genera respuestas de manera asíncrona con streaming."""
        try:
            sources = set()            
            async for chunk in self._qa.astream({"query": query}):
                for doc in chunk.get("source_documents", []):
                    sources.add(doc.metadata.get("source", "Desconocido"))
                yield chunk["result"]
            if sources:
                yield f"\nFuentes: {', '.join(sources)}"                
        except Exception as e:
            print(f"Error en la generación del stream: {e}")
            yield "Error interno en el servidor. Intenta de nuevo más tarde."