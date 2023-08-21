from ..entity import Redis
from ..service.firebaseService import sendingCancelMessageToUser


def expireCallBack(message):
	userId = message["data"].decode("utf-8")[8:]
	sendingCancelMessageToUser(userId)
	

async def listenExpireEvents():
	redis = Redis.EventListenerRedis()
	redisSubscriber = redis.redis.pubsub()
	redisSubscriber.psubscribe(**{"__keyevent@0__:*": expireCallBack})
	
	for message in redisSubscriber.listen():
		pass