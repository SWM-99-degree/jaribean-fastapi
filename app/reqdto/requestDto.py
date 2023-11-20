from pydantic import BaseModel
from typing import Dict, Optional

class MatchingReqDto(BaseModel):
    peopleNumber : int
    latitude : float
    longitude : float



class MatchingCafeReqDto(BaseModel):
    peopleNumber : int
    userId : str

class MatchingCancelReqDto(BaseModel):
    matchingId : str = None
