from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from database.models import Player, PlayerStats, UserQuest, GeneratedQuest

logger = logging.getLogger(__name__)

class StatsService:

    def __init__(self, db: Session):
        self.db = db

    async def update_stats_on_quest_complete(self, player_id: int, quest: UserQuest):

        try:
            player = await self.db.query(Player).filter(Player.id == player_id).first
            if not player:
                raise ValueError("Player not found")

            stats = player.stats
            if not stats:
                stats = PlayerStats(player_id=player_id)
                self.db.add(stats)

            stats.total_quest_completed += 1
            stats.total_experience_earned += quest.points

            if quest.generated_quest:
                category = quest.generated_quest.category.lower()
                if category == "health":
                    stats.health_quests_completed += 1
                elif category == "learning":
                    stats.learning_quests_completed += 1
                elif category == "productivity":
                    stats.productivity_quests_completed += 1
                elif category == "creativity":
                    stats.creativity_quests_completed += 1
                elif category == "sports":
                    stats.sports_quests_completed += 1

            stats.last_active_date = datetime.now(timezone.utc)

            self._update_streak(stats)

            self.db.commit()
            logger.info(f"Update stat for player {player_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating stats: {e}")
            raise

    def _update_streak(self, stats: PlayerStats):

        now = datetime.now(timezone.utc).date()
        last_time_active = stats.last_active_date.date()

        if last_time_active == now:
            return
        elif last_time_active == now - timedelta(days=1):
            stats.current_streak += 1
        else:
            stats.current_streak = 1

        if stats.current_streak > stats.longest_streak:
            stats.longest_streak = stats.current_streak

    async def get_player_dashboard(self, player_id: int) -> Dict[str, Any]:

        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise ValueError("Player not found")

        stats = player.stats
        if not stats:
            stats = PlayerStats(player_id=player_id)

        # Собираем активные квесты
        active_quests = self.db.query(UserQuest).filter(
            UserQuest.player_id == player_id,
            UserQuest.is_completed == False
        ).all()

        # Рассчитываем прогресс до следующего уровня
        current_level_exp = (player.level ** 2) * 100
        next_level_exp = ((player.level + 1) ** 2) * 100
        exp_progress = player.experience - current_level_exp
        exp_needed = next_level_exp - current_level_exp
        level_progress = (exp_progress / exp_needed) * 100 if exp_needed > 0 else 100

        return {
            "player": {
                "id": player.id,
                "username": player.username,
                "level": player.level,
                "experience": player.experience,
                "goals": player.goals,
                "next_level_exp": next_level_exp,
                "level_progress": round(level_progress, 2)
            },
            "stats": {
                "total_quests_completed": stats.total_quests_completed,
                "total_experience_earned": stats.total_experience_earned,
                "total_days_active": stats.total_days_active,
                "current_streak": stats.current_streak,
                "longest_streak": stats.longest_streak,
                "by_category": {
                    "health": stats.health_quests_completed,
                    "learning": stats.learning_quests_completed,
                    "productivity": stats.productivity_quests_completed,
                    "creativity": stats.creativity_quests_completed,
                    "sports": stats.sports_quests_completed
                }
            },
            "active_quests": [
                {
                    "id": q.id,
                    "title": q.title,
                    "points": q.points,
                    "created_at": q.created_at.isoformat()
                }
                for q in active_quests[:5]  # Последние 5 активных квестов
            ],
            "achievements": await self._get_player_achievements(player_id)
        }

    def _get_player_achievements(self, player_id: int) -> list:

        player = self.db.query(Player).filter(Player.id == player_id).first()
        stats = player.stats

        achievements = []

        if player.level >= 10:
            achievements.append({"name": "Новичок", "description": "Достиг 10 уровня"})
        if player.level >= 20:
            achievements.append({"name": "Опытный", "description": "Достиг 20 уровня"})

            # Достижения по квестам
        if stats and stats.total_quests_completed >= 40:
            achievements.append({"name": "Искатель", "description": "Выполнил 40 квестов"})

            # Достижения по стрику
        if stats and stats.current_streak >= 7:
            achievements.append({"name": "Последовательный", "description": "7 дней подряд"})

        return achievements