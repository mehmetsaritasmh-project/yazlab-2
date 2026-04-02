from pymongo import MongoClient
from bson import ObjectId

class ProductDatabase:
    def __init__(self):
        # İzole veritabanı motoru [cite: 63, 64]
        self.client = MongoClient("mongodb://product_db_container:27017/")
        self.db = self.client["product_db"]
        self.collection = self.db["products"]

    def create_product(self, product_data):
        return self.collection.insert_one(product_data).inserted_id

    def get_product(self, p_id):
        return self.collection.find_one({"_id": ObjectId(p_id)})