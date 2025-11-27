from sqlalchemy import Column, String, Integer,ForeignKey, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    level = Column(Integer, default=1)
    goals = Column(JSON, default=list)
    habits = Column(JSON, default=list)
    experience = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.now(timezone.utc))
    ai_settings = Column(JSON, default={"enable": True, "model": "Qwen2.5-7B-Instruct"})

    generated_quests = relationship("GeneratedQuest", back_populates="player")
    user_quests = relationship("UserQuest", back_populates="player")

    def add_experience(self, points:int):
        self.experience += points
        self.check_level_up()

    def check_level_up(self):
        exp_needed = self.level ** 2 * 100
        while exp_needed <= self.experience:
            self.level += 1
            self.experience -= exp_needed
            exp_needed = self.level ** 2 * 100

class GeneratedQuest(Base):
    __tablename__ = "generated_quest"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    steps = Column(JSON, nullable=False)
    estimated_time = Column(String)
    difficulty = Column(String)
    category = Column(String)
    total_points = Column(Integer)
    ai_generated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    ai_model = Column(String, nullable=True)
    generation_prompt = Column(Text, nullable=True)

    player_id = Column(Integer, ForeignKey("players.id"))
    player = relationship("Player", back_populates="generated_quest")
    quest = relationship("UserQuest", back_populates="generated_quest")

class UserQuest(Base):
    __tablename__ = "user_quest"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    points = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey("players.id"))
    user = relationship("Player", back_populates="user_quest")

    quest_id = Column(Integer, ForeignKey("generated_quest.id"), nullable=True)
    quest = relationship("GeneratedQuest", back_populates="user_quest")