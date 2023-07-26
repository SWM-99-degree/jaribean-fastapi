from fastapi import FastAPI, Header, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import Response
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from sse_starlette import sse
from sse_starlette.sse import EventSourceResponse
from time import sleep
import jwt

from .entity import Redis, Documents
from .entity import mongodb
from .reqdto import requestDto
from .service.matchingService import cafePutSSEMessage, cafeFastPutSSEMessage, userPutSSEMessage, getSSEMessage

import json
import os
from bson.objectid import ObjectId
import asyncio

## 왜 gitpush가 안되는 걸깐

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = FastAPI()

async def verify_jwt_token(token:str = Header("ACCESS_AUTHORIZATION")):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        return payload["userId"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 초기 세팅
@app.on_event("startup")
def on_app_start():
	mongodb.connect()

@app.on_event("shutdown")
async def on_app_shutdown():
	mongodb.close()


@app.get("/api/stream")
async def getSSEInfo(userId : str = Depends(verify_jwt_token)):
	async def event_generator():
		while True:
			Message = getSSEMessage(userId)
			if Message:
				response = {
				"userId" : Message[0],
				"direction" : Message[1]
				}
				reponse_data = json.dumps(response)
				yield reponse_data
			await asyncio.sleep(3)
	return EventSourceResponse(event_generator(), content_type='text/event-stream')
	

# 초기 세팅
@app.get("/api/test")
async def getTest():
	redis = Redis.MessageSet("new")
	redis.add("hello")
	print(redis)

# @app.get("/api/db")
# def getDBTEST():
# 	# 참고 자료
# 	collection = mongodb.client["cafe"]["cafe"]
# 	cafe = collection.find_one(
# 		{"_id" : ObjectId("64884c1d65989d25539387b5")}
# 	)
# 	print(cafe)


# matching 요청을 받았을 때
@app.post("/api/matching")
async def postMatchingMessage(matchingReqDto : requestDto.MatchingReqDto, userId : str = await Depends(verify_jwt_token)):
	set = Redis.MessageSet("matching" + userId)
	if set.exist():
		return None
	
	lambda_url = os.environ["LAMBDA_URL"]
	headers = { "Content-Type": "application/json" }
	payload_json = json.dumps(matchingReqDto)
	payload_json["userId"] = userId

	response = Request.post(lambda_url, headers=headers, data=payload_json)

	if response.status_code == 200:
		response_data = response.json()
		return response_data
	else:
		return None






# 카페의 매칭 응답 요청
@app.post("/api/matching/cafe")
async def receiveMatchingMessage(matchingReqDto : requestDto.MatchingCafeReqDto, cafeId : str = await Depends(verify_jwt_token)):

	set = Redis.MessageSet("matching" + matchingReqDto.userId)
	if (set.exist() == None):
		cafeFastPutSSEMessage(cafe, matchingReqDto.userId, 'cancel')
		raise HTTPException(status_code=400, detail="이미 매칭이 되었습니다.")

	collection = mongodb.client["cafe"]["matching"]

	matching = Documents.Matching(
		userId = matchingReqDto.userId,
   		cafeId = cafeId,
		number = matchingReqDto.peopleNumber
	)

	result = collection.insert_one(matching.dict)

	userPutSSEMessage(matchingReqDto.userId, (matchingReqDto.cafeId, result.inserted_id))

	cafes = list(set.get_all())
	set.delete()
	for cafe in cafes:
		cafeFastPutSSEMessage(cafe, matchingReqDto.userId, 'cancel')

	return 



# 카페의 매칭 거절 요청
@app.delete("/api/matching/cafe")
async def rejectMatchingMessage(matchingReqDto : requestDto.MatchingCafeReqDto, cafeId : str = await Depends(verify_jwt_token)):
	# matching + 유저에서 하나를 카페를 뺀다
	set = Redis.MessageSet("matching" + matchingReqDto.userId)
	set.remove(cafeId)

	if set.delete_if_empty():
		userPutSSEMessage(matchingReqDto.userId, (matchingReqDto.userId,"cancel"))
	
	return


# 유저의 매칭 취소 요청 - 매칭되기 이전
@app.delete("/api/matching/user")
async def cancelMatchingBefore(userId : str = await Depends(verify_jwt_token)):
	
	set = Redis.MessageSet("matching" + userId)

	cafes = list(set.get_all())
	for cafe in cafes:
		cafeFastPutSSEMessage(cafe, userId, 'cancel')
	set.delete()


# 유저의 매칭 취소 요청 - 매칭된 이후
@app.delete("/api/matching/user")
async def cancelMatchingAfter(matchingCancelReqDto : requestDto.MatchingCancelReqDto, userId : str = await Depends(verify_jwt_token)):
	collection = mongodb.client["cafe"]["matching"]
	collection.delete_one(
		{"_id" : ObjectId(matchingCancelReqDto.matchingId)}
	)
	
	cafeFastPutSSEMessage(matchingCancelReqDto.cafeId, userId, "cancel")
	return


@app.post("/api/matching/lambda")
async def postMatchingMessageToCafe(matchingReqDto : requestDto.MatchingReqDto):
	if postMatchingMessageToCafe.running:
		return
	postMatchingMessageToCafe.running = True

	userId = matchingReqDto["userId"]
	number = matchingReqDto["peopleNumber"]

	try:
		collection = mongodb.client["cafe"]["cafe"]
		
		location = {
			"type": "Point",
			"coordinates": [matchingReqDto["latitude"], matchingReqDto["longitude"]]
		}

		cafes = await collection.find({
			"location_field": {
				"$near": {
				"$geometry": location,
				"$maxDistance": 700  # 최대 탐색 반경 (미터 단위)
				}
			}
		})
		
		new_set = Redis.MessageSet("matching" + matchingReqDto["userId"])

		for cafe in cafes:
			cafeId = cafe["_id"]
			new_set.add(cafeId)
			cafePutSSEMessage(cafeId, userId, number)
	
	finally:
		postMatchingMessageToCafe.running = False

postMatchingMessageToCafe.running = False


