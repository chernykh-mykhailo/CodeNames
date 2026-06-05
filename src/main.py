import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", protected_namespaces=()
    )

    bot_token: str
    monobank_token: str = ""
    mono_jar_url: str = ""
    admin_id: int = 0
    redis_url: str = ""


async def main():
    logging.basicConfig(level=logging.INFO)
    settings = Settings()

    # Initialize Database
    from src.core.database.session import init_db

    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Getting bot info
    bot_info = await bot.get_me()
    bot.username = bot_info.username

    # Register commands
    from aiogram.types import (
        BotCommand,
        BotCommandScopeDefault,
        BotCommandScopeAllPrivateChats,
        BotCommandScopeAllGroupChats,
        BotCommandScopeChat,
    )

    try:
        await bot.delete_my_commands(scope=BotCommandScopeDefault())

        # Default Menu
        await bot.set_my_commands(
            [
                BotCommand(command="codenames", description="Запустити нову гру"),
                BotCommand(command="diamonds", description="Магазин алмазів 💎"),
                BotCommand(command="feedback", description="Надіслати відгук"),
            ],
            scope=BotCommandScopeDefault(),
        )

        # Groups Menu
        await bot.set_my_commands(
            [
                BotCommand(command="codenames", description="Запустити нову гру"),
                BotCommand(command="stop", description="Зупинити гру"),
                BotCommand(command="cnstop", description="Зупинити гру (аліас)"),
                BotCommand(command="feedback", description="Надіслати відгук"),
            ],
            scope=BotCommandScopeAllGroupChats(),
        )

        # Private Menu
        await bot.set_my_commands(
            [
                BotCommand(command="codenames", description="Запустити нову гру"),
                BotCommand(command="stats", description="Переглянути статистику"),
                BotCommand(command="settings", description="Налаштування бота"),
                BotCommand(command="my_dicts", description="Мої словники 📚"),
                BotCommand(command="add_dict", description="Додати словник 📝"),
                BotCommand(command="feedback", description="Надіслати відгук"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )

        # Admin Menu
        if settings.admin_id:
            try:
                await bot.set_my_commands(
                    [
                        BotCommand(
                            command="codenames", description="Запустити нову гру"
                        ),
                        BotCommand(
                            command="stats", description="Переглянути статистику"
                        ),
                        BotCommand(command="settings", description="Налаштування бота"),
                        BotCommand(
                            command="feedback", description="Надіслати відгук/помилку"
                        ),
                        BotCommand(
                            command="test_render", description="Тест рендерингу (Admin)"
                        ),
                        BotCommand(
                            command="test_render_en",
                            description="Тест рендерингу EN (Admin)",
                        ),
                    ],
                    scope=BotCommandScopeChat(chat_id=settings.admin_id),
                )
            except Exception as e:
                logging.error(f"Failed to set admin commands: {e}")
    except Exception as e:
        logging.warning(
            f"Failed to register/delete bot commands due to rate limits: {e}"
        )

    if settings.redis_url:
        from aiogram.fsm.storage.redis import RedisStorage

        storage = RedisStorage.from_url(settings.redis_url)
        logging.info("Using RedisStorage for FSM")
    else:
        storage = MemoryStorage()
        logging.info("Using MemoryStorage for FSM")

    dp = Dispatcher(storage=storage)

    # DEBUG Middleware: Log every message
    @dp.message.outer_middleware()
    async def debug_log_middleware(handler, event, data):
        logging.info(
            f"DEBUG Update [CHAT {event.chat.id}]: text='{event.text}' from={event.from_user.id}"
        )
        result = await handler(event, data)
        logging.info(f"DEBUG Result: {result}")
        return result

    # Import handlers
    from src.bot.handlers import (
        game_router,
        common,
        admin,
        settings as settings_router,
        shop,
        dictionaries,
    )

    dp.include_router(shop.router)
    dp.include_router(game_router.router)
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(settings_router.router)
    dp.include_router(dictionaries.router)
    dp["settings"] = settings

    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
