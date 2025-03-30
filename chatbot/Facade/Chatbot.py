from aux_classes import QueryRequest
from Singleton.Singleton import Singleton
from Singleton.Constants_manager import Constants_manager
from Singleton.Documents_manager import Documents_manager
from Composite.Cache_manager import Cache_manager
from Composite.DB_manager import DB_manager
from Composite.LLM_manager import LLM_manager

import asyncio

class Chatbot(Singleton):


    def __init__(self):
        self._services = []
        
        self.docs = Documents_manager()
        self.db = DB_manager()
        self._services.append(self.db)

        self.cache = Cache_manager([self.db])
        self._services.append(self.cache)

        self.llm = LLM_manager([self.db, self.cache])
        self._services.append(self.llm)

        const = Constants_manager()
        const.add_observer(self.docs)
        const.add_observer(self.db)
        const.add_observer(self.cache)
        const.add_observer(self.llm)


    async def init_services(self):
        for service in self._services:
            await service.connect()
            await service.wait_for_connection()


    async def chat(self, request: QueryRequest):
        return await self.llm.get_response(request)


    async def update_documents(self):
        await asyncio.to_thread(self.docs.update_repo)
        await asyncio.to_thread(self.db.update_vectors)
        await asyncio.to_thread(self.llm.start)


    def reload(self):
        const = Constants_manager()
        const.load_environment_variables