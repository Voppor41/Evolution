from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from database.db import get_db
from services.user_service import UserService
from database.schemas import PlayerCreate, PlayerResponse, PlayerUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/players", tags=["players"])

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(player_data: PlayerCreate, user_service: UserService = Depends(get_user_service)):

    try:
        player = await user_service.create_player(
            username=player_data.username,
            email=player_data.email,
            password=player_data.password,
            goals=player_data.goals
        )
        return player

    except Exception as e:
        logger.error(f"Error creating player: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Iternal server error")

@router.get("/{player_id", response_model=PlayerResponse)
async def get_player(player_id: int, user_service: UserService = Depends(get_user_service)):

    player = await user_service.get_player_by_id(player_id)

    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    return player

@router.put("/{player_id}/goals", response_model=PlayerResponse)
async def update_player_goals(player_id: int,
                              goals_update: PlayerUpdate,
                              user_service: UserService = Depends(get_user_service)):

    try:
        player = await user_service.update_player_goals(player_id, goals_update.goals)
        return player
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{player_id}/quest")
async def get_player_quest(player_id: int,
                           completed: bool = None,
                           user_service: UserService = Depends(get_user_service)):

    try:
        quest = await user_service.get_player_quest(player_id, completed)
        return {"quest": quest, "count": len(quest)}

    except Exception as e:
        logger.error(f"Error founding player quest: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Iternal server error")
    