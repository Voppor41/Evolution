import json
import os
import logging
from typing import Dict, Any, AsyncGenerator
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AIService:

    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.default_model = os.getenv("AI_MODEL")

        if not self.api_key:
            logger.warning("AI api key not found")
            self.client = None
        else:
            try:
                self.client = InferenceClient(
                    token=self.api_key,
                    timeout=30
                )
                logger.info("AI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AI client: {e}")
                self.client = None

    async def generate_quest(
            self,
            user_data: Dict[str, Any],
            stream: bool = False
    ) -> AsyncGenerator[str, None] | Dict[str, Any]:
        """
        Генерирует персонализированный квест для пользователя

        Args:
            user_data: Данные пользователя (уровень, цели, привычки)
            stream: Режим потоковой генерации

        Returns:
            Сгенерированный квест в формате JSON или поток данных
        """
        if not self.client:
            logger.info("Using fallback quest generation")
            return self._generate_fallback_quest(user_data)

        try:
            prompt = self._build_quest_prompt(user_data)  # Исправлено _built -> _build

            if stream:
                return self._generate_streaming(prompt)
            else:
                return await self._generate_complete(prompt)  # Добавлен await

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return self._generate_fallback_quest(user_data)

    async def _build_quest_prompt(self, user_data: Dict[str, Any]) -> str:
        return f"""
                Ты — наставник в RPG-игре о саморазвитии. создай персональный квест для игрока на основе его данных:
                Уровень: {user_data.get('level', 1)}
                Цели: {', '.join(user_data.get('goals', []))}
                Привычки: {', '.join(user_data.get('habits', []))}
                Предпочтения: {user_data.get('preferences', {})}

                Создай квест который:
                1. Соответствует целям пользователя
                2. Учитывает его привычки и уровень
                3. Состоит из 3-5 конкретных шагов (задач)
                4. Имеет увлекательное описание и название
                5. Указывает примерное время выполнения
                6. Имеет соответствующую сложность (easy, medium, hard)
                7. Относится к одной из категорий: здоровье, обучение, продуктивность, творчество, спорт

                Верни ответ ТОЛЬКО в формате JSON:
                {{
                    "title": "Название квеста",
                    "description": "Описание квеста",
                    "steps": [
                        {{
                            "title": "Конкретное название задачи",
                            "description": "Детальное описание что нужно сделать", 
                            "points": 10,
                            "estimated_time": "15 минут"
                        }}
                    ],
                    "estimated_time": "Общее время выполнения",
                    "difficulty": "easy/medium/hard",
                    "category": "категория"
            }}"""

    async def _generate_complete(self, prompt) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                prompt=prompt,
                model=self.default_model,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                return_full_text=False
            )
            return self._parse_ai_response(response)

        except Exception as e:
            logger.error(f"AI completion error: {e}")
            raise


    async def _generate_streaming(self, prompt) -> AsyncGenerator[str, None]:
        try:
            stream = self.client.chat.completions.create(
                prompt=prompt,
                model=self.default_model,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                stream=True
            )

            for chunk in stream:
                if hasattr(chunk, 'text'):
                    yield chunk.text
                else:
                    yield str(chunk)

        except Exception as e:
            logger.info(f"AI streaming generate error: {e}")
            yield json.dumps(self._generate_fallback_quest({}))


    def _parse_ai_response(self, response: str) -> Dict[str, Any]:

        try:
            cleaned_response = response.strip()

            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.find('}') + 1

            if start_idx != -1 and end_idx != 0:
                json_str = cleaned_response[start_idx:end_idx]
                quest_data = json.loads(json_str)

                required_field = ['title', 'description', 'steps', 'difficulty', 'category']
                if all(field in quest_data for field in required_field):
                    return quest_data

            logger.warning("AI response parsing failed, using fallback")
            return self._generate_fallback_quest({})

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}, response:{response}")
            return self._generate_fallback_quest({})

    def _generate_fallback_quest(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Резервная генерация квеста если AI недоступен"""
        goals = user_data.get('goals', [])
        level = user_data.get('level', 1)

        # Более интеллектуальный fallback на основе целей
        goal_text = ' '.join(goals).lower() if goals else ''

        if any(word in goal_text for word in ['здор', 'спорт', 'фитнес', 'трениров']):
            return {
                "title": "Путь к здоровому образу жизни",
                "description": "Начни свое путешествие к улучшению здоровья и физической формы",
                "steps": [
                    {
                        "title": "Утренняя энергия",
                        "description": "Выполни 15-минутную утреннюю зарядку",
                        "points": 25,
                        "estimated_time": "15 минут"
                    },
                    {
                        "title": "Водный баланс",
                        "description": "Выпей 2 литра воды в течение дня",
                        "points": 20,
                        "estimated_time": "Весь день"
                    },
                    {
                        "title": "Здоровый перекус",
                        "description": "Замени один вредный перекус на фрукты или овощи",
                        "points": 15,
                        "estimated_time": "5 минут"
                    }
                ],
                "total_points": 60,
                "difficulty": "easy",
                "category": "health",
                "duration": "1 день"
            }
        elif any(word in goal_text for word in ['уч', 'обуч', 'книг', 'чтение']):
            return {
                "title": "Квест знаний",
                "description": "Открой для себя новые горизонты обучения",
                "steps": [
                    {
                        "title": "Чтение на развитие",
                        "description": "Прочитай одну главу из образовательной книги",
                        "points": 30,
                        "estimated_time": "30 минут"
                    }
                ],
                "total_points": 30,
                "difficulty": "easy",
                "category": "learning",
                "duration": "1 день"
            }

        # Базовый квест по умолчанию
        return {
            "title": "Начало пути героя",
            "description": "Сделай первый шаг к своим целям",
            "steps": [
                {
                    "title": "Планирование дня",
                    "description": "Составь план на сегодня и выдели 3 главные задачи",
                    "points": 30,
                    "estimated_time": "10 минут"
                }
            ],
            "total_points": 30,
            "difficulty": "easy",
            "category": "productivity",
            "duration": "1 день"
        }