from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    session_id: Optional[int] = None
    topic: Optional[str] = Field(default=None, max_length=100)


class ChatResponse(BaseModel):
    response: str
    session_id: int


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    topic: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    session_id: int
    messages: List[MessageOut]
