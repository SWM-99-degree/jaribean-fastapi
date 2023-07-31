import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from pydantic import BaseModel, Field
from datetime import datetime
from geojson import Point
#from enum.Enum import UserRole

class Matching(BaseModel):
    userId : str
    cafeId : str
    number : int
    matchingTime : datetime = Field(default_factory=datetime.now)



class User(BaseModel):
    userName : str
    userNickname : str
    #userRole : UserRole
    createdAt : datetime
    modifiedAt : datetime
    


class Cafe(BaseModel):
    name : str
    phoneNumber : str
    address : str
    imageUrl : str
    coordinate : Point
    #userRole : UserRole
    createdAt : datetime
    modifiedAt : datetime

