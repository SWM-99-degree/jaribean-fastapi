from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from odmantic import AIOEngine
import certifi
import os

from dotenv import load_dotenv
from pathlib import Path



ca = certifi.where()
class MongoDB:
    def __init__(self):
        self.client = None

    def connect(self):
        self.client = MongoClient("mongodb+srv://chlrltjd5263:DOkzRJKGVgO6En97@cluster0.kbzsagk.mongodb.net/?retryWrites=true&w=majority", tlsCAFile = ca)
        #self.engine = AIOEngine(client=self.client)
        print("DB 와 연결되었습니다.")
    
    def db_table(self, table):
        #self.engine = AIOEngine(client=self.client, database=table)
        print()
    
    def close(self):
        self.client.close()

mongodb = MongoDB()