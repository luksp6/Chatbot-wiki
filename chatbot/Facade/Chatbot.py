from aux_classes import QueryRequest

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

    def chat(self, request: QueryRequest):
        return self.llm.get_response(request)

    def update_documents(self):
        self.docs.update_repo()
        self.db.update_vectors()
        self.llm.start()

    def reload(self):
        self.const.load_enviroment_variables()

}