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
    admin_id: str = "0"
    redis_url: str = ""

    @property
    def admin_ids(self) -> list[int]:
        if not self.admin_id:
            return []
        try:
            return [int(x.strip()) for x in str(self.admin_id).split(",") if x.strip()]
        except Exception:
            return []


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
                BotCommand(command="cn_profile", description="Мій профіль 👤"),
                BotCommand(command="top", description="Таблиця лідерів 🏆"),
                BotCommand(command="diamonds", description="Магазин алмазів 💎"),
                BotCommand(command="feedback", description="Надіслати відгук"),
            ],
            scope=BotCommandScopeDefault(),
        )

        # Groups Menu
        await bot.set_my_commands(
            [
                BotCommand(command="codenames", description="Запустити нову гру"),
                BotCommand(command="cn_join", description="Приєднатися до гри"),
                BotCommand(command="cn_profile", description="Мій профіль 👤"),
                BotCommand(command="top", description="Таблиця лідерів 🏆"),
                BotCommand(command="cn_stop", description="Зупинити гру"),
                BotCommand(command="cn_buffs", description="Магазин бафів ⚡"),
                BotCommand(command="cn_leave", description="Покинути гру"),
                BotCommand(
                    command="cn_next", description="Скликати на наступну гру 🎮"
                ),
                BotCommand(
                    command="cn_extend", description="Подовжити час ходу або реєстрації ⏳"
                ),
            ],
            scope=BotCommandScopeAllGroupChats(),
        )

        # Private Menu
        await bot.set_my_commands(
            [
                BotCommand(command="codenames", description="Запустити нову гру"),
                BotCommand(command="profile", description="Мій профіль 👤"),
                BotCommand(command="settings", description="Налаштування бота"),
                BotCommand(command="my_dicts", description="Мої словники 📚"),
                BotCommand(command="view_dict", description="Переглянути словник 📖"),
                BotCommand(command="add_dict", description="Додати словник 📝"),
                BotCommand(command="add_words", description="Додати слова ➕"),
                BotCommand(command="del_words", description="Вилучити слова ➖"),
                BotCommand(command="feedback", description="Надіслати відгук"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )

        # Admin Menu
        for a_id in settings.admin_ids:
            try:
                await bot.set_my_commands(
                    [
                        BotCommand(
                            command="codenames", description="Запустити нову гру"
                        ),
                        BotCommand(command="cn_join", description="Приєднатися до гри"),
                        BotCommand(
                            command="stats", description="Переглянути статистику"
                        ),
                        BotCommand(command="settings", description="Налаштування бота"),
                        BotCommand(
                            command="feedback", description="Надіслати відгук/помилку"
                        ),
                        BotCommand(command="admin", description="Адмін-панель (Admin)"),
                        BotCommand(
                            command="gb1",
                            description="Адмін: Дати Щит [зелені/червоні]",
                        ),
                        BotCommand(
                            command="gb2",
                            description="Адмін: Дати Перехоплення [зелені/червоні]",
                        ),
                        BotCommand(
                            command="gb3", description="Адмін: Активувати Детектор"
                        ),
                        BotCommand(
                            command="gb4", description="Адмін: Відкрити 1 Агента"
                        ),
                        BotCommand(
                            command="gb5",
                            description="Адмін: Змінити всі слова (Remap)",
                        ),
                        BotCommand(
                            command="test_render", description="Тест рендерингу (Admin)"
                        ),
                        BotCommand(
                            command="test_render_en",
                            description="Тест рендерингу EN (Admin)",
                        ),
                    ],
                    scope=BotCommandScopeChat(chat_id=a_id),
                )
            except Exception as e:
                logging.error(f"Failed to set admin commands for {a_id}: {e}")
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

    # Register game classes for Redis persistence
    from src.core.platform.game_manager import manager, register_game_class
    from src.games.codenames.game import CodeNamesGame

    register_game_class("codenames", CodeNamesGame)

    # Initialize Redis for game session persistence
    if settings.redis_url:
        manager.init_redis(settings.redis_url)

    dp = Dispatcher(storage=storage)

    # (Auto-save removed — game state is now persisted explicitly in handlers that mutate it.)

    # Import handlers
    from src.bot.handlers import (
        game_router,
        common,
        admin,
        settings as settings_router,
        shop,
        dictionaries,
        leaderboard,
        profile,
        feedback,
        game_setup,
        buff_shop,
    )

    dp.include_router(shop.router)
    dp.include_router(game_router.router)
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(settings_router.router)
    dp.include_router(dictionaries.router)
    dp.include_router(leaderboard.router)
    dp.include_router(profile.router)
    dp.include_router(feedback.router)
    dp.include_router(game_setup.router)
    dp.include_router(buff_shop.router)
    dp["settings"] = settings

    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Start background turn timer polling task
    async def check_turn_timers():
        while True:
            try:
                import time
                from src.games.codenames.engine import Team
                from src.bot.handlers.game_router import update_main_board, trigger_game_over
                from src.assets.texts import get_text, b

                # Copy sessions to avoid runtime dictionary change errors
                sessions = list(manager.sessions.values())
                for game in sessions:
                    if game.status != "in_progress" or not game.engine or game.engine.is_over:
                        continue
                    
                    if not game.engine.turn_start_time:
                        continue

                    elapsed = time.time() - game.engine.turn_start_time
                    limit = game.engine.turn_time_limit # 180 seconds default

                    # 1. 30 seconds warning check
                    if limit - elapsed <= 30 and not game.engine.turn_warning_triggered:
                        game.engine.turn_warning_triggered = True
                        manager.save_game(game.chat_id)
                        
                        t = get_text(game.language)
                        # Broadcast 30 seconds warning with Extend Turn button
                        await update_main_board(None, game, bot) # This will re-render keyboard with Extend Turn button
                        
                        await bot.send_message(
                            game.chat_id,
                            t.TURN_30_SEC_WARNING,
                            message_thread_id=game.thread_id,
                            parse_mode="HTML"
                        )
                        
                    # 2. Timeout check
                    if elapsed >= limit:
                        t = get_text(game.language)
                        
                        # Auto-pass (force end turn)
                        turn_before = game.engine.current_turn
                        game.engine.end_turn()
                        if game.engine.mode == "duet":
                            game.update_duet_spymaster_queue(previous_turn=turn_before)
                        
                        manager.save_game(game.chat_id)
                        
                        # Send timeout announcement
                        await bot.send_message(
                            game.chat_id,
                            t.TIME_UP,
                            message_thread_id=game.thread_id,
                            parse_mode="HTML"
                        )
                        
                        # Update main board after turn change
                        await update_main_board(None, game, bot)

                # Copy sessions to check registration timers
                for game in sessions:
                    if game.status == "registration":
                        if not getattr(game, "reg_start_time", None):
                            continue
                        
                        reg_elapsed = time.time() - game.reg_start_time
                        reg_limit = game.reg_timer # in seconds

                        # 1. 30 seconds warning to registration end
                        if reg_limit - reg_elapsed <= 30 and not getattr(game, "reg_warning_triggered", False):
                            game.reg_warning_triggered = True
                            manager.save_game(game.chat_id)
                            
                            t = get_text(game.language)
                            await bot.send_message(
                                game.chat_id,
                                b(game.language, "⏳ До закінчення реєстрації залишилось 30 секунд!", "⏳ Only 30 seconds left for registration!"),
                                message_thread_id=game.thread_id,
                                parse_mode="HTML"
                            )
                        
                        # 2. Registration Timeout (start game or cancel)
                        if reg_elapsed >= reg_limit:
                            t = get_text(game.language)
                            
                            # Check if enough players to start automatically
                            # Minimum players: 2 (or 1 if auto_bot is enabled)
                            auto_bot_enabled = game.metadata.get("auto_bot_enabled", False)
                            can_start = len(game.players) >= 2 or (len(game.players) >= 1 and auto_bot_enabled)

                            if can_start:
                                # Start the game automatically!
                                from src.bot.handlers.game_router import start_game
                                # Create dummy CallbackQuery to invoke start_game
                                class DummyMessage:
                                    def __init__(self, chat):
                                        self.chat = chat
                                class DummyCallbackQuery:
                                    def __init__(self, message, from_user):
                                        self.message = message
                                        self.from_user = from_user
                                        self.data = "game_start"
                                    async def answer(self, text=None, show_alert=False):
                                        pass
                                
                                # Use creator of lobby or first player to simulate callback trigger
                                creator_id = game.metadata.get("creator_id")
                                if creator_id and creator_id in game.players:
                                    trigger_user = type('User', (object,), {'id': creator_id, 'full_name': game.players[creator_id].full_name})
                                else:
                                    first_player_id = list(game.players.keys())[0]
                                    trigger_user = type('User', (object,), {'id': first_player_id, 'full_name': game.players[first_player_id].full_name})

                                dummy_chat = type('Chat', (object,), {'id': game.chat_id})
                                dummy_msg = DummyMessage(dummy_chat)
                                dummy_cb = DummyCallbackQuery(dummy_msg, trigger_user)
                                
                                class DummySettings:
                                    def __init__(self):
                                        self.admin_ids = []
                                
                                await start_game(dummy_cb, bot, DummySettings())
                            else:
                                # Cancel game (not enough players)
                                await bot.send_message(
                                    game.chat_id,
                                    t.REG_TIMEOUT,
                                    message_thread_id=game.thread_id
                                )
                                try:
                                    reg_msg_id = game.metadata.get("registration_msg_id")
                                    if reg_msg_id:
                                        await bot.unpin_chat_message(chat_id=game.chat_id, message_id=reg_msg_id)
                                except Exception:
                                    pass
                                manager.end_game(game.chat_id)

            except Exception as e:
                logging.error(f"Error checking turn/reg timers: {e}")
            await asyncio.sleep(5)

    asyncio.create_task(check_turn_timers())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
