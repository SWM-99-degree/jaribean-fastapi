from pydantic import BaseModel
from typing import Dict, Optional

class MachingReqDto(BaseModel):
    userId : str
    number : int
    point : Optional[Dict[str, float]] = None
    cafeId : Optional[str] = None

class MachingCancelReqDto(BaseModel):
    machingId : str
