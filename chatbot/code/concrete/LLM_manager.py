from abstract.Singleton.Singleton import Singleton
from abstract.Observer.Observer import Observer
from abstract.Composite.Compound_service import Compound_service

from concrete.Constants_manager import Constants_manager
from concrete.DB_manager import DB_manager
from concrete.Cache_manager import Cache_manager

from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.globals import set_llm_cache

from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage


class LLM_manager(Singleton, Observer, Compound_service):

    def __init__(self, services_to_wait=[]):
        Compound_service.__init__(self, services_to_wait)
        self._chat_history = {}  # {session_id: [mensajes]}

    async def notify(self):
        await self.disconnect()
        await self.connect()
        await self.wait_for_connection()

    async def _connect(self):
        if self._service is None:
            db = DB_manager.get_instance(DB_manager)
            const = Constants_manager.get_instance(Constants_manager)
            #cache = Cache_manager.get_instance(Cache_manager)

            #set_llm_cache(cache.get_cache_instance())

            self._service = ChatOllama(
                model=const.LLM_NAME,
                temperature=const.TEMPERATURE,
                max_tokens=const.MAX_TOKENS
            )

            self._history_prompt = ChatPromptTemplate.from_messages([
                ("system", const.HISTORY_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ])

            self._history_aware_retriever = create_history_aware_retriever(
                llm=self._service,
                retriever=db.get_retriever(const.K),
                prompt=self._history_prompt
            )

            self._qa_prompt = ChatPromptTemplate.from_messages([
                ("system", const.SYSTEM_PROMPT),
                ("human", "{input}"),
            ])

            self._document_chain = create_stuff_documents_chain(self._service, self._qa_prompt)

            self.rag_chain  = create_retrieval_chain(
                retriever=self._history_aware_retriever,
                combine_docs_chain=self._document_chain
            )

            self._connected.set()


    async def _disconnect(self):
        if self._service:
            self._service = None
            self._retriever = None
            self._prompt = None
            self._qa = None
            self.chat_history = {}

    
    async def warm_up(self):
        print("Calentando LLM...")
        response, _ = await self.get_response("Hola, esta es una consulta de calentamiento. No me interesa tu respuesta.")
        self.clear_history()
        print(f"Respuesta de calentamiento: {response}")

    
    async def get_response(self, session_id="default", question=""):
        """Genera una respuesta asíncrona."""
        try:
            response = await self.rag_chain.ainvoke({"input": question, "chat_history": self._get_history(session_id)})
            sources = set(doc.metadata["source"] for doc in response["context"])

            self._add_to_history(session_id, question, response["answer"])
            return response["answer"], sources
        except Exception as e:
            print(f"Error en la generación de la respuesta: {e}")
            return "Error interno en el servidor. Intenta de nuevo más tarde."
    

    def _get_history(self, session_id):
        return self._chat_history.setdefault(session_id, [])

    def _add_to_history(self, session_id, question, answer):
        history = self._get_history(session_id)
        history.append({"role": "user", "content": question})
        history.append({"role": "system", "content": answer})


    def clear_session_history(self, session_id):
        self._chat_history[session_id] = []

    def clear_history(self):
        self._chat_history = {}