import os

from enum import Enum
from dotenv import load_dotenv
from bson.objectid import ObjectId

from entity import mongodb

class FCMStatus(Enum):
    FIRST = 1
    SECOND = 2
    FAIL = 3
    SUCCESS = 0

def changeFCMLoggingStatusReceive(loggingId):
    collection = mongodb.client["jariBean"]["fcmlogging"]
    
    changeStatus = {
        "$set" : {
            "status" : FCMStatus.SUCCESS.value
        }
    }
    
    collection.update_one({"_id" : ObjectId(loggingId)}, changeStatus)
    

def sendFCMLogging(message, userId, receiveId):
    collection = mongodb.client["jariBean"]["fcmlogging"]

    data = {
        "sendId" : userId,
        "receiveId" : receiveId,
        "fcmMessage" : str(message),
        "status" : FCMStatus.FIRST.value
    }

    result = collection.insert_one(data)

    return result.inserted_id

