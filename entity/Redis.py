import redis


class MessageSet:
    def __init__(self, name):
        self.name = name
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    def add(self, *items):
        return self.redis.sadd(self.name, *items)

    def remove(self, *items):
        return self.redis.srem(self.name, *items)

    def get_all(self):
        return self.redis.smembers(self.name)

    def is_member(self, item):
        return self.redis.sismember(self.name, item)

    def size(self):
        return self.redis.scard(self.name)
    
    def delete_if_empty(self):
        if self.size() == 0:
            self.redis.delete(self.name)
    
    def delete(self):
        self.redis.delete(self.name)

class MessageQueue(object):
    def __init__(self, **redis_kwargs):
        self.key = "machingQueue"
        self.rq = redis.Redis(**redis_kwargs)

    def size(self): # 큐 크기 확인
        return self.rq.llen(self.key)

    def isEmpty(self): # 비어있는 큐인지 확인
        return self.size() == 0

    def put(self, element): # 데이터 넣기
        self.rq.lpush(self.key, element) # left push

    def get(self, isBlocking=False, timeout=None): # 데이터 꺼내기
        if isBlocking:
            element = self.rq.brpop(self.key, timeout=timeout) # blocking right pop
            element = element[1] # key[0], value[1]
        else:
            element = self.rq.rpop(self.key) # right pop
        return element

    def get_without_pop(self): # 꺼낼 데이터 조회
        if self.isEmpty():
            return None
        element = self.rq.lindex(self.key, -1)
        return element