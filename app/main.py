from fastapi import FastAPI, Header, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from sse_starlette import sse
from sse_starlette.sse import EventSourceResponse
from time import sleep
from pymongo import GEO2D
from bson.son import SON
import jwt


from .entity import Redis, Documents
from .entity import mongodb, redisdb
from .reqdto import requestDto
from .reqdto.responseDto import MyCustomException, MyCustomResponse
from .service.matchingService import cafePutSSEMessage, cafeFastPutSSEMessage, userPutSSEMessage, getSSEMessage
from .service.firebaseService import testCode, sendingCompleteMessageToCafe, sendingAcceptMessageToUserFromCafe, sendingMatchingMessageToCafe, sendingCancelMessageToCafeFromUserBeforeMatching, sendingCancelMessageToCafeFromUserAfterMatching, sendingCancelMessageToUser
from .service.sqsService import send_messages
from .service.authorization import verify_jwt_token
from .service.expireHandlerService import listenExpireEvents, expireCallBack

import threading
import json
import os
from bson.objectid import ObjectId
import asyncio
import datetime
import time
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(MyCustomException)
def customExceptionHandler(request: Request, exc: MyCustomException):
	return JSONResponse(status_code = exc.status_code, content = {
		"code" : exc.code,
		"msg" : exc.msg,
		"data" : {
			"code" : exc.code,
			"msg" : exc.msg
		}
	})


def start_listening():
    asyncio.run(listenExpireEvents())
    

@app.on_event("startup")
def on_app_start():
	mongodb.connect()
	redisdb.connect()
	threading.Thread(target=start_listening, daemon=True).start()

@app.on_event("shutdown")
async def on_app_shutdown():
	mongodb.close()
	redisdb.close()


# matching 요청을 받았을 때
@app.post("/api/matching")
async def postMatchingMessage(matchingReqDto : requestDto.MatchingReqDto, userId : str = Depends(verify_jwt_token), ACCESS_AUTHORIZATION: Optional[str] = Header(None, convert_underscores = False)):
	
	set = Redis.MessageSet("matching:" + userId)
	if set.exist():
		raise MyCustomException(400, -1, "이미 매칭이 진행중입니다.")
	
	data = {
		'peopleNumber' : matchingReqDto.peopleNumber,
		'latitude' : matchingReqDto.latitude,
		'longitude' : matchingReqDto.longitude,
		'userId' : userId,
		'token' : ACCESS_AUTHORIZATION
	}
	payload_json = json.dumps(data)
	response_data = send_messages(payload_json)

	if response_data == None:
		raise MyCustomException(405, -1, "SQS가 가동중이지 않습니다.")
	else:
		return MyCustomResponse(1, "매칭을 진행합니다.")


# 카페의 매칭 응답 요청
@app.post("/api/matching/cafe")
async def receiveMatchingMessage(matchingReqDto : requestDto.MatchingCafeReqDto, cafeId : str = Depends(verify_jwt_token)):
	set = Redis.MessageSet("matching:" + matchingReqDto.userId)
	if not set.exist():
		raise MyCustomException(400, -1, "이미 매칭이 진행중입니다.")
	
	cafes = list(set.get_all())
	set.delete()

	collection = mongodb.client["jariBean"]["cafe"]

	collection = mongodb.client["jariBean"]["matching"]
	
	matching = Documents.Matching(
		userId = matchingReqDto.userId,
   		cafeId = cafeId,
		seating = int(matchingReqDto.peopleNumber),
		status = Documents.Status.PROCESSING
	)
	result = collection.insert_one(matching.dict())

	sendingAcceptMessageToUserFromCafe(matchingReqDto.userId, result.inserted_id, cafeId)
	
	for cafeId in cafes:
		sendingCancelMessageToCafeFromUserBeforeMatching(cafeId.decode("utf-8"), matchingReqDto.userId)

	return MyCustomResponse(1, "요청에 성공했습니다.")



# 카페의 매칭 거절 요청
@app.delete("/api/matching/cafe")
async def rejectMatchingMessage(matchingReqDto : requestDto.MatchingCafeReqDto, cafeId : str = Depends(verify_jwt_token)):
	set = Redis.MessageSet("matching:" + matchingReqDto.userId)
	set.remove(cafeId)

	if set.delete_if_empty():
		sendingCancelMessageToUser(matchingReqDto.userId)
		
	return MyCustomResponse(1, "매칭을 거절하였습니다.")

# 유저의 매칭 취소 요청 - 매칭되기 이전
@app.delete("/api/matching/before")
async def cancelMatchingBefore(userId : str = Depends(verify_jwt_token)):
	set = Redis.MessageSet("matching:" + userId)
	cafes = list(set.get_all())
	
	for cafeId in cafes:
		sendingCancelMessageToCafeFromUserBeforeMatching(cafeId.decode("utf-8"), userId)
	set.delete()
	return MyCustomResponse(1, "매칭을 취소가 성공하였습니다.")

# 유저의 매칭 취소 요청 - 매칭된 이후
@app.put("/api/matching/after")
async def cancelMatchingAfter(matchingCancelReqDto : requestDto.MatchingCancelReqDto, userId : str = Depends(verify_jwt_token)):
	collection = mongodb.client["jariBean"]["matching"]
	
	new_data = {
    	"$set": {
        	"status": "CANCEL",
    	}
	}
	collection.update_one({"_id": ObjectId(matchingCancelReqDto.matchingId)}, new_data)
	matching = collection.find_one({"_id": ObjectId(matchingCancelReqDto.matchingId)})

	current_time = datetime.datetime.now()
	sendingCancelMessageToCafeFromUserAfterMatching(matchingCancelReqDto.cafeId, matchingCancelReqDto.matchingId)

	if current_time - matching["matchingTime"]> datetime.timedelta(seconds=10):
		# TODO 결제 모듈
		return MyCustomResponse(1, "매칭 거절에 성공했습니다! 보증금이 환급되지 않습니다.")
	else:
		return MyCustomResponse(1, "매칭 거절에 성공했습니다! 보증금이 환급됩니다.")

@app.post("/api/matching/lambda")
def postMatchingMessageToCafe(matchingReqDto : requestDto.MatchingReqDto, userId : str = Depends(verify_jwt_token)):
	if postMatchingMessageToCafe.running:
		raise MyCustomException(400, -1, "매칭에 대한 처리가 이미 진행중입니다.")
	
	new_set = Redis.MessageSet("matching:" + userId)
	if new_set.exist():
		raise MyCustomException(400, -1, "이미 매칭이 진행중입니다.")
	
	postMatchingMessageToCafe.running = True
	number = matchingReqDto.peopleNumber

	try:
		collection = mongodb.client["jariBean"]["cafe"]

		collection.create_index([("coordinate", "2dsphere")])
		query = {
    		"coordinate" : {
        		"$near": {
            		"$geometry": {
                		"type" : "Point",
                		"coordinates" :[matchingReqDto.longitude, matchingReqDto.latitude] #[126.661675911488, 37.450979037492] 
            		},
            		"$maxDistance": 700
        		}
    		}
		}

		cafes = collection.find(query)
		
		
		for cafe in cafes:
			cafeId = str(cafe["_id"])
			new_set.add(cafeId)
			try:
				sendingMatchingMessageToCafe(cafeId, userId, number)
			except:
				continue
		new_set.expire()
		return MyCustomResponse(1, "매칭이 진행중입니다. 잠시만 기다려주세요.")
	finally:
		postMatchingMessageToCafe.running = False

postMatchingMessageToCafe.running = False



@app.put("/api/matching/noshow")
def putNoShow(matchingReq : requestDto.MatchingCancelReqDto, userId : str = Depends(verify_jwt_token)):
	collection = mongodb.client["jariBean"]["matching"]
	result = collection.find_one({"_id": ObjectId(matchingReq.matchingId)})
	if result['status'] != "PROCESSING":
		raise MyCustomException(400, -1, "매칭에 대한 처리가 이미 진행되었습니다.")
	
	new_data = {
    	"$set": {
        	"status": "NOSHOW",
    	}
	}

	collection.update_one({"_id": ObjectId(matchingReq.matchingId)}, new_data)
	return MyCustomResponse(1, "매칭 요청의 상태가 No-SHOW 로 변경되었습니다.")



@app.put("/api/matching/complete")
def putComplete(matchingReq : requestDto.MatchingCancelReqDto, userId : str = Depends(verify_jwt_token)):
	collection = mongodb.client["jariBean"]["matching"]
	result = collection.find_one({"_id": ObjectId(matchingReq.matchingId)})
	if result['status'] != "PROCESSING":
		raise MyCustomException(400, -1, "매칭에 대한 처리가 이미 진행되었습니다.")
	
	new_data = {
    	"$set": {
        	"status": "COMPLETE",
    	}
	}

	collection.update_one({"_id": ObjectId(matchingReq.matchingId)}, new_data)

	sendingCompleteMessageToCafe(userId, matchingReq.matchingId, matchingReq.cafeId)

	return MyCustomResponse(1, "매칭이 완료되었습니다.")