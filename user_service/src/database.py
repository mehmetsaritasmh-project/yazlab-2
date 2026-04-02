from pymongo import MongoClient
from bson import ObjectId

class UserDatabase:
    def __init__(self):
        # localhost yerine docker-compose'daki servis adı: user_db_container
        self.client = MongoClient("mongodb://mongodb:27017")
        self.db = self.client["yazlab2_db"]
        self.collection = self.db["users"]

    def create_user(self, user_data):
        result = self.collection.insert_one(user_data)
        return result.inserted_id

    def get_user(self, user_id):
        try:
            return self.collection.find_one({"_id": ObjectId(user_id)})
        except:
            return self.collection.find_one({"id": user_id}) # Alternatif arama