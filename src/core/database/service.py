from sqlalchemy import select, func, case
from src.core.database.session import async_session
from src.core.database.models import User, GameStat
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

db_service = DbService()
