from fastapi import FastAPI
from entity.RedisQueue import MessageQueue
from pydantic import BaseSettings
from time import sleep


app = FastAPI()

queue = MessageQueue("my_queue", host = "localhost", port=6379, db=0)


@app.get("/matchingmessage/queue")
async def getMatchingMessage():
	cnt = 0
	while True:
		msg = queue.get(isBlocking=True) # 큐가 비어있을 때 대기
		sleep(3)
		if msg is not None:
			print(msg)
		else: cnt +=1

		if cnt > 10:
			break