from pydantic import BaseModel
from typing import Dict, Optional

class MachingReqDto(BaseModel):
    userId : str
    number : int
    point : Dict[str, float]
    cafeId : Optional[str] = None
