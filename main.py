from fastapi import FastAPI
from dotenv import load_dotenv
from botocore.exceptions import ClientError


from dto.requestDto import MachingReqDto, MachingCancelReqDto
from entity.Redis import MessageQueue, MessageSet
from entity import mongodb

import requests
import json
import os
from bson.objectid import ObjectId



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


app = FastAPI()

# 초기 세팅
@app.on_event("startup")
def on_app_start():
	mongodb.connect()

@app.on_event("shutdown")
async def on_app_shutdown():
	mongodb.close()

# @app.get("/api/db")
# async def getDBTEST():
# 	# 참고 자료
# 	collection = mongodb.client["cafe"]["cafe"]
# 	cafe = await collection.find_one(
# 		{"_id" : ObjectId("64884c1d65989d25539387b5")}
# 	)
# 	print(cafe)


# maching 요청을 받았을 때
@app.post("/api/matching")
async def postMachingMessage(machingReqDto : MachingReqDto):
	lambda_url = os.environ["LAMBDA_URL"]
	headers = { "Content-Type": "application/json" }
	payload_json = json.dumps(machingReqDto)

	response = requests.post(lambda_url, headers=headers, data=payload_json)

	if response.status_code == 200:
		response_data = response.json()
		return response_data
	else:
		return None


@app.post("/api/maching/cafe")
async def receiveMachingMessage(machingReqDto : MachingReqDto):
	# TODO firebase로 유저애게 요청이 완료되었다고 알림

	set = MessageSet("maching" + machingReqDto.userId)
	if (set.exist() == None):
		return # 오류 코드
	cafes = list(set.get_all())
	set.delete()

	for cafe in cafes:
		# TODO firebase로 다른 카페들에게 요청이 완료되었다고 알림
		print()
	
	return ""

	

# cafe에 예약 취소
@app.delete("/api/matching/cafe")
async def rejectMachingMessage(matchingReqDto : MachingReqDto):
	set = MessageSet(matchingReqDto.userId)
	set.remove(matchingReqDto.cafeId)
	if set.delete_if_empty():
		# TODO user에게 요청이 실패되었다고 알림
		print()
	return


# user가 취소
@app.delete("/api/matching/user")
async def cancelMaching(machingCancelReqDto : MachingCancelReqDto):
	collection = mongodb.client["cafe"]["maching"]
	await collection.delete_one(
		{"_id" : ObjectId(machingCancelReqDto.machingId)}
	)
	# TODO cafe에게 요청이 취소되었다고 알림
	return


@app.post("/api/matching/lambda")
async def postMatchingMessageToCafe(machingReqDto : MachingReqDto):
	if postMatchingMessageToCafe.running:
		return
	postMatchingMessageToCafe.running = True

	try:
		collection = mongodb.client["cafe"]["cafe"]
		
		location = {
			"type": "Point",
			"coordinates": [machingReqDto.get("userLatitude"), machingReqDto.get("userLongitude")]
		}

		cafes = await collection.find({
			"location_field": {
				"$near": {
				"$geometry": location,
				"$maxDistance": 700  # 최대 탐색 반경 (미터 단위)
				}
			}
		})
			
		set = MessageSet("maching" + machingReqDto.get("userId"))

		for cafe in cafes:
			set.add(cafe.id)
	# TODO 요청을 보내는 로직 필요 Firebase를 기준으로 필요함
	finally:
		postMatchingMessageToCafe.running = False
	
postMatchingMessageToCafe.running = False