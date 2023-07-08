# import aioredis

# class RedisDriver:
#     def __init__(self):
#         self.redis_url = f'redis://{your_ur}'
#         self.redis_client = aioredis.from_url(self.redis_url)
    
#     async def set_key(self, key, value, ttl=60):
#         await self.redis_client.set(key, value)
#         if ttl:
#             await self.redis_client.expire(key, ttl)
#         return True
    	
#     async def get_key(self, key):
#         return await self.redis_client.get(key)
   
   
# # * test code
# if __name__ == '__main__':
#     import asyncio
#     redis_instance = RedisDriver()

#     async def main():
#         await redis_instance.set_key('test', 'test_value', 10)
#         await redis_instance.set_key('test2', 'test2_value', 10)
#         print(await redis_instance.get_key('test'))
#         print(await redis_instance.get_key('test2'))

#     asyncio.run(main())