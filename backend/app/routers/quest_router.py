from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from database.db import get_db
from services.quest_service import QuestService
from services.user_service import UserService
from database.schemas import QuestResponse, QuestCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quests", tags=["quests"])

def get_quest_service(db: Session = Depends(get_db)) -> QuestService:
    return QuestService(db)

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

@router.post("/generate/{player_id}", response_model=QuestResponse)
async def generate_quest(player_id: int,
                         quest_service: QuestService = Depends(get_user_service),
                         user_service: UserService = Depends(get_user_service)):

    try:

        player = user_service.get_player_by_id(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )

        quest = await quest_service.generate_quest_for_player(player_id)
        return quest

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating quest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quest"
        )


@router.post("/{quest_id}/complete", response_model=QuestResponse)
async def complete_quest(
        quest_id: int,
        quest_service: QuestService = Depends(get_quest_service)
):
    """Завершение квеста и начисление опыта"""
    try:
        player = await quest_service.complete_quest(quest_id)
        # Возвращаем обновленный квест
        quest = await quest_service.get_quest_by_id(quest_id)
        return quest
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error completing quest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete quest"
        )


@router.get("/player/{player_id}/active", response_model=list[QuestResponse])
async def get_active_quests(
        player_id: int,
        quest_service: QuestService = Depends(get_quest_service),
        user_service: UserService = Depends(get_user_service)
):
    """Получение активных квестов игрока"""
    try:
        # Проверяем существование игрока
        player = await user_service.get_player_by_id(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )

        quests = await quest_service.get_active_quests(player_id)
        return quests
    except Exception as e:
        logger.error(f"Error getting active quests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/manual/{player_id}", response_model=QuestResponse)
async def create_manual_quest(
        player_id: int,
        quest_data: QuestCreate,
        quest_service: QuestService = Depends(get_quest_service),
        user_service: UserService = Depends(get_user_service)
):
    """Создание квеста вручную"""
    try:
        # Проверяем существование игрока
        player = await user_service.get_player_by_id(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )

        quest = await quest_service.create_manual_quest(player_id, quest_data.dict())
        return quest
    except Exception as e:
        logger.error(f"Error creating manual quest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quest"
        )


@router.delete("/{quest_id}")
async def delete_quest(
        quest_id: int,
        quest_service: QuestService = Depends(get_quest_service)
):
    """Удаление квеста"""
    try:
        success = await quest_service.delete_quest(quest_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quest not found"
            )
        return {"message": "Quest deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting quest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quest"
        )