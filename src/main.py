import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# GLOBAL FIX: Silence pydantic warnings about 'model_' protected namespace
# This affects all models initialized after this line
ConfigDict.protected_namespaces = ()

class Settings(BaseSettings):
    bot_token: str
    
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=()
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    
    # Initialize Database
    from src.core.database.session import init_db
    await init_db()
    
    bot = Bot(
        token=settings.bot_token, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Getting bot info for deep linking
    bot_info = await bot.get_me()
    bot.username = bot_info.username
    
    dp = Dispatcher(storage=MemoryStorage())

    # Import handlers
    from src.bot.handlers import common, game_router
    dp.include_router(common.router)
    dp.include_router(game_router.router)

    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
