from sqlalchemy import select, func, case
from src.core.database.session import async_session
from src.core.database.models import User, GameStat, Chat
from src.core.database.schemas import ChatSettings
from datetime import datetime


def _hardcore_suffixes(hardcore_mode: str) -> list[str]:
    if hardcore_mode == "hard":
        return ["_hardcore"]
    if hardcore_mode == "light":
        return ["_light_hardcore"]
    if hardcore_mode == "roulette":
        return ["_roulette_hardcore"]
    return []

class DbService:
    @staticmethod
    async def save_game_result(
        user_id: int, 
        full_name: str, 
        username: str, 
        game_type: str, 
        result: str,
        guessed_words: int = 0,
        assassins_hit: int = 0,
        opponent_words_hit: int = 0,
        mode: str = None,
        chat_id: int = None
    ):
        async with async_session() as session:
            # 1. Ensure user exists
            user = await session.get(User, user_id)
            if not user:
                user = User(
                    id=user_id, 
                    full_name=full_name, 
                    username=username,
                    guessed_words=guessed_words,
                    assassins_hit=assassins_hit,
                    opponent_words_hit=opponent_words_hit
                )
                session.add(user)
            else:
                user.full_name = full_name
                user.username = username
                user.guessed_words = (user.guessed_words or 0) + guessed_words
                user.assassins_hit = (user.assassins_hit or 0) + assassins_hit
                user.opponent_words_hit = (user.opponent_words_hit or 0) + opponent_words_hit
            
            # 2. Add game stat
            stat = GameStat(
                user_id=user_id,
                chat_id=chat_id,
                game_type=game_type,
                mode=mode,
                result=result,
                played_at=datetime.utcnow()
            )
            session.add(stat)
            
            # 3. Reward with diamonds for win
            if result == "win":
                user.diamonds = (user.diamonds or 0) + 100
                
            await session.commit()

    @staticmethod
    async def ensure_chat(chat_id: int, title: str = None):
        async with async_session() as session:
            chat = await session.get(Chat, chat_id)
            if not chat:
                chat = Chat(id=chat_id, title=title or f"Chat {chat_id}")
                session.add(chat)
            elif title and chat.title != title:
                chat.title = title
            await session.commit()

    @staticmethod
    async def get_user_combat_stats(user_id: int) -> dict:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return {"guessed_words": 0, "assassins_hit": 0, "opponent_words_hit": 0}
            return {
                "guessed_words": user.guessed_words or 0,
                "assassins_hit": user.assassins_hit or 0,
                "opponent_words_hit": user.opponent_words_hit or 0,
            }

    @staticmethod
    async def get_user_stats(user_id: int, mode: str = None, hardcore_mode: str = "off"):
        async with async_session() as session:
            q = select(
                func.count(GameStat.id).label("total"),
                func.sum(case((GameStat.result == "win", 1), else_=0)).label("wins"),
                func.sum(case((GameStat.result == "loss", 1), else_=0)).label("losses")
            ).where(GameStat.user_id == user_id, GameStat.game_type == "codenames")
            
            hc_suffixes = _hardcore_suffixes(hardcore_mode)
            if mode:
                if hardcore_mode != "off":
                    q = q.where(GameStat.mode.in_([f"{mode}{s}" for s in hc_suffixes]))
                else:
                    q = q.where(GameStat.mode == mode)
            else:
                if hardcore_mode != "off":
                    patterns = [s.lstrip("_") for s in hc_suffixes]
                    q = q.where(GameStat.mode.in_(
                        ["hardcore", "classic_hardcore", "duet_hardcore", "3p_hardcore",
                         "classic_light_hardcore", "duet_light_hardcore", "3p_light_hardcore"]
                        if hardcore_mode == "all" else
                        [f"classic{s}" for s in hc_suffixes] +
                        [f"duet{s}" for s in hc_suffixes] +
                        [f"3p{s}" for s in hc_suffixes] +
                        (["hardcore"] if hardcore_mode == "hard" else [])
                    ))
                else:
                    q = q.where(
                        (GameStat.mode.is_(None)) |
                        (~GameStat.mode.like("%hardcore"))
                    )
            res = await session.execute(q)
            return res.first()

    @staticmethod
    async def get_top_players(limit: int = 10, mode: str = None, chat_id: int = None, hardcore_mode: str = "off"):
        """Get top players by wins. Optionally filter by mode, chat, and hardcore."""
        async with async_session() as session:
            q = select(
                GameStat.user_id,
                User.full_name,
                User.username,
                func.count(GameStat.id).label("total"),
                func.sum(case((GameStat.result == "win", 1), else_=0)).label("wins"),
                func.sum(case((GameStat.result == "loss", 1), else_=0)).label("losses"),
            ).join(User, User.id == GameStat.user_id).where(
                GameStat.game_type == "codenames"
            )
            
            hc_suffixes = _hardcore_suffixes(hardcore_mode)
            if mode:
                if hardcore_mode != "off":
                    q = q.where(GameStat.mode.in_([f"{mode}{s}" for s in hc_suffixes]))
                else:
                    q = q.where(GameStat.mode == mode)
            else:
                if hardcore_mode != "off":
                    q = q.where(GameStat.mode.in_(
                        [f"classic{s}" for s in hc_suffixes] +
                        [f"duet{s}" for s in hc_suffixes] +
                        [f"3p{s}" for s in hc_suffixes] +
                        (["hardcore"] if hardcore_mode == "hard" else [])
                    ))
                else:
                    q = q.where(
                        (GameStat.mode.is_(None)) |
                        (~GameStat.mode.like("%hardcore"))
                    )
            
            if chat_id:
                q = q.where(GameStat.chat_id == chat_id)
            q = q.group_by(GameStat.user_id, User.full_name, User.username)
            q = q.order_by(func.sum(case((GameStat.result == "win", 1), else_=0)).desc())
            q = q.limit(limit)
            res = await session.execute(q)
            return res.all()

    @staticmethod
    async def get_top_players_by_words(limit: int = 10):
        """Get top players by guessed words."""
        async with async_session() as session:
            q = select(
                User.id,
                User.full_name,
                User.username,
                User.guessed_words,
            ).where(User.guessed_words > 0).order_by(
                User.guessed_words.desc()
            ).limit(limit)
            res = await session.execute(q)
            return res.all()

    @staticmethod
    async def get_top_chats(limit: int = 10):
        """Get top chats by number of games played."""
        async with async_session() as session:
            q = select(
                GameStat.chat_id,
                Chat.title,
                func.count(func.distinct(GameStat.id)).label("total_records"),
            ).join(Chat, Chat.id == GameStat.chat_id).where(
                GameStat.chat_id.isnot(None),
                GameStat.game_type == "codenames"
            ).group_by(
                GameStat.chat_id, Chat.title
            ).order_by(
                func.count(func.distinct(GameStat.id)).desc()
            ).limit(limit)
            res = await session.execute(q)
            return res.all()

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
    async def get_user_coins(user_id: int) -> int:
        async with async_session() as session:
            user = await session.get(User, user_id)
            return user.coins if (user and user.coins is not None) else 0

    @staticmethod
    async def update_user_coins(user_id: int, delta: int) -> bool:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            current_coins = user.coins if user.coins is not None else 0
            if current_coins + delta < 0:
                return False
            user.coins = current_coins + delta
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
                "avoid_captain": user.buff_avoid_captain or 0,
                "become_captain": user.buff_become_captain or 0,
                "avoid_captain_ready": user.buff_avoid_captain_ready or 0,
                "become_captain_ready": user.buff_become_captain_ready or 0,
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
    async def get_user_captain_buff_flags(user_id: int) -> dict:
        """Get which captain buffs are toggled ON (ready)."""
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return {"avoid_captain_ready": False, "become_captain_ready": False}
            return {
                "avoid_captain_ready": bool(user.buff_avoid_captain_ready),
                "become_captain_ready": bool(user.buff_become_captain_ready),
            }

    @staticmethod
    async def toggle_captain_buff_ready(user_id: int, buff_type: str, turn_on: bool) -> bool:
        """Toggle the ready flag for avoid_captain or become_captain buff.
        Returns True if successful, False if insufficient inventory.
        buff_type should be 'avoid_captain' or 'become_captain'.
        """
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return False

            count_col = f"buff_{buff_type}"
            ready_col = f"buff_{buff_type}_ready"

            has_count = getattr(user, count_col) or 0
            is_ready = getattr(user, ready_col) or 0

            if turn_on and not is_ready:
                # Activate: need at least 1 item in inventory
                if has_count < 1:
                    return False
                # Mark as ready (doesn't consume yet)
                setattr(user, ready_col, 1)
            elif not turn_on and is_ready:
                # Deactivate
                setattr(user, ready_col, 0)
            else:
                return True  # Already in desired state

            await session.commit()
            return True

    @staticmethod
    async def consume_captain_buff(user_id: int, buff_type: str) -> bool:
        """Consume 1 item of the captain buff after it was triggered.
        Also resets the ready flag.
        """
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return False

            count_col = f"buff_{buff_type}"
            ready_col = f"buff_{buff_type}_ready"

            has_count = getattr(user, count_col) or 0
            if has_count < 1:
                return False

            setattr(user, count_col, has_count - 1)
            setattr(user, ready_col, 0)
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
