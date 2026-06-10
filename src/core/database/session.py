from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.database.models import Base
from pydantic_settings import BaseSettings, SettingsConfigDict

class DbSettings(BaseSettings):
    database_url: str
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
        protected_namespaces=()
    )

settings = DbSettings()
engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

from sqlalchemy import text

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Run startup migrations for existing databases
        columns_to_add = [
            ("diamonds", "BIGINT DEFAULT 500"),
            ("coins", "BIGINT DEFAULT 0"),
            ("buff_armor", "INTEGER DEFAULT 0"),
            ("buff_intercept", "INTEGER DEFAULT 0"),
            ("buff_detector", "INTEGER DEFAULT 0"),
            ("buff_reveal", "INTEGER DEFAULT 0"),
            ("buff_remap", "INTEGER DEFAULT 0"),
            ("buff_avoid_captain", "INTEGER DEFAULT 0"),
            ("buff_become_captain", "INTEGER DEFAULT 0"),
            ("buff_avoid_captain_ready", "INTEGER DEFAULT 0"),
            ("buff_become_captain_ready", "INTEGER DEFAULT 0"),
            ("guessed_words", "INTEGER DEFAULT 0"),
            ("assassins_hit", "INTEGER DEFAULT 0"),
            ("opponent_words_hit", "INTEGER DEFAULT 0")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass

        try:
            await conn.execute(text("ALTER TABLE custom_dictionaries ADD COLUMN creator_id BIGINT"))
        except Exception:
            pass

        # Migrate game_stats table
        gs_columns = [
            ("chat_id", "BIGINT"),
            ("mode", "VARCHAR"),
        ]
        for col_name, col_type in gs_columns:
            try:
                await conn.execute(text(f"ALTER TABLE game_stats ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass
