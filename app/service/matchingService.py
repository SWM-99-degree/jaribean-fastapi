import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from entity.Redis import MessageQueue


def cafePutSSEMessage(userId, putId, direction):
    getSSEfromRedis = MessageQueue("SSE" + userId)
    getSSEfromRedis.put((putId, direction))

def userPutSSEMessage(userId, putId):
    getSSEfromRedis = MessageQueue("SSE" + userId)
    getSSEfromRedis.put(putId)

def cafeFastPutSSEMessage(userId, putId, direction):
    getSSEfromRedis = MessageQueue("SSE" + userId)
    getSSEfromRedis.fastput((putId, direction))



    # 만약 PutId가 cancel이라면 삭제

def getSSEMessage(userId):
    getSSEfromRedis = MessageQueue("SSE" + userId)
    if getSSEfromRedis.isEmpty():
        return None
    else:
        return getSSEfromRedis.get()

        
