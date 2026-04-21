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
        protected_namespaces=()
    )
    
    bot_token: str
    admin_id: int = 0

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
    
    # Getting bot info
    bot_info = await bot.get_me()
    bot.username = bot_info.username

    # Register commands
    from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats, BotCommandScopeChat
    
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
    
    # Default Menu
    await bot.set_my_commands([
        BotCommand(command="codenames", description="Запустити нову гру"),
        BotCommand(command="feedback", description="Надіслати відгук"),
    ], scope=BotCommandScopeDefault())
    
    # Groups Menu
    await bot.set_my_commands([
        BotCommand(command="codenames", description="Запустити нову гру"),
        BotCommand(command="feedback", description="Надіслати відгук"),
    ], scope=BotCommandScopeAllGroupChats())
    
    # Private Menu
    await bot.set_my_commands([
        BotCommand(command="codenames", description="Запустити нову гру"),
        BotCommand(command="stats", description="Переглянути статистику"),
        BotCommand(command="settings", description="Налаштування бота"),
        BotCommand(command="feedback", description="Надіслати відгук"),
    ], scope=BotCommandScopeAllPrivateChats())

    # Admin Menu (Direct chat with admin)
    if settings.admin_id:
        try:
            await bot.set_my_commands([
                BotCommand(command="codenames", description="Запустити нову гру"),
                BotCommand(command="stats", description="Переглянути статистику"),
                BotCommand(command="settings", description="Налаштування бота"),
                BotCommand(command="feedback", description="Надіслати відгук/помилку"),
                BotCommand(command="test_render", description="Тест рендерингу (Admin)"),
                BotCommand(command="test_render_en", description="Тест рендерингу EN (Admin)"),
            ], scope=BotCommandScopeChat(chat_id=settings.admin_id))
        except Exception as e:
            logging.error(f"Failed to set admin commands: {e}")
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Import handlers
    from src.bot.handlers import common, game_router, settings as settings_router, admin
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(settings_router.router)
    dp.include_router(game_router.router)

    dp["settings"] = settings

    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
