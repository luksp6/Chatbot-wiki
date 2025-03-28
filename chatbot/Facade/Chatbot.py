from aux_classes import QueryRequest

import asyncio

class Chatbot(Singleton):
{
    def __init__(self):
        self.const = Constants_manager()
        self.docs = Documents_manager()
        self.db = DB_manager()
        self.cache = Cache_manager()
        self.llm = LLM_manager()
        self.const.add_observer(self.docs)
        self.const.add_observer(self.db)
        self.const.add_observer(self.llm)

    async def chat(self, request: QueryRequest):
        cache_key = f"chat:{hash(request.query)}"
        cached_response = await redis_manager.get_cache(cache_key)
        if cached_response:
            return cached_response

        response = await self.llm.get_response(request)
        await redis_manager.set_cache(cache_key, response)  # Guardar en caché
        return response

    async def update_documents(self):
        await asyncio.to_thread(self.docs.update_repo)
        await asyncio.to_thread(self.db.update_vectors)
        await asyncio.to_thread(self.llm.start)

    async def reload(self):
        await asyncio.to_thread(self.const.load_environment_variables)

}