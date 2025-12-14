from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from database.db import get_db
from services.user_service import UserService
from database.models import Player


load_dotenv()

SECRETE_KEY = os.getenv("SECRET_KEY")
ALGORITHMS = "HS256"

security = HTTPBearer

async def get_current_user(
        credetials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> Player:

    token = credetials.credentials

    try:
        payload = jwt.decode(token, SECRETE_KEY, algorithms=ALGORITHMS)
        username: str = payload.get("sub")
        if username is None:
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authentication": "Bearer"}
        )

    user_service = UserService(db)
    user = await user_service.get_player_by_username(username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authentication": "Bearer"}
        )

    return user

async def get_current_active_user(current_player: Player = Depends(get_current_user)) -> Player:
    if not current_player:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_player