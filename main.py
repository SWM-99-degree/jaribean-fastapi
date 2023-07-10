from fastapi import FastAPI
from entity.Redis import MessageQueue, MessageSet
from time import sleep
from dto.requestDto import MachingReqDto
from myapi.entity import mongodb

app = FastAPI()

# 초기 세팅
@app.on_event("startup")
def on_app_start():
	mongodb.connect()

@app.on_event("shutdown")
async def on_app_shutdown():
	mongodb.close()

# maching 요청을 받았을 때
@app.post("/api/matching")
async def postMachingMessage(machingReqDto : MachingReqDto):
	# 내부적으로 동일한 key의 queue가 형성되도록 설정
	queue = MessageQueue()
	queue.put({"userId" : machingReqDto.userId, "userLatitude" : machingReqDto.point.get("x"), "userLongitude" : machingReqDto.point.get("y")})
	getMatchingMessage()
	return

# cafe에 예약 취소
@app.delete("/api/matching/{cafeId}&&{userId}}")
async def rejectMachingMessage(machingReqDto : MachingReqDto):
	set = MessageSet(machingReqDto.userId)
	set.remove(machingReqDto.cafeId)
	set.delete_if_empty()


# user가 취소
@app.delete("/api/matching/{userId}")
async def cancelMaching(machingReqDto : MachingReqDto):
	# 몽고 DB에서 상태 바꿔줘야 함
	
	return


# 자동적으로 실행된다.
async def getMatchingMessage():
	if getMatchingMessage.running:
		return
	getMatchingMessage.running = True

	try:
		db = mongodb.client["cafe"]
		collection = db["cafe"]
		cnt = 0
		while cnt < 10:
			msg = queue.get(isBlocking=True) # 큐가 비어있을 때 대기
			
			if msg is None:
				cnt += 1
				sleep(1)
				continue

			location = {
			"type": "Point",
			"coordinates": [msg.get("userLatitude"), msg.get("userLongitude")]
			}

			cafes = collection.find({
			"location_field": {
				"$near": {
					"$geometry": location,
					"$maxDistance": 700  # 최대 탐색 반경 (미터 단위)
					}
				}
			})
			
			set = MessageSet(msg.get("userId"))

			for cafe in cafes:
				set.add(cafe.id)
				# 요청을 보내는 로직 필요 Firebase를 기준으로 필요함
	finally:
		getMatchingMessage.running = False
	
getMatchingMessage.running = False