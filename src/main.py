import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=() # Disable protection to avoid conflicts with 'model_' etc
    )
    
    bot_token: str

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

    # Register commands
    from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
    
    # Reset all first (to clear cache)
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
    
    # Global commands (Default)
    await bot.set_my_commands([
        BotCommand(command="codenames", description="Запустити нову гру"),
    ], scope=BotCommandScopeDefault())
    
    # Groups specifically
    await bot.set_my_commands([
        BotCommand(command="codenames", description="Запустити нову гру"),
    ], scope=BotCommandScopeAllGroupChats())
    
    # Private commands
    await bot.set_my_commands([
        BotCommand(command="codenames", description="Запустити нову гру"),
        BotCommand(command="stats", description="Переглянути статистику"),
        BotCommand(command="settings", description="Налаштування бота"),
    ], scope=BotCommandScopeAllPrivateChats())
    
    dp = Dispatcher(storage=MemoryStorage())

    # Import handlers
    from src.bot.handlers import common, game_router, settings
    dp.include_router(common.router)
    dp.include_router(game_router.router)
    dp.include_router(settings.router)

    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
