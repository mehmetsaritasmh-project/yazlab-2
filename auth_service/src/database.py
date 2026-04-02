from pymongo import MongoClient

class AuthDatabase:
    def __init__(self):
        # Docker-compose'daki servis adı 'mongodb' olmalı
        self.client = MongoClient("mongodb://mongodb:27017/")
        self.db = self.client["auth_db"]
        self.collection = self.db["tokens"]

    def save_token(self, username, token):
        self.collection.insert_one({"username": username, "token": token})

    def check_token(self, token):
        return self.collection.find_one({"token": token})