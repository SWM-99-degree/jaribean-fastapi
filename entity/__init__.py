from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from odmantic import AIOEngine

# 소중한 Secrets.json 가져오기
from myapi.config.MongoConfig import MONGO_DB_NAME, MONGO_DB_URL

class MongoDB:
    def __init__(self):
        self.client = None

    def connect(self):
        self.client = MongoClient("{MONGO_DB_URL}")
        print("DB 와 연결되었습니다.")
    
    def close(self):
        self.client.close()

mongodb = MongoDB()