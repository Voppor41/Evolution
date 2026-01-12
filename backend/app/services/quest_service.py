import asyncio
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import json

from database.models import Player, GeneratedQuest, UserQuest
from .ai_service import AIService
from .stats_service import StatsService

logger = logging.getLogger(__name__)

class QuestService:

    def __init__(self, db: Session):
        self.db = db
        self.stats_service = StatsService(db)
        try:
            self.ai_service = AIService()
            logger.info("AI service initialized successfully in QuestService")
        except Exception as e:
            logger.error(f"Failed initialized AI service: {e}")
            self.ai_service = None

    async def generate_quest_for_player(self, player_id: int) -> UserQuest:

        try:
            player = self.db.query(Player).filter(Player.id == player_id).first()

            if not player:
                raise ValueError(f"Player with this id: {player_id} not found")

            if not self.ai_service or not hasattr(self.ai_service, 'generate_quest'):
                logger.warning("AI service not available, using fallback")
                return await self._create_fallback_quest(player_id)

            user_data = {
                'level': player.level,
                'goals': player.goals,
                'habits': player.habits or [],
                'preferences': player.ai_settings or {}
            }

            quest_data = await self.ai_service.generate_quest(user_data)

            # Сохраняем сгенерированный шаблон квеста
            generated_quest = GeneratedQuest(
                title=quest_data["title"],
                description=quest_data["description"],
                steps=json.dumps(quest_data["steps"]),
                estimated_time=quest_data.get("estimated_time"),
                difficulty=quest_data["difficulty"],
                category=quest_data.get("category", "general"),
                total_points=quest_data.get("total_points", 0),
                ai_generated=True,
                player_id=player_id
            )

            self.db.add(generated_quest)
            self.db.commit()
            self.db.refresh(generated_quest)

            # Создаем персональный квест для игрока
            user_quest = UserQuest(
                title=quest_data["title"],
                description=quest_data["description"],
                points=quest_data.get("total_points", 0),
                player_id=player_id,
                generated_quest_id=generated_quest.id
            )

            self.db.add(user_quest)
            self.db.commit()
            self.db.refresh(user_quest)

            logger.info(f"Generated quest '{quest_data['title']}' for player {player_id}")
            return user_quest

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating quest for player {player_id}: {e}")
            # Используем fallback в случае ошибки
            return await self._create_fallback_quest(player_id)

    async def _create_fallback_quest(self, player_id: int) -> UserQuest:
        """Создание резервного квеста если AI недоступен"""
        try:
            # Простой fallback квест
            user_quest = UserQuest(
                title="Базовый квест продуктивности",
                description="Начни свой путь к эффективности",
                points=30,
                player_id=player_id
            )

            self.db.add(user_quest)
            self.db.commit()
            self.db.refresh(user_quest)

            logger.info(f"Created fallback quest for player {player_id}")
            return user_quest

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating fallback quest: {e}")
            raise

    async def create_manual_quest(self, player_id: int, quest_data: Dict[str, Any]) -> UserQuest:

        try:
            user_quest = UserQuest(
                title=quest_data["title"],
                description=quest_data.get("description", ""),
                points=quest_data.get("points", 0),
                player_id=player_id
            )

            self.db.add(user_quest)
            self.db.commit()
            self.db.refresh(user_quest)

            return user_quest

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating manual quest: {e}")
            raise

    async def complete_quest(self, quest_id: int) -> Player:
        """Завершение квеста и начисление опыта"""
        try:
            quest = self.db.query(UserQuest).filter(UserQuest.id == quest_id).first()
            if not quest:
                raise ValueError(f"Quest with id {quest_id} not found")

            if quest.is_completed:
                raise ValueError("Quest already completed")

            # Отмечаем квест как выполненный
            quest.is_completed = True
            quest.completed_at = datetime.now(timezone.utc)

            # Начисляем опыт игроку
            player = quest.player
            player.add_experience(quest.points)

            await self.stats_service.update_stats_on_quest_complete(player.id, quest)

            self.db.commit()
            self.db.refresh(player)

            logger.info(f"Completed quest {quest_id}. Player {player.id} gained {quest.points} experience")
            return player

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing quest {quest_id}: {e}")
            raise

    async def get_quest_by_id(self, quest_id: int) -> Optional[UserQuest]:
        """Получение квеста по ID"""
        return self.db.query(UserQuest).filter(UserQuest.id == quest_id).first()

    async def get_active_quests(self, player_id: int) -> List[UserQuest]:
        """Получение активных (незавершенных) квестов игрока"""
        return self.db.query(UserQuest).filter(
            UserQuest.player_id == player_id,
            UserQuest.is_completed == False
        ).order_by(UserQuest.created_at.desc()).all()

    async def delete_quest(self, quest_id: int) -> bool:
        """Удаление квеста"""
        try:
            quest = await self.get_quest_by_id(quest_id)
            if not quest:
                return False

            self.db.delete(quest)
            self.db.commit()

            logger.info(f"Deleted quest {quest_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting quest {quest_id}: {e}")
            raise