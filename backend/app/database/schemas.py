from pydantic import BaseModel, EmailStr, constr
from datetime import datetime, UTC
from typing import Optional, List

class PlayerBase(BaseModel):
    username: str
    email: EmailStr

class PlayerCreate(BaseModel):
    username: str
    email: EmailStr
    password: constr(min_length=8, max_length=20)

class Player(PlayerBase):
    id: int
    lvl: int
    experience: int
    created_at: datetime.now(UTC)
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True

class PlayerPreferences(BaseModel):
    preferred_categories: List[str]
    time_availability: str = "medium"
    difficult_preference: str = "medium"     #easy, medium, hard

class PlayerUpdate(BaseModel):
    goals: Optional[List[str]]
    habits: Optional[List[str]]
    preferences: Optional[List[str]]

class PlayerLogin(BaseModel):
    username: str
    password: str
    is_verified: bool

class QuestBase(BaseModel):
    title: str
    description: Optional[str] = None
    points: int = 0

class QuestCreate(BaseModel):
    pass

class Quest(QuestBase):
    id: int
    player_id: int
    is_completed: bool
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attribute = True

class QuestComplete(BaseModel):
    is_completed: bool = True

class QuestStep(BaseModel):
    title: str
    description: str
    points: int
    estimated_time: str

class AiQuestBase(BaseModel):
    title: str
    description: str
    steps: List[QuestStep]
    estimated_time: str
    difficulty: str
    category: str

class AiQuestCreate(AiQuestBase):
    pass


class AiQuest(AiQuestBase):
    id: int
    user_id: int
    ai_generated: bool
    ai_model: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class QuestGAiResponse(BaseModel):
    quest: AiQuest
    tasks: List[Quest]

class AISettings(BaseModel):
    enabled: bool = True
    model: str = "Qwen2.5-7B-Instruct"
    temperature: float = 0.7
    max_tokens: int = 1024

class QuestGAiRequest(BaseModel):
    theme: Optional[str] = None
    category: Optional[str] = None
    stream: bool = False
    ai_settings: Optional[AISettings]