from fastapi import FastAPI, Header, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import Response
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from sse_starlette import sse
from sse_starlette.sse import EventSourceResponse
from time import sleep
from pymongo import GEO2D
from bson.son import SON
import jwt


from .entity import Redis, Documents
from .entity import mongodb
from .reqdto import requestDto
from .service.matchingService import cafePutSSEMessage, cafeFastPutSSEMessage, userPutSSEMessage, getSSEMessage
from .service.firebaseService import testCode, sendingCompleteMessageToCafe, sendingAcceptMessageToUserFromCafe, sendingMatchingMessageToCafe, sendingCancelMessageToCafeFromUserBeforeMatching, sendingCancelMessageToCafeFromUserAfterMatching, sendingCancelMessageToUser
from .service.sqsService import send_messages

import threading
import json
import os
from bson.objectid import ObjectId
import asyncio
import datetime
import time
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

# TODO changed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_jwt_token(token: Optional[str] = Header("ACCESS_AUTHORIZATION")):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS512"])
        return payload["userId"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="토큰이 알맞지 않습니다.")

def expireCallBack(message):
	userId = message["data"].decode("utf-8")[8:]
	sendingCancelMessageToUser(userId)
	


async def listenExpireEvents():
	redis = Redis.EventListenerRedis()
	redisSubscriber = redis.redis.pubsub()
	redisSubscriber.psubscribe(**{"__keyevent@0__:*": expireCallBack})
	
	for message in redisSubscriber.listen():
		pass

def start_listening():
    asyncio.run(listenExpireEvents())
    

@app.on_event("startup")
def on_app_start():
	mongodb.connect()
	threading.Thread(target=start_listening, daemon=True).start()

@app.on_event("shutdown")
async def on_app_shutdown():
	mongodb.close()

	

# 초기 세팅
@app.get("/api/test")
async def getTest():
	data = {"name" : "yoHO!",
	 		"token" : 123123213}
	msg = json.dumps(data)
	send_messages(msg)

@app.get("/api/test/test")
async def receivedTest():
	print("test clear!")
	

# matching 요청을 받았을 때
@app.post("/api/matching")
async def postMatchingMessage(matchingReqDto : requestDto.MatchingReqDto, userId : str = Depends(verify_jwt_token)):
	
	set = Redis.MessageSet("matching" + userId)
	if set.exist():
		raise HTTPException(status_code=400, detail= "이미 요청 대기 중입니다.")

	matchingReqDto["userId"] = userId
	matchingReqDto["token"] = Header("ACCESS_AUTHORIZATION")
	payload_json = json.dumps(matchingReqDto)

	response_data = send_messages(payload_json)

	if response_data == None:
		raise HTTPException(status_code=405, detail="SQS 작동 오류")
	else:
		return {"status": 1, "message": "요청이 진행중입니다."}



# 카페의 매칭 응답 요청
# SSE 버전 userPutSSEMessage(matchingReqDto.userId, (matchingReqDto.cafeId, result.inserted_id))
@app.post("/api/matching/cafe")
async def receiveMatchingMessage(matchingReqDto : requestDto.MatchingCafeReqDto, cafeId : str = Depends(verify_jwt_token)):
	
	set = Redis.MessageSet("matching" + matchingReqDto.userId)
	if (set.exist() == None):
		raise HTTPException(status_code=400, detail="이미 매칭이 되었습니다.")
	
	cafes = list(set.get_all())
	set.delete()

	collection = mongodb.client["cafe"]["cafe"]
	cafe = collection.find_one({"userId": cafeId})

	collection = mongodb.client["cafe"]["matching"]
	
	# TODO status 필요함
	matching = Documents.Matching(
		userId = matchingReqDto.userId,
   		cafe = cafe,
		number = matchingReqDto.peopleNumber,
		status = Documents.Status("PROCESSING")
	)
	result = collection.insert_one(matching.dict)

	sendingAcceptMessageToUserFromCafe(matchingReqDto.userId, result.inserted_id, cafeId)
	
	for cafeId in cafes:
		sendingCancelMessageToCafeFromUserBeforeMatching(cafeId, matchingReqDto.userId)
	return {"status": 1, "message": "요청에 성공했습니다!"}



# 카페의 매칭 거절 요청
# SSE 버전 userPutSSEMessage(matchingReqDto.userId, (matchingReqDto.userId,"cancel"))
@app.delete("/api/matching/cafe")
async def rejectMatchingMessage(matchingReqDto : requestDto.MatchingCafeReqDto, cafeId : str = Depends(verify_jwt_token)):
	set = Redis.MessageSet("matching" + matchingReqDto.userId)
	set.remove(cafeId)

	if set.delete_if_empty():
		sendingCancelMessageToUser(matchingReqDto.userId)
		
	return {"status": 1, "message": "매칭 거절에 성공했습니다!"}


# 유저의 매칭 취소 요청 - 매칭되기 이전
@app.delete("/api/matching/before")
async def cancelMatchingBefore(userId : str = Depends(verify_jwt_token)):
	set = Redis.MessageSet("matching" + userId)
	cafes = list(set.get_all())
	for cafeId in cafes:
		sendingCancelMessageToCafeFromUserBeforeMatching(cafeId, userId)
	set.delete()
	return {"status": 1, "message": "매칭 거절에 성공했습니다!"}


# 유저의 매칭 취소 요청 - 매칭된 이후
@app.put("/api/matching/after")
async def cancelMatchingAfter(matchingCancelReqDto : requestDto.MatchingCancelReqDto, userId : str = Depends(verify_jwt_token)):
	collection = mongodb.client["cafe"]["matching"]
	
	new_data = {
    	"$set": {
        	"status": "CANCEL",
    	}	
	}
	matching = collection.update_one({"_id": ObjectId(matchingCancelReqDto.matchingId)}, new_data)

	current_time = datetime.datetime.now()
	sendingCancelMessageToCafeFromUserAfterMatching(matching["cafeId"], matchingCancelReqDto.matchingId)

	if current_time - matching["matchingTime"] > 90:
		# 추가적으로 결제가 되도록 하는 코드 필요
		return {"status": 1, "message": "매칭 거절에 성공했습니다! 보증금이 환급되지 않습니다."}
	else:
		return {"status": 1, "message": "매칭 거절에 성공했습니다! 보증금이 환급됩니다."}


@app.post("/api/matching/lambda")
async def postMatchingMessageToCafe(matchingReqDto : requestDto.MatchingReqDto, userId : str = Depends(verify_jwt_token)):
	if postMatchingMessageToCafe.running:
		raise HTTPException(status_code=400, detail= "이미 매칭이 진행 중입니다.")
	
	postMatchingMessageToCafe.running = True
	number = matchingReqDto.peopleNumber

	try:
		collection = mongodb.client["cafe"]["cafe"]

		collection.create_index([("coordinate", "2dsphere")])
		query = {
    		"coordinate" : {
        		"$near": {
            		"$geometry": {
                		"type" : "Point",
                		"coordinates" :[matchingReqDto.latitude, matchingReqDto.longitude] #[126.661675911488, 37.450979037492] 
            		},
            		"$maxDistance": 700
        		}
    		}
		}

		cafes = collection.find(query)
		
		new_set = Redis.MessageSet("matching" + userId)
		

		for cafe in cafes:
			cafeId = str(cafe["userId"])
			new_set.add(cafeId)
			try:
				await sendingMatchingMessageToCafe(cafeId, userId, number)
			except:
				print("토큰이 없습니다.")
			#cafePutSSEMessage(cafeId, userId, number)
		new_set.expire()
		return {"status": 1, "message": "매칭 요청에 성공했습니다!"}
	finally:
		postMatchingMessageToCafe.running = False

postMatchingMessageToCafe.running = False


# TODO NOSHOW - COMPLETE 인지를 무조건 확인해야 함
@app.put("/api/matching/noshow")
async def putNoShow(matchingReq : requestDto.MatchingCancelReqDto, userId : str = Depends(verify_jwt_token)):
	collection = mongodb.client["cafe"]["matching"]
	result = collection.find_one({"_id": ObjectId(matchingReq.matchingId)})
	if result.status != "PROCESSING":
		raise HTTPException(status_code=400, detail= "매칭에 대한 처리가 이미 진행되었습니다.")
	
	new_data = {
    	"$set": {
        	"status": "NOSHOW",
    	}
	}
	collection.update_one({"_id": ObjectId(matchingReq.matchingId)}, new_data)
	return {"status": 1, "message": "노쇼 설정이 되었습니다!"}




# TODO COMPLETE
@app.put("/api/matching/complete")
async def putComplete(matchingReq : requestDto.MatchingCancelReqDto, userId : str = Depends(verify_jwt_token)):
	collection = mongodb.client["cafe"]["matching"]
	new_data = {
    	"$set": {
        	"status": "COMPLETE",
    	}
	}
	collection.update_one({"_id": ObjectId(matchingReq.matchingId)}, new_data)
	sendingCompleteMessageToCafe(userId, matchingReq.matchingId, matchingReq.cafeId)
	return {"status": 1, "message": "매칭이 성사되어 종료되었습니다!"}