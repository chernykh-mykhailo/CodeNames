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

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
