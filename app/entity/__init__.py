from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from odmantic import AIOEngine
import certifi
import os
import redis

from dotenv import load_dotenv
from pathlib import Path


load_dotenv()
ca = certifi.where()
class MongoDB:
    def __init__(self):
        self.client = None

    def connect(self):
        self.client = MongoClient(os.getenv("MONGO_DB_URL"), tlsCAFile = ca)
        #self.engine = AIOEngine(client=self.client)
        print("DB 와 연결되었습니다.")
    
    def db_table(self, table):
        #self.engine = AIOEngine(client=self.client, database=table)
        print()
    
    def close(self):
        self.client.close()

class RedisDB:
    def __init__(self):
        self.redis = None
    def connect(self):
        self.redis = redis.Redis(host=os.getenv("REDIS_ENDPOINT"), port=6379, db=0)
    def close(self):
        self.redis.close()

mongodb = MongoDB()
redisdb = RedisDB()