from pymongo.mongo_client import MongoClient

uri = "mongodb+srv://fullglobaltech:gbjY7H9OD8Kjh8cE@full.wn7m584.mongodb.net/?retryWrites=true&w=majority"


class BBDD:
    def __init__(self):
        self.client = MongoClient(uri)

    def ping(self):
        self.client.admin.command('ping')
        return "Pong"
