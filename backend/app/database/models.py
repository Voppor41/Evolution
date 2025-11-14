from sqlalchemy import Column, String, Integer,ForeignKey, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

Base = declarative_base

class Player:
    __tablename__ = "player"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    level = Column(Integer, default=1)
    habits = Column(JSON, default=list)
    experience = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.now(UTC))
    ai_settings = Column(JSON, default={"enable": True, "model": "Qwen2.5-7B-Instruct"})

    quest = relationship("UserQuests", back_populates="player")

    def add_experience(self, points:int):
        self.experience += points
        self.check_level_up()

    def check_level_up(self):
        exp_needed = self.level ** 2 * 100
        while exp_needed <= self.experience:
            self.level += 1
            self.experience -= exp_needed
            exp_needed = self.level ** 2 * 100

class GeneratedQuest:
    __tablename__ = "generated_quest"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    steps = Column(Text, nullable=False)
    estimated_time = Column(String)
    difficulty = Column(String)
    ai_generated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    ai_model = Column(String, nullable=True)
    generation_prompt = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("player.id"))
    user = relationship("Player", back_populates="generated_quest")
    quest = relationship("UserQuest", back_populates="generated_quest")

class UserQuest:
    __tablename__ = "user_quest"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    points = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey("player.id"))
    user = relationship("Player", back_populates="user_quest")

    quest_id = Column(Integer, ForeignKey("generated_quest.id"), nullable=True)
    quest = relationship("GeneratedQuest", back_populates="user_quest")