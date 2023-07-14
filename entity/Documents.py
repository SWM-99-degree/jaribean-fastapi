import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from pydantic import BaseModel, Field
from datetime import datetime
from geojson import Point
from enum.Enum import UserRole

class Matching(BaseModel):
    id : str = Field(alias = "_id")
    userId : str
    cafeId : str
    number : int
    matchingTime : datetime


class User(BaseModel):
    id : str = Field(alias = "_id")
    userName : str
    userNickname : str
    userRole : UserRole
    createdAt : datetime
    modifiedAt : datetime
    


class Cafe(BaseModel):
    id : str = Field(alias = "_id")
    cafeName : str
    cafePhoneNumber : str
    cafeAddress : str
    cafeImg : str
    coordinate : Point
    userRole : UserRole
    createdAt : datetime
    modifiedAt : datetime

