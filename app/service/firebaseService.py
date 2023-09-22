import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

from entity import Redis
from .loggingService import sendFCMLogging

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "jaribean-3af6f-firebase-adminsdk-voaca-c380f36f12.json"))

token_domain = "Token:"
# local ../ server /code/
cred_path = "/code/jaribean-3af6f-firebase-adminsdk-voaca-c380f36f12.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

def expireCallBack(message):
	userId = str(message["data"].decode("utf-8")[9:])
	sendingCancelMessageToUser(userId)
	

async def listenExpireEvents():
	redis = Redis.EventListenerRedis()
	redisSubscriber = redis.redis.pubsub()
	redisSubscriber.psubscribe(**{"__keyevent@0__:*": expireCallBack})
	
	for message in redisSubscriber.listen():
		pass

def androidNotification(title, body):
    notification = messaging.Notification(
         title = title,
         body = body
    )
    androidNotification = messaging.AndroidNotification(
            title = title,
            body = body,
            channel_id = "jari_bean_alert",
            priority = "high"
        )
    androidConfig = messaging.AndroidConfig(
          notification = androidNotification
    )
    return androidConfig, notification
     

def testSend(token, userId, username, peopleNumber):
    userToken = token

    androidConfig, notification = androidNotification("매칭 요청!", "새로운 매칭 요청입니다!")
    
    sendFCM = messaging.Message(
        notification = notification,
        android = androidConfig,
        data = {
            "username" : str(username),
            "userId" : str(userId),
            "peopleNumber" : str(peopleNumber),
            "type" : "matchingRequest"
        },
        token = userToken
    )

    messageId = sendFCMLogging(sendFCM, "FromServer", userId)
    sendFCM.data['loggingId'] = str(messageId)

    print(sendFCM)
    response = messaging.send(sendFCM)
    return sendFCM, response
     

def sendingCompleteMessageToCafe(userId, matchingId, cafeId):
    global token_domain
    userToken = Redis.Redis(token_domain+str(cafeId)).getToken()

    androidConfig, notification = androidNotification("매칭 완료 성공!", str(userId) + "와 매칭이 완료되었습니다.")
    
    sendFCM = messaging.Message(
        notification = notification,
        android = androidConfig,
        data = {
            "userId" : userId,
            "cafeId" : cafeId,
            "matchingId" : matchingId,
            "direction" : "complete",
            "type" : "matchingComplete"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)




def sendingCancelMessageToCafeFromUserAfterMatching(cafeId, matchingId, username):
    global token_domain
    userToken = Redis.Redis(str(token_domain+str(cafeId))).getToken()

    androidConfig, notification = androidNotification("매칭 취소!", "유저가 매칭 취소 요청을 보냈습니다.")

    sendFCM = messaging.Message(
        notification = notification,
        android = androidConfig,
        data = {
            "username" : str(username),
            "userId" : str(matchingId),
            "direction" : "cancel",
            "type" : "matchingCancelAfterMatching"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)


def sendingCancelMessageToCafeFromUserBeforeMatching(cafeId, userId):
    global token_domain
    userToken = Redis.Redis(token_domain+str(cafeId)).getToken()

    androidConfig, notification = androidNotification("매칭 취소!", "다른 매장과 이미 매칭 되었습니다.")

    sendFCM = messaging.Message(
        notification = notification,
        android = androidConfig,
        data = {
            "userId" : str(userId),
            "direction" : "cancel",
            "type" : "matchingCancelBeforeMatching"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)


def sendingMatchingMessageToCafe(cafeId, userId, peopleNumber, username):
    global token_domain
    userToken = Redis.Redis(str(token_domain+cafeId)).getToken()

    androidConfig, notification = androidNotification("매칭 요청!", "새로운 매칭 요청입니다!")
    
    sendFCM = messaging.Message(
        notification = notification,
        android = androidConfig,
        data = {
            "username" : str(username),
            "userId" : str(userId),
            "peopleNumber" : str(peopleNumber),
            "type" : "matchingRequest"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)



# 전송 보장이 꼭 필요한 로직들
def sendingAcceptMessageToUserFromCafe(userId, matchingId, cafeId):
    global token_domain
    userToken = Redis.Redis(token_domain+str(userId)).getToken()

    androidConfig, notification = androidNotification("매칭 성공!", str(cafeId) + "와 매칭이 성사되었습니다.")

    sendFCM = messaging.Message(
        notification = notification,
        android = androidConfig,
        data = { 
            "userId" : str(userId),
            "cafeId" : str(cafeId),
            "matchingId" : str(matchingId),
            "direction" : "matching",
            "type" : "matchingSuccess"
        },
        token = userToken
    )
    messageId = sendFCMLogging(sendFCM, cafeId, userId)

    sendFCM.data['loggingId'] = str(messageId)
    response = messaging.send(sendFCM)


def sendingCancelMessageToUser(userId):
    global token_domain
    userToken = Redis.Redis(token_domain+str(userId)).getToken()

    androidConfig, notification = androidNotification("매칭 실패!", "주변에 매칭 가능한 카페가 없습니다.")

    sendFCM = messaging.Message(
        android = androidConfig,
        notification = notification,
        data = {
            'userId' : str(userId),
            'direction' : 'cancel',
            'type' : 'matchingFail'
        },
        token = userToken)
    
    messageId = sendFCMLogging(sendFCM, "FromServer", userId)

    sendFCM.data['loggingId'] = str(messageId)
    response = messaging.send(sendFCM)