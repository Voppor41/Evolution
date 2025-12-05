import asyncio
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import logging
import bcrypt

from database.models import GeneratedQuest, UserQuest, Player
from .ai_service import AIService
from .auth_service import AuthService
from .auth_service import create_access_token

logger = logging.getLogger(__name__)

class UserService:

    def __init__(self, db:Session):
        self.db = db
        try:
            self.ai_service = AIService()
            logger.info("AI service initialized successfully")
        except Exception as e:
            logger.error(f"Error initialized AI service: {e}")
            self.ai_service = None

    async def create_player(self, username: str, email:str, password:str, goals: list=None) -> Player:
        try:
            existing_user = self.db.query(Player).filter((Player.username == username) | (Player.email == email)).first()

            if existing_user:
                raise ValueError("This username or email already exist")

            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            hashed_password_str = hashed_password.decode('utf-8')

            player = Player(
                username=username,
                email=email,
                hashed_password=hashed_password_str,
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

    async def login_player(self, username:str, password:str) -> Player:
        try:
            player = self.db.query(Player).filter(Player.username == username).first()

            if not player:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверное имя пользователя или пароль"
                )

            # Проверяем пароль (если используете bcrypt напрямую)
            import bcrypt
            if not bcrypt.checkpw(password.encode('utf-8'), player.hashed_password.encode('utf-8')):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверное имя пользователя или пароль"
                )

            # Создаем JWT токен
            access_token = AuthService.create_access_token(
                data={"sub": player.username, "id": player.id}
            )

            logger.info(f"Успешный вход пользователя: {username}")

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "player": player
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при аутентификации: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка сервера"
            )


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
