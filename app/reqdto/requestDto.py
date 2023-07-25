from pydantic import BaseModel
from typing import Dict, Optional

class MatchingReqDto(BaseModel):
    userId : str = None
    number : int
    point : Optional[Dict[str, float]] = None
    cafeId : Optional[str] = None

class MatchingCancelReqDto(BaseModel):
    machingId : str
    cafeId : str
