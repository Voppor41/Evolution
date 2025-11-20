import asyncio
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import logging

from ..database.models import GeneratedQuest, UserQuest, Player
from ai_service import AIService

logger = logging.getLogger(__name__)

class UserService:

    def __init__(self, db:Session):
        self.db = db
        self.ai_service = AIService()

    async def create_player(self, username: str, email:str, password:str, goals: list=None) -> Player:
        try:
            existing_user = self.db.query(Player).filter((Player.username == username) | (Player.email == email)).first()

            if existing_user:
                raise ValueError("This username or email already exist")

            player = Player(
                username=username,
                email=email,
                hashed_password=password,
                goals=goals or [],
                level=1,
                experience=0
            )

            self.db.add(player)
            self.db.commit()
            self.db.refresh(player)

            logger.info(f"Create new player {player}")
            return player
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating player: {e}")
            raise

    async def get_player_by_id(self, player_id: int) -> Optional[Player]:
        return self.db.query(Player).filter(Player.id == player_id).first()

    async def get_player_by_username(self, username) -> Optional[Player]:
        return self.db.query(Player).filter(Player.username == username).first()

    async def update_player_goals(self, player_id:int, goals: List[str]) -> Player:

        try:
            player = await self.get_player_by_id(player_id)
            if not player:
                raise ValueError(f"Player not found")

            player.goals = goals
            self.db.commit()
            self.db.refresh(player)

            return player

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error of update player goals: {e}")
            raise

    async def update_player_exp(self, player_id: int, experience: int) -> Player:

        try:
            player = await self.get_player_by_id(player_id)

            if not player:
                raise ValueError("Player not found")

            player.add_experince(experience)
            self.db.commit()
            self.db.refresh(player)

            logger.info(f"Added {experience} experience to player {player_id}. New level: {player.level}")

            return player

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding experience to player: {e}")
            raise

    async def get_player_quest(self, player_id: int, completed:bool = None) -> List[UserQuest]:
        query = self.db.query(UserQuest).filter(UserQuest.player_id == player_id)

        if completed is not None:
            query = query.filter(UserQuest.is_completed == completed)

        return query.order_by(UserQuest.created_at.desc()).all()
