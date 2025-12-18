from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class PlayerBase(BaseModel):
    username: str
    email: EmailStr
    goals: List[str] = Dict

class PlayerCreate(PlayerBase):
    password: str

class PlayerUpdate(BaseModel):
    goals: List[str]

class PlayerResponse(PlayerBase):
    id: int
    level: int
    experience: int
    is_active: bool
    is_verified: bool
    registered_at: datetime

    class Config:
        from_attributes = True

class QuestStep(BaseModel):
    title: str
    description: str
    points: int
    estimated_time: str

class QuestBase(BaseModel):
    title: str
    description: str
    points: int = 0

class QuestCreate(QuestBase):
    pass

class QuestResponse(QuestBase):
    id: int
    is_completed: bool
    created_at: datetime
    completed_at: Optional[datetime]
    player_id: int

    class Config:
        from_attributes = True

class QuestGenerationResponse(BaseModel):
    quest: QuestResponse
    generated_quest_id: Optional[int]
    ai_generated: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class PlayerLogin(BaseModel):
    username: str
    password: str