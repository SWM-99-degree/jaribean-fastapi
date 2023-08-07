import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

from entity import Redis

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "jaribean-3af6f-firebase-adminsdk-voaca-c380f36f12.json"))

token_domain = "Token:"
cred_path = "../jaribean-3af6f-firebase-adminsdk-voaca-c380f36f12.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)


def testCode(token):
    # sendFCM1 = messaging.Message(notification= {"answer": "졸리다"}, token = token)
    sendFCM = messaging.Message(data = {"title":"안녕", "description":"안녕ㅇㅇㅇㅇㅇ"}, token = token)
    response = messaging.send(sendFCM)

def sendingCompleteMessageToCafe(userId, matchingId, cafeId):
    global token_domain
    userToken = Redis.Redis(token_domain+cafeId).getToken()
    sendFCM = messaging.Message(
        data = {
            "data" : {
            "userId" : userId,
            "cafeId" : cafeId,
            "matchingId" : matchingId,
            "direction" : "complete"
            },
            "type" : "data"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)



def sendingAcceptMessageToUserFromCafe(userId, matchingId, cafeId):
    global token_domain
    userToken = Redis.Redis(token_domain+userId).getToken()

    sendFCM = messaging.Message(
        data = { 
            "data" : {
            "title" : "매칭 성공 완료!",
            "description" : cafeId + "와 매칭이 시작되었습니다!",
            "userId" : userId,
            "cafeId" : cafeId,
            "matchingId" : matchingId,
            "direction" : "matching"
            },
            "type" : "noti"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)


def sendingCancelMessageToUser(userId):
    global token_domain
    userToken = Redis.Redis(token_domain+userId).getToken()
    sendFCM = messaging.Message(
        data = { 
            "data" : {
            "userId" : userId,
            "direction" : "cancel"
            },
            "type" : "data"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)

def sendingCancelMessageToCafeFromUserAfterMatching(cafeId, matchingId):
    global token_domain
    userToken = Redis.Redis(token_domain+cafeId).getToken()

    sendFCM = messaging.Message(
        data = {
            "data" : {
            "userId" : matchingId,
            "direction" : "cancel"},
            "type" : "data"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)


def sendingCancelMessageToCafeFromUserBeforeMatching(cafeId, userId):
    global token_domain
    userToken = Redis.Redis(token_domain+cafeId).getToken()

    sendFCM = messaging.Message(
        data = {
            "data" : {
            "userId" : userId,
            "direction" : "cancel"},
            "type" : "data"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)


def sendingMatchingMessageToCafe(cafeId, userId, peopleNumber):
    global token_domain
    userToken = Redis.Redis(token_domain+cafeId).getToken()

    sendFCM = messaging.Message(
        data = {
            "data" : {
                "userId" : userId,
                "peopleNumber" : peopleNumber},
            "type" : "data"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)
