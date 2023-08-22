import sys
import os
from enum import Enum
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from pydantic import BaseModel, Field
from datetime import datetime
from geojson import Point
#from enum.Enum import UserRole

class Status(str, Enum):
    CANCEL = 'CANCEL'
    PROCESSING = 'PROCESSING'
    COMPLETE = "COMPLETE"
    NOSHOW = "NOSHOW"

class User(BaseModel):
    id : str
    userName : str
    userNickname : str
    #userRole : UserRole
    createdAt : datetime
    modifiedAt : datetime
    


class Cafe(BaseModel):
    id : str
    name : str
    phoneNumber : str
    address : str
    imageUrl : str
    instagramUrl : str
    coordinate : Point
    createdAt : datetime
    modifiedAt : datetime


class Matching(BaseModel):
    userId : str
    cafeId: str
    seating : int
    matchingTime : datetime = Field(default_factory=datetime.now)
    status : Status
