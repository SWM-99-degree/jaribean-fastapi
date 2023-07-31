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


async def sendingAcceptMessageToUserFromCafe(userId, matchingId, cafeId):
    global token_domain
    userToken = Redis.Redis(token_domain+userId).getToken()

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
    global token_domain
    userToken = Redis.Redis(token_domain+userId).getToken()

    sendFCM = messaging.Message(
        data = { "userId" : userId,
            "direction" : "cancel"
        },
        token = userToken
    )
    response = messaging.send(sendFCM)

async def sendingCancelMessageToCafeFromUserAfterMatching(cafeId, matchingId):
    global token_domain
    userToken = Redis.Redis(token_domain+cafeId).getToken()

    sendFCM = messaging.Message(
        data = {"userId" : matchingId,
                "direction" : "cancel"},
        token = userToken
    )
    response = messaging.send(sendFCM)


async def sendingCancelMessageToCafeFromUserBeforeMatching(cafeId, userId):
    global token_domain
    userToken = Redis.Redis(token_domain+cafeId).getToken()

    sendFCM = messaging.Message(
        data = {"userId" : userId,
                "direction" : "cancel"},
        token = userToken
    )
    response = messaging.send(sendFCM)


async def sendingMatchingMessageToCafe(cafeId, userId, peopleNumber):
    global token_domain
    userToken = Redis.Redis(token_domain+cafeId).getToken()

    sendFCM = messaging.Message(
        data = {"userId" : userId,
                "peopleNumber" : peopleNumber},
        token = userToken
    )
    response = messaging.send(sendFCM)
