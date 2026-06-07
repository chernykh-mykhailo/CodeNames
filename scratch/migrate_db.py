"""Migration script: add buff columns for avoid/become captain."""
import asyncio
from sqlalchemy import text
from src.core.database.session import async_session

async def migrate():
    async with async_session() as session:
        # Add new buff columns
        for col in [
            "buff_avoid_captain INTEGER DEFAULT 0",
            "buff_become_captain INTEGER DEFAULT 0",
            "buff_avoid_captain_ready INTEGER DEFAULT 0",
            "buff_become_captain_ready INTEGER DEFAULT 0",
        ]:
            try:
                await session.execute(text(f"ALTER TABLE users ADD COLUMN {col}"))
            except Exception as e:
                print(f"Column might already exist: {e}")
        await session.commit()
        print("Migration completed!")

asyncio.run(migrate())