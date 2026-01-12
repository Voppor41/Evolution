from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from dependencies.auth import get_current_user
from database.db import get_db
from services.stats_service import StatsService
from database.models import Player

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

def get_stats_service(db: Session = Depends(get_db)) -> StatsService:

@router.get("/")
async def get_dashboard(current_user: Player = Depends(get_current_user),
                        stats_service: StatsService = Depends(get_stats_service)):
    try:

        dashboard = await stats_service.get_player_dashboard(current_user.id)
        return dashboard
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10, stats_service: StatsService = Depends(get_stats_service), db: Session = Depends(get_db)):
    try:
        top_players = db.query(Player).order_by(Player.level.desc(), Player.experience.desc()).limit(limit).all

        return [
            {
                "rank": i + 1,
                "username": player.username,
                "level": player.level,
                "experience": player.experience,
                "totall_quests": player.stats.total_quests_completed if player.stats else 0
            }
            for i, player in enumerate(top_players)
        ]

    except Exception as e:
        logger.error(f"Error loading ledearboard: {e}")
        raise HTTPException(status_code=500, detail="Iternal server error")
