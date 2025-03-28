from aux_classes import QueryRequest

import asyncio

class Chatbot(Singleton):
{
    def __init__(self):
        self.const = Constants_manager()
        self.docs = Documents_manager()
        self.db = DB_manager()
        self.llm = LLM_manager()
        self.const.add_observer(self.docs)
        self.const.add_observer(self.db)
        self.const.add_observer(self.llm)

    async def chat(self, request: QueryRequest):
        return await self.llm.get_response(request)

    async def update_documents(self):
        await asyncio.to_thread(self.docs.update_repo)
        await asyncio.to_thread(self.db.update_vectors)
        await asyncio.to_thread(self.llm.start)

    async def reload(self):
        await asyncio.to_thread(self.const.load_environment_variables)

}