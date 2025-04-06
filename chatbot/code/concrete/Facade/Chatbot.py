from utils.aux_classes import QueryRequest

from abstract.Singleton.Singleton import Singleton

from concrete.Constants_manager import Constants_manager
from concrete.Documents_manager import Documents_manager
from concrete.Cache_manager import Cache_manager
from concrete.DB_manager import DB_manager
from concrete.LLM_manager import LLM_manager

import asyncio
import os

class Chatbot(Singleton):


    def __init__(self):
        self._services = []
        
        self.docs = Documents_manager()

        self.db = DB_manager()
        self._services.append(self.db)

        self.cache = Cache_manager()
        self.cache.set_services_to_wait([self.db])
        self._services.append(self.cache)

        self.llm = LLM_manager()
        self.llm.set_services_to_wait([self.db, self.cache])
        self._services.append(self.llm)

        const = Constants_manager.get_instance(Constants_manager)
        const.add_observer(self.docs)
        const.add_observer(self.db)
        const.add_observer(self.cache)
        const.add_observer(self.llm)

    async def start(self):
        deployed = self._was_deployed()
        await self.docs.start()
        await self.init_services()
        await self.cache.clear_cache()
        await self.llm.warm_up()
        if not deployed:
            await asyncio.to_thread(self.db.update_vectors)

    async def init_services(self):
        for service in self._services:
            await service.connect()
            await service.wait_for_connection()


    async def chat(self, message):
        async for chunk in self.llm.get_response(message):
            yield chunk


    async def update_documents(self):
        await asyncio.to_thread(self.docs.update_repo)
        await asyncio.to_thread(self.db.update_vectors)
        await self.cache.clear_cache()
        await asyncio.to_thread(self.llm.start)

    def _was_deployed(self):
        const = Constants_manager.get_instance(Constants_manager)
        return os.path.exists(os.path.join(os.getcwd(), const.RESOURCES_PATH))