import asyncio
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import bcrypt

from database.models import GeneratedQuest, UserQuest, Player
from .ai_service import AIService
from .auth_service import AuthService

logger = logging.getLogger(__name__)


class UserService:

    def __init__(self, db: Session):
        self.db = db
        try:
            self.ai_service = AIService()
            logger.info("AI service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AI service: {e}")
            self.ai_service = None

    async def create_player(self, username: str, email: str, password: str, goals: list = None) -> Player:
        """Create a new player with hashed password"""
        try:
            existing_user = self.db.query(Player).filter(
                (Player.username == username) | (Player.email == email)
            ).first()

            if existing_user:
                raise ValueError("This username or email already exists")

            # Hash the password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            hashed_password_str = hashed_password.decode('utf-8')

            player = Player(
                username=username,
                email=email,
                hashed_password=hashed_password_str,
                goals=goals or [],
                level=1,
                experience=0,
                is_active=True,
                is_verified=False
            )

            self.db.add(player)
            self.db.commit()
            self.db.refresh(player)

            logger.info(f"Created new player: {player.username} (ID: {player.id})")
            return player

        except ValueError as e:
            self.db.rollback()
            logger.warning(f"Attempt to create existing user: {username}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating player: {e}")
            raise

    async def change_password(self, player_id: int, old_password: str, new_password: str) -> bool:
        """Change player's password"""
        player = await self.get_player_by_id(player_id)
        if not player:
            raise ValueError("Player not found")

        # Verify old password
        if not bcrypt.checkpw(old_password.encode('utf-8'), player.hashed_password.encode('utf-8')):
            raise ValueError("Incorrect old password")

        # Hash new password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        player.hashed_password = hashed_password.decode('utf-8')

        self.db.commit()
        return True

    async def login_player(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate player and return JWT token"""
        try:
            # Find player by username
            player = await self.get_player_by_username(username)

            if not player:
                logger.warning(f"Login attempt for non-existent user: {username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )

            # Check if account is active
            if not player.is_active:
                logger.warning(f"Login attempt for inactive account: {username}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated"
                )

            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), player.hashed_password.encode('utf-8')):
                logger.warning(f"Invalid password for user: {username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )

            # Create JWT token
            access_token = AuthService.create_access_token(
                data={"sub": player.username, "id": player.id, "email": player.email}
            )

            logger.info(f"Successful login: {username} (ID: {player.id})")

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "player": {
                    "id": player.id,
                    "username": player.username,
                    "email": player.email,
                    "level": player.level,
                    "experience": player.experience,
                    "goals": player.goals
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """Get player by ID"""
        return self.db.query(Player).filter(Player.id == player_id).first()

    async def get_player_by_username(self, username: str) -> Optional[Player]:
        """Get player by username"""
        return self.db.query(Player).filter(Player.username == username).first()

    async def update_player_goals(self, player_id: int, goals: List[str]) -> Player:
        """Update player's goals"""
        try:
            player = await self.get_player_by_id(player_id)
            if not player:
                raise ValueError(f"Player with ID {player_id} not found")

            player.goals = goals
            self.db.commit()
            self.db.refresh(player)

            logger.info(f"Updated goals for player {player_id}")
            return player

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating player goals: {e}")
            raise

    async def update_player_exp(self, player_id: int, experience: int) -> Player:
        """Add experience to player"""
        try:
            player = await self.get_player_by_id(player_id)

            if not player:
                raise ValueError(f"Player with ID {player_id} not found")

            # Исправлено: add_experience вместо add_experince
            player.add_experience(experience)  # ✅ Исправлено
            self.db.commit()
            self.db.refresh(player)

            logger.info(f"Added {experience} experience to player {player_id}. New level: {player.level}")
            return player

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding experience to player {player_id}: {e}")
            raise

    async def get_player_quests(self, player_id: int, completed: bool = None) -> List[UserQuest]:
        """Get player's quests"""
        query = self.db.query(UserQuest).filter(UserQuest.player_id == player_id)

        if completed is not None:
            query = query.filter(UserQuest.is_completed == completed)

        return query.order_by(UserQuest.created_at.desc()).all()