from sqlalchemy import select, func, case
from src.core.database.session import async_session
from src.core.database.models import User, GameStat, Chat
from src.core.database.schemas import ChatSettings
from datetime import datetime

class DbService:
    @staticmethod
    async def save_game_result(user_id: int, full_name: str, username: str, game_type: str, result: str):
        async with async_session() as session:
            # 1. Ensure user exists
            user = await session.get(User, user_id)
            if not user:
                user = User(id=user_id, full_name=full_name, username=username)
                session.add(user)
            else:
                user.full_name = full_name
                user.username = username
            
            # 2. Add game stat
            stat = GameStat(
                user_id=user_id,
                game_type=game_type,
                result=result,
                played_at=datetime.utcnow()
            )
            session.add(stat)
            
            # 3. Reward with diamonds for win
            if result == "win":
                user.diamonds = (user.diamonds or 0) + 100
                
            await session.commit()

    @staticmethod
    async def get_user_stats(user_id: int):
        async with async_session() as session:
            res = await session.execute(
                select(
                    func.count(GameStat.id).label("total"),
                    func.sum(case((GameStat.result == "win", 1), else_=0)).label("wins"),
                    func.sum(case((GameStat.result == "loss", 1), else_=0)).label("losses")
                ).where(GameStat.user_id == user_id, GameStat.game_type == "codenames")
            )
            return res.first()

    @staticmethod
    async def get_chat_settings(chat_id: int) -> ChatSettings:
        async with async_session() as session:
            chat = await session.get(Chat, chat_id)
            if not chat or not chat.settings:
                return ChatSettings()
            return ChatSettings(**chat.settings)

    @staticmethod
    async def update_chat_settings(chat_id: int, settings: ChatSettings):
        async with async_session() as session:
            chat = await session.get(Chat, chat_id)
            if not chat:
                chat = Chat(id=chat_id, title=f"Chat {chat_id}")
                session.add(chat)
            chat.settings = settings.model_dump()
            await session.commit()

    @staticmethod
    async def get_system_setting(key: str) -> dict:
        async with async_session() as session:
            from src.core.database.models import SystemSettings
            res = await session.execute(select(SystemSettings).where(SystemSettings.key == key))
            item = res.scalar_one_or_none()
            return item.value if item else {}

    @staticmethod
    async def update_system_setting(key: str, value: dict):
        async with async_session() as session:
            from src.core.database.models import SystemSettings
            res = await session.execute(select(SystemSettings).where(SystemSettings.key == key))
            item = res.scalar_one_or_none()
            if not item:
                item = SystemSettings(key=key, value=value)
                session.add(item)
            else:
                item.value = value
            await session.commit()

    @staticmethod
    async def get_user_diamonds(user_id: int) -> int:
        async with async_session() as session:
            user = await session.get(User, user_id)
            return user.diamonds if user else 0

    @staticmethod
    async def update_user_diamonds(user_id: int, delta: int) -> bool:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            if (user.diamonds or 0) + delta < 0:
                return False
            user.diamonds = (user.diamonds or 0) + delta
            await session.commit()
            return True

    @staticmethod
    async def get_user_inventory(user_id: int) -> dict:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return {"armor": 0, "intercept": 0, "detector": 0, "reveal": 0, "remap": 0}
            return {
                "armor": user.buff_armor or 0,
                "intercept": user.buff_intercept or 0,
                "detector": user.buff_detector or 0,
                "reveal": user.buff_reveal or 0,
                "remap": user.buff_remap or 0,
            }

    @staticmethod
    async def update_user_buff(user_id: int, buff_type: str, delta: int) -> bool:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            col_name = f"buff_{buff_type}"
            if not hasattr(user, col_name):
                return False
            val = getattr(user, col_name) or 0
            if val + delta < 0:
                return False
            setattr(user, col_name, val + delta)
            await session.commit()
            return True


    @staticmethod
    async def get_user_by_username(username: str) -> User:
        async with async_session() as session:
            clean_username = username.lstrip("@")
            res = await session.execute(select(User).where(User.username == clean_username))
            return res.scalar_one_or_none()

    @staticmethod
    async def ensure_user(user_id: int, full_name: str = "User", username: str = None) -> User:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                user = User(id=user_id, full_name=full_name, username=username)
                session.add(user)
                await session.commit()
                return user
            return user

    @staticmethod
    async def add_custom_dictionary(chat_id: int, name: str, words: list):
        async with async_session() as session:
            from src.core.database.models import CustomDictionary
            # Check if exists for this chat with same name
            res = await session.execute(
                select(CustomDictionary).where(CustomDictionary.chat_id == chat_id, CustomDictionary.name == name)
            )
            item = res.scalar_one_or_none()
            if not item:
                item = CustomDictionary(chat_id=chat_id, name=name, words=words)
                session.add(item)
            else:
                item.words = words
            await session.commit()

    @staticmethod
    async def get_custom_dictionaries(chat_id: int):
        async with async_session() as session:
            from src.core.database.models import CustomDictionary
            res = await session.execute(select(CustomDictionary).where(CustomDictionary.chat_id == chat_id))
            return res.scalars().all()

db_service = DbService()
