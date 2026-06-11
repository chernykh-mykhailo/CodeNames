from typing import Any
import asyncio
from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame
from src.core.database.service import db_service
from src.assets.texts import get_text, b
import logging

logger = logging.getLogger(__name__)

router = Router()


async def update_registration_view(bot: Bot, chat_id: int, game: Any):
    t = get_text(game.language)
    msg_id = game.metadata.get("registration_msg_id")
    if not msg_id:
        return

    mentions = []
    for p in game.players.values():
        link = f'<a href="tg://user?id={p.user_id}">{p.full_name}</a>'
        mentions.append(f"- {link}")

    text = (
        f"{t.REGISTRATION_TITLE.format(count=len(game.players))}\n\n"
        f"{t.PLAYERS_LIST}\n" + "\n".join(mentions)
    )

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t.JOIN_BTN,
                    url=f"https://t.me/{bot.username}?start=join_{chat_id}",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.START_BTN, callback_data="game_start", style="success"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.CANCEL_BTN, callback_data="game_cancel", style="danger"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.SETTINGS_BTN, callback_data="game_settings"
                )
            ],
        ]
    )

    try:
        await bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id, text=text, reply_markup=kb
        )
    except Exception:
        pass


@router.callback_query(lambda c: c.data == "game_settings")
async def show_settings(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    t = get_text(game.language)
    status_dark = "✅" if game.dark_mode else "❌"
    status_buttons = "✅" if game.button_board else "❌"
    status_auto_bot = "✅" if game.metadata.get("auto_bot_enabled", False) else "❌"
    status_hardcore = {"off": "❌", "light": "💀", "roulette": "🎰", "hard": "✅"}.get(game.metadata.get("hardcore_mode", "off"), "❌")
    hardcore_label = {
        "off": b(game.language, "💀 Hardcore: ❌", "💀 Hardcore: ❌"),
        "light": b(game.language, "⏱ Тік-Так: ⏱", "⏱ Tick-Tock: ⏱"),
        "roulette": b(game.language, "🎰 Рулетка: 🎰", "🎰 Roulette: 🎰"),
        "hard": b(game.language, "☠️ Хардкор: ✅", "☠️ Hardcore: ✅"),
    }.get(game.metadata.get("hardcore_mode", "off"), "💀 Hardcore: ❌")

    kb_list = [
        [
            types.InlineKeyboardButton(
                text=t.SET_MODE.format(mode=game.metadata.get("mode", "Classic")),
                callback_data="setup_mode",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=hardcore_label,
                callback_data="setup_hardcore_menu",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SET_BOARD_SIZE.format(size=game.board_size),
                callback_data="setup_board_size",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SETTING_BUTTON_BOARD.format(status=status_buttons),
                callback_data="setup_buttons",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SET_WORDS.format(words=game.word_set),
                callback_data="setup_words",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SETTING_AUTO_BOT.format(status=status_auto_bot),
                callback_data="setup_toggle_auto_bot",
            )
        ]
    ]
    
    # Add difficulty button if auto-bot is enabled
    if game.metadata.get("auto_bot_enabled", False):
        difficulty_display = {
            "easy": "🟢 Easy",
            "medium": "🟡 Medium", 
            "hard": "🔴 Hard"
        }.get(game.metadata.get("auto_bot_difficulty", "medium"), "🟡 Medium")
        kb_list.append([
            types.InlineKeyboardButton(
                text=t.SETTING_AUTO_BOT_DIFFICULTY.format(level=difficulty_display),
                callback_data="setup_auto_bot_difficulty",
            )
        ])
        # Quick link to chat-level settings for settings that are shared
        # (hardcore, pin, etc.) so they don't get out of sync.
    kb_list.append([types.InlineKeyboardButton(
                text=t.CHAT_SETTINGS_BTN,
                callback_data="setup_open_chat_settings",
            )])
    
    kb_list.append([types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="setup_back", style="primary")])

    kb = types.InlineKeyboardMarkup(inline_keyboard=kb_list)
    await callback.message.edit_text(t.SETTINGS_TITLE, reply_markup=kb)


async def _admin_check(callback: types.CallbackQuery, bot: Bot, settings) -> bool:
    """Check if user is allowed to change settings.
    
    Lobby creator always has access.
    If admin_only_settings is ON, only chat admins/bot-admin/creator can change.
    If admin_only_settings is OFF, anyone can change.
    Returns True if NOT allowed (caller should return).
    """
    if callback.message.chat.type == "private":
        return False
    
    user_id = callback.from_user.id
    
    # Bot admin always allowed
    # Bot admin always allowed
    if user_id in settings.admin_ids:
        return False
    
    game = manager.get_game(callback.message.chat.id)
    lang = game.language if game else "uk"
    
    # Lobby creator always allowed
    if game and user_id == game.metadata.get("creator_id"):
        return False
    
    # If admin_only_settings is OFF, anyone can change
    if game and not game.metadata.get("admin_only_settings", False):
        return False
    
    # Otherwise check if chat admin
    member = await bot.get_chat_member(callback.message.chat.id, user_id)
    if member.status in ["administrator", "creator"]:
        return False
    
    await callback.answer(
        get_text(lang).ONLY_CREATOR_OR_ADMIN,
        show_alert=True,
    )
    return True


@router.callback_query(lambda c: c.data == "setup_auto_bot_difficulty")
async def change_game_auto_bot_difficulty(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    try:
        # Check if user is bot admin (not chat admin)
        if callback.from_user.id not in settings.admin_ids:
            t = get_text(game.language)
            await callback.answer(
                t.ADMIN_ONLY_ERROR,
                show_alert=True,
            )
            return

        chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
        t = get_text(game.language)

        # Cycle through difficulties
        difficulties = ["easy", "medium", "hard"]
        current_index = difficulties.index(chat_settings.auto_bot_difficulty) if chat_settings.auto_bot_difficulty in difficulties else 1
        next_difficulty = difficulties[(current_index + 1) % len(difficulties)]

        chat_settings.auto_bot_difficulty = next_difficulty
        await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

        game.metadata["auto_bot_difficulty"] = chat_settings.auto_bot_difficulty

        await show_settings(callback)

        difficulty_names = {
            "easy": t.DIFFICULTY_EASY if hasattr(t, "DIFFICULTY_EASY") else "Easy",
            "medium": t.DIFFICULTY_MEDIUM if hasattr(t, "DIFFICULTY_MEDIUM") else "Medium",
            "hard": t.DIFFICULTY_HARD if hasattr(t, "DIFFICULTY_HARD") else "Hard"
        }
        await callback.answer(t.AUTO_BOT_DIFFICULTY_CHANGED.format(level=difficulty_names[next_difficulty]))
    except Exception as e:
        logger.error(f"Error in change_game_auto_bot_difficulty: {e}")
        await callback.answer("❌ Помилка при зміні складності")


@router.callback_query(lambda c: c.data == "setup_board_size")
async def setup_board_size_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)

    buttons = []
    row1 = [
        types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}")
        for i in range(4, 8)
    ]
    buttons.append(row1)
    row2 = [
        types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}")
        for i in range(8, 12)
    ]
    buttons.append(row2)
    row3 = [
        types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}")
        for i in range(12, 14)
    ]
    buttons.append(row3)

    buttons.append(
        [
            types.InlineKeyboardButton(
                text=t.BACK_BTN, callback_data="setup_board_size_back"
            )
        ]
    )

    await callback.message.edit_text(
        t.SET_BOARD_SIZE_TITLE,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(lambda c: c.data.startswith("setup_size_"))
async def setup_board_size_confirm(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return

    size = int(callback.data.replace("setup_size_", ""))
    game.board_size = size

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.board_size = size

    if size > 8:
        game.button_board = False
        chat_settings.button_board = False

    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    t = get_text(game.language)

    await show_settings(callback)
    manager.save_game(callback.message.chat.id)
    await callback.answer(t.SETUP_SIZE_SET_MSG.format(size=size))


@router.callback_query(lambda c: c.data == "setup_board_size_back")
async def setup_board_size_back(callback: types.CallbackQuery):
    await show_settings(callback)


@router.callback_query(lambda c: c.data == "setup_buttons")
async def setup_buttons_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return

    t = get_text(game.language)
    if game.board_size > 8:
        return await callback.answer(t.SETTING_BUTTON_BOARD.split(":")[0] + b(game.language, " ❌ Слів занадто багато!", " ❌ Too many words!"), show_alert=True)

    game.button_board = not game.button_board
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.button_board = game.button_board
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    manager.save_game(callback.message.chat.id)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_mode")
async def setup_mode_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t.MODE_CLASSIC_BTN, callback_data="conf_mode_Classic"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.MODE_DUET_BTN, callback_data="conf_mode_Duet"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.BACK_BTN, callback_data="game_settings"
                )
            ],
        ]
    )
    await callback.message.edit_text(t.SET_MODE_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("conf_mode_"))
async def confirm_mode(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.metadata["mode"] = callback.data.replace("conf_mode_", "")
    await show_settings(callback)
    manager.save_game(callback.message.chat.id)


@router.callback_query(lambda c: c.data == "setup_back")
async def settings_back(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    from src.bot.handlers.game_setup import update_registration_view
    await update_registration_view(bot, callback.message.chat.id, game)


@router.callback_query(lambda c: c.data == "setup_words")
async def setup_words_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    from src.games.codenames.words import WordRepository

    repo = WordRepository()
    sets = repo.list_available_sets(game.language)

    custom_dicts = await db_service.get_custom_dictionaries(callback.message.chat.id)

    t = get_text(game.language)
    buttons = []
    for s in sets:
        buttons.append(
            [
                types.InlineKeyboardButton(
                    text=t.WORD_SET_FORMAT.format(name=s),
                    callback_data=f"conf_words_{s}",
                )
            ]
        )

    for d in custom_dicts:
        buttons.append(
            [
                types.InlineKeyboardButton(
                    text=f"✨ {d.name}", callback_data=f"conf_words_custom_{d.id}"
                )
            ]
        )

    await callback.message.edit_text(
        t.SET_WORDS_TITLE,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=buttons
            + [
                [
                    types.InlineKeyboardButton(
                        text=t.BACK_BTN, callback_data="game_settings"
                    )
                ]
            ]
        ),
    )


@router.callback_query(lambda c: c.data.startswith("conf_words_"))
async def confirm_word_set(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.word_set = callback.data.replace("conf_words_", "")
    await show_settings(callback)
    manager.save_game(callback.message.chat.id)


@router.callback_query(lambda c: c.data == "game_cancel")
async def cancel_registration(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return

    game = manager.get_game(callback.message.chat.id)
    if not game:
        return await callback.answer()

    t = get_text(game.language)
    user_id = callback.from_user.id

    # Allow: bot admin, lobby creator, player in the game, chat admin
    # Allow: bot admin, lobby creator, player in the game, chat admin
    if user_id not in settings.admin_ids and user_id != game.metadata.get("creator_id"):
        if user_id not in game.players:
            if callback.message.chat.type != "private":
                member = await bot.get_chat_member(
                    callback.message.chat.id, user_id
                )
                if member.status not in ["administrator", "creator"]:
                    return await callback.answer(t.ONLY_ADMIN_STOP, show_alert=True)

    # Try to unpin the registration/board message before ending the game
    chat_id = callback.message.chat.id
    try:
        await bot.unpin_chat_message(chat_id=chat_id, message_id=callback.message.message_id)
    except Exception:
        pass
    try:
        if game.metadata.get("registration_msg_id"):
            await bot.unpin_chat_message(chat_id=chat_id, message_id=game.metadata["registration_msg_id"])
    except Exception as e:
        logger.warning(f"Failed to unpin registration_msg_id: {e}")
    try:
        board_id = getattr(game, 'board_msg_id', None) or game.metadata.get('board_msg_id')
        if board_id:
            await bot.unpin_chat_message(chat_id=chat_id, message_id=board_id)
    except Exception as e:
        logger.warning(f"Failed to unpin board_msg_id: {e}")

    manager.end_game(chat_id)

    await callback.message.edit_text(t.GAME_STOPPED)
    await callback.answer()


@router.message(Command("cn_stop"))
async def cmd_stop(message: types.Message, bot: Bot, settings):
    game = manager.get_game(message.chat.id)
    if not game:
        return

    t = get_text(game.language)
    user_id = message.from_user.id

    # Allow: bot admin, lobby creator, player in the game, chat admin
    if message.chat.type != "private" and user_id not in settings.admin_ids:
        if user_id != game.metadata.get("creator_id") and user_id not in game.players:
            member = await bot.get_chat_member(message.chat.id, user_id)
            if member.status not in ["administrator", "creator"]:
                return await message.answer(t.ONLY_ADMIN_STOP)

    # Unpin message BEFORE ending the game
    try:
        board_id = getattr(game, 'board_msg_id', None) or game.metadata.get('board_msg_id')
        if board_id:
            await bot.unpin_chat_message(chat_id=message.chat.id, message_id=board_id)
    except Exception as e:
        logger.warning(f"Failed to unpin board message in cmd_stop: {e}")

    try:
        if game.metadata.get("registration_msg_id"):
            await bot.unpin_chat_message(
                chat_id=message.chat.id, message_id=game.metadata["registration_msg_id"]
            )
    except Exception as e:
        logger.warning(f"Failed to unpin registration message in cmd_stop: {e}")

    manager.end_game(message.chat.id)

    await message.answer(t.GAME_STOPPED)


@router.callback_query(lambda c: c.data == "setup_toggle_auto_bot")
async def setup_auto_bot_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Check if user is bot admin (not chat admin)
    if callback.from_user.id not in settings.admin_ids:
        t = get_text(game.language)
        await callback.answer(
            t.ADMIN_ONLY_ERROR,
            show_alert=True,
        )
        return

    game.metadata["auto_bot_enabled"] = not game.metadata.get("auto_bot_enabled", False)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.auto_bot_enabled = game.metadata["auto_bot_enabled"]
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    manager.save_game(callback.message.chat.id)
    await callback.answer()

@router.callback_query(lambda c: c.data == "setup_hardcore_menu")
async def setup_hardcore_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)
    current = game.metadata.get("hardcore_mode", "off")
    def btn(mode, label):
        mark = " ◀" if current == mode else ""
        return [types.InlineKeyboardButton(text=f"{label}{mark}", callback_data=f"setup_hc_{mode}")]
    descs = "\n".join([
        t.HARDCORE_OFF_DESC,
        t.HARDCORE_LIGHT_DESC,
        t.HARDCORE_ROULETTE_DESC,
        t.HARDCORE_HARD_DESC,
    ])
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        btn("off", t.HARDCORE_OFF_BTN),
        btn("light", t.HARDCORE_LIGHT_BTN),
        btn("roulette", t.HARDCORE_ROULETTE_BTN),
        btn("hard", t.HARDCORE_HARD_BTN),
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")],
    ])
    await callback.message.edit_text(f"{t.HARDCORE_MENU_TITLE}\n\n{descs}", reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("setup_hc_"))
async def setup_hc_select(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return
    mode = callback.data.replace("setup_hc_", "")
    game.metadata["hardcore_mode"] = mode
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.hardcore_mode = mode
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    await show_settings(callback)
    manager.save_game(callback.message.chat.id)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_open_chat_settings")
async def setup_open_chat_settings(callback: types.CallbackQuery):
    """Open the chat-level settings menu from inside the lobby.

    This provides a quick way to reach settings that are shared between
    chat and lobby (hardcore, pin, dark mode, etc.) so the user can
    verify/edit the same value from either place.
    """
    if not callback.message:
        return
    chat_id = callback.message.chat.id
    chat_settings = await db_service.get_chat_settings(chat_id)
    from src.bot.handlers.settings import show_chat_settings, game_lobby_chats
    game_lobby_chats.add(chat_id)
    await show_chat_settings(callback, chat_settings)
    await callback.answer()
