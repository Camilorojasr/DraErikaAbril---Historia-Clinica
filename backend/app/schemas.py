from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel


class StateIn(BaseModel):
    data: Dict[str, Any]


class StateOut(BaseModel):
    data: Dict[str, Any]
    updated_at: datetime

    class Config:
        from_attributes = True
