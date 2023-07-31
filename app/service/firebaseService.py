import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

from entity import Redis

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "jaribean-3af6f-firebase-adminsdk-voaca-c380f36f12.json"))

cred_path = "../jaribean-3af6f-firebase-adminsdk-voaca-c380f36f12.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)


async def sendingAcceptMessageToUserFromCafe(userId, matchingId, cafeId):
    userToken = Redis.Redis(userId).getToken()

    sendFCM = messaging.Message(
        data = { "userId" : userId,
                "cafeId" : cafeId,
            "matchingId" : matchingId,
            "direction" : "matching"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)


async def sendingCancelMessageToUser(userId):
    userToken = Redis.Redis(userId).getToken()

    sendFCM = messaging.Message(
        data = { "userId" : userId,
            "direction" : "cancel"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)

async def sendingCancelMessageToCafeFromUserAfterMatching(cafeId, matchingId):
    userToken = Redis.Redis(cafeId).getToken()

    sendFCM = messaging.Message(
        data = {"userId" : matchingId,
                "direction" : "cancel"},
        token = userToken
    )
    response = messaging.send(sendFCM)


async def sendingCancelMessageToCafeFromUserBeforeMatching(cafeId, userId):
    userToken = Redis.Redis(cafeId).getToken()

    sendFCM = messaging.Message(
        data = {"userId" : userId,
                "direction" : "cancel"},
        token = userToken
    )
    response = messaging.send(sendFCM)


async def sendingMatchingMessageToCafe(cafeId, userId, peopleNumber):
    userToken = Redis.Redis(cafeId).getToken()

    sendFCM = messaging.Message(
        data = {"userId" : userId,
                "peopleNumber" : peopleNumber},
        token = userToken
    )
    response = messaging.send(sendFCM)
