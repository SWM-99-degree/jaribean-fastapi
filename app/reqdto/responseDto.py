class MyCustomException(Exception):
    def __init__(self, status_code : int,code:int, msg:str):
        self.status_code = status_code
        self.code = code
        self.msg = msg
        

def MyCustomResponse(code : int, msg : str):
	return {"code" : code, "msg" : msg, "data" : {"code":code, "msg": msg}}

def MatchingResponse(code : int, msg : str, id : str):
	return {"code" : code, "msg" : msg, "data" : {"code":code, "msg": msg, "matchingId": id}}