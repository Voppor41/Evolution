import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from database.db import engine, Base
from database import models
from routers.player_router import router as player_router
from routers.quest_router import router as quest_router

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Evolution API",
    description="RPG-приложение для саморазвития с AI-генерацией квестов",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(player_router)
app.include_router(quest_router)

@app.get("/")
async def root():
    return {"message": "Evolution API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)