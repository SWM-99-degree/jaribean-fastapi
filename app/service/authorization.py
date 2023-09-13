import threading
import json
import os
from typing import Optional
import jwt
from fastapi import  Header
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from reqdto.responseDto import MyCustomException, MyCustomResponse

async def verify_jwt_token(ACCESS_AUTHORIZATION: Optional[str] = Header(None, convert_underscores = False)):
    try:
        payload = jwt.decode(ACCESS_AUTHORIZATION, os.getenv("SECRET_KEY"), algorithms=["HS512"])
        return payload
    except jwt.ExpiredSignatureError:
        raise MyCustomException(401, -1, "토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
	    raise MyCustomException(401, -1, "토큰이 유효하지 않습니다.")