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


@app.get("/stream")
async def getSSEInfo(userId : str = Depends(verify_jwt_token)):
	async def event_generator():
		while True:
			Message = getSSEMessage(userId)
			if Message:
				yield Message# SSE 이벤트 생성
			await asyncio.sleep(3)
	return EventSourceResponse(event_generator())
	



# 초기 세팅
# 매칭 후 취소
# userSet {cafe1, cafe2, cafe3} - cafe2 삭제 + cafe1
# user cafe1 
# cafe1 (user, 2) o
# cafe2 (user, 2) x
# cafe3 (user, 2) (user, cancel)

# 모두에게 거절당함
# userSet {cafe1, cafe2, cafe3} - 모두 삭제
# user cancel
# cafe1 (user, 2) x
# cafe2 (user, 2) x
# cafe3 (user, 2) x


# user -> cafeId, cancel은 취소, 


@app.get("/api/test")
async def getTest():
	redis = Redis.MessageSet("new")
	redis.add("hello")
	print(redis)

@app.get("/api/db")
def getDBTEST():
	# 참고 자료
	collection = mongodb.client["cafe"]["cafe"]
	cafe = collection.find_one(
		{"_id" : ObjectId("64884c1d65989d25539387b5")}
	)
	print(cafe)


# maching 요청을 받았을 때
@app.post("/api/matching")
async def postMachingMessage(machingReqDto : requestDto.MatchingReqDto):
	lambda_url = os.environ["LAMBDA_URL"]
	headers = { "Content-Type": "application/json" }
	payload_json = json.dumps(machingReqDto)

	response = Request.post(lambda_url, headers=headers, data=payload_json)

	if response.status_code == 200:
		response_data = response.json()
		return response_data
	else:
		return None






# 카페의 매칭 응답 요청
@app.post("/api/maching/cafe")
async def receiveMachingMessage(matchingReqDto : requestDto.MatchingReqDto, cafeId : str = await Depends(verify_jwt_token)):
	# 취소가 되었는지를 확인해야 함
	set = Redis.MessageSet("matching" + matchingReqDto.userId)
	if (set.exist() == None):
		cafeFastPutSSEMessage(cafe, matchingReqDto.userId, 'cancel')
		return

	collection = mongodb.client["cafe"]["maching"]
	matching = Documents.Matching(
		userId = matchingReqDto.userId,
   		cafeId = matchingReqDto.cafeId,
		number = matchingReqDto.number
	)

	result = collection.insert_one(
		matching.dict
	)

	userPutSSEMessage(matchingReqDto.userId, (matchingReqDto.cafeId, result.inserted_id))

	
	cafes = list(set.get_all())
	set.delete()

	for cafe in cafes:
		# 만약에 한번더 요청이 왔을 경우에는 front에서 자동으로 취소되도록 로직이 필요할 것 같음
		cafeFastPutSSEMessage(cafe, matchingReqDto.userId, 'cancel')
	
	return 



# 카페의 매칭 거절 요청
@app.delete("/api/matching/cafe")
async def rejectMachingMessage(matchingReqDto : requestDto.MatchingReqDto, cafeId : str = await Depends(verify_jwt_token)):
	# matching + 유저에서 하나를 카페를 뺀다
	set = Redis.MessageSet("matching" + matchingReqDto.userId)
	set.remove(cafeId)

	# 만약에 maching 사이에 아무것도 없다면 아예 삭제하고, userId에게 삭제를 부여함
	if set.delete_if_empty():
		userPutSSEMessage(matchingReqDto.userId, (matchingReqDto.userId,"cancel"))
	return


# 유저의 매칭 취소 요청 - 매칭되기 이전
@app.delete("/api/matching/user")
async def cancelMatchingBefore(matchingReqDto : requestDto.MatchingReqDto, userId : str = await Depends(verify_jwt_token)):
	set = Redis.MessageSet("matching" + userId)

	cafes = list(set.get_all())
	set.delete()
	for cafe in cafes:
		cafeFastPutSSEMessage(cafe, userId, 'cancel')
	set.delete()


# 유저의 매칭 취소 요청 - 매칭된 이후
@app.delete("/api/matching/user")
async def cancelMachingAfter(matchingCancelReqDto : requestDto.MatchingCancelReqDto, userId : str = await Depends(verify_jwt_token)):
	collection = mongodb.client["cafe"]["maching"]
	collection.delete_one(
		{"_id" : ObjectId(matchingCancelReqDto.machingId)}
	)
	# 매칭된 유저 Id를 보내서 카페에서 삭제하도록 함
	cafeFastPutSSEMessage(matchingCancelReqDto.cafeId, userId, "cancel")
	return


@app.post("/api/matching/lambda")
async def postMatchingMessageToCafe(matchingReqDto : requestDto.MatchingReqDto):
	if postMatchingMessageToCafe.running:
		return
	postMatchingMessageToCafe.running = True

	userId = matchingReqDto["userId"]
	number = matchingReqDto["number"]

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
		
		new_set = Redis.MessageSet("maching" + matchingReqDto["userId"])
		for cafe in cafes:
			cafeId = cafe["_id"]
			new_set.add(cafeId)
			cafePutSSEMessage(cafeId, userId, number)

	
	finally:
		postMatchingMessageToCafe.running = False



	
postMatchingMessageToCafe.running = False


