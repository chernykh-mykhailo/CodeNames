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
    status_pin = "✅" if getattr(game, "pin_message", True) else "❌"
    status_sheet = "✅" if game.metadata.get("spymaster_sheet", False) else "❌"
    status_past_clues = "✅" if game.metadata.get("show_past_clues", True) else "❌"
    status_strict = "✅" if game.metadata.get("strict_clues", False) else "❌"
    status_pass = "✅" if game.metadata.get("allow_pass", True) else "❌"
    status_auto_bot = "✅" if game.metadata.get("auto_bot_enabled", False) else "❌"

    kb_list = [
        [
            types.InlineKeyboardButton(
                text=t.SET_MODE.format(mode=game.metadata.get("mode", "Classic")),
                callback_data="setup_mode",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SET_LANG.format(lang=game.language.upper()),
                callback_data="setup_lang",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SETTING_DARK_MODE.format(status=status_dark),
                callback_data="setup_dark",
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
                text=t.SETTING_PIN_MESSAGE.format(status=status_pin),
                callback_data="setup_pin_msg",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SETTING_CAPTAIN_SHEET.format(status=status_sheet),
                callback_data="setup_toggle_sheet",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SETTING_PAST_CLUES.format(status=status_past_clues),
                callback_data="setup_toggle_past_clues",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SETTING_STRICT_CLUES.format(status=status_strict),
                callback_data="setup_toggle_strict",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SETTING_ALLOW_PASS.format(status=status_pass),
                callback_data="setup_toggle_pass",
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
                text=t.SET_TIMER_REG.format(time=game.reg_timer // 60),
                callback_data="setup_timer_reg",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SET_TIMER_TURN.format(time=game.turn_timer // 60),
                callback_data="setup_timer_turn",
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
    
    kb_list.append([types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="setup_back", style="primary")])

    kb = types.InlineKeyboardMarkup(inline_keyboard=kb_list)
    await callback.message.edit_text(t.SETTINGS_TITLE, reply_markup=kb)


async def _admin_check(callback: types.CallbackQuery, bot: Bot, settings) -> bool:
    """Check if user is admin. Returns True if NOT admin (caller should return)."""
    if (
        callback.message.chat.type != "private"
        and callback.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            await callback.answer(
                get_text(manager.get_game(callback.message.chat.id).language if manager.get_game(callback.message.chat.id) else "uk").ADMIN_ONLY_ERROR,
                show_alert=True,
            )
            return True
    return False


@router.callback_query(lambda c: c.data == "setup_pin_msg")
async def setup_pin_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return

    game.pin_message = not getattr(game, "pin_message", True)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.pin_message = game.pin_message
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()

@router.callback_query(lambda c: c.data == "setup_auto_bot_difficulty")
async def change_game_auto_bot_difficulty(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    try:
        # Check if user is bot admin (not chat admin)
        if callback.from_user.id != settings.admin_id:
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


@router.callback_query(lambda c: c.data == "setup_toggle_sheet")
async def setup_sheet_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return

    game.metadata["spymaster_sheet"] = not game.metadata.get("spymaster_sheet", False)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.spymaster_sheet = game.metadata["spymaster_sheet"]
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_toggle_past_clues")
async def setup_past_clues_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return

    game.metadata["show_past_clues"] = not game.metadata.get("show_past_clues", True)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.show_past_clues = game.metadata["show_past_clues"]
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_toggle_strict")
async def setup_strict_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return

    game.metadata["strict_clues"] = not game.metadata.get("strict_clues", False)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.strict_clues = game.metadata["strict_clues"]
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_toggle_pass")
async def setup_pass_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return

    game.metadata["allow_pass"] = not game.metadata.get("allow_pass", True)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.allow_pass = game.metadata["allow_pass"]
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_dark")
async def setup_dark_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    if await _admin_check(callback, bot, settings):
        return

    game.dark_mode = not game.dark_mode
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.dark_mode = game.dark_mode
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


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

    await show_settings(callback)
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

    if game.board_size > 8:
        return await callback.answer(t.SETTING_BUTTON_BOARD.split(":")[0] + b(game.language, " ❌ Слів занадто багато!", " ❌ Too many words!"), show_alert=True)

    game.button_board = not game.button_board
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.button_board = game.button_board
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_timer_reg")
async def setup_timer_reg_menu(callback: types.CallbackQuery):
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
                    text=t.TIME_2M, callback_data="conf_tmreg_120"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.TIME_5M, callback_data="conf_tmreg_300"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.TIME_10M, callback_data="conf_tmreg_600"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.BACK_BTN, callback_data="game_settings"
                )
            ],
        ]
    )
    await callback.message.edit_text(t.SET_TMR_REG_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("conf_tmreg_"))
async def confirm_tmreg(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.reg_timer = int(callback.data.replace("conf_tmreg_", ""))
    await show_settings(callback)


@router.callback_query(lambda c: c.data == "setup_timer_turn")
async def setup_timer_turn_menu(callback: types.CallbackQuery):
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
                    text=t.TIME_1M, callback_data="conf_tmturn_60"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.TIME_2M, callback_data="conf_tmturn_120"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.TIME_3M, callback_data="conf_tmturn_180"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.BACK_BTN, callback_data="game_settings"
                )
            ],
        ]
    )
    await callback.message.edit_text(t.SET_TMR_TURN_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("conf_tmturn_"))
async def confirm_tmturn(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.turn_timer = int(callback.data.replace("conf_tmturn_", ""))
    await show_settings(callback)


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
                    text=t.MODE_HARDCORE_BTN,
                    callback_data="conf_mode_Hardcore"
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


@router.callback_query(lambda c: c.data == "setup_back")
async def settings_back(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    from src.bot.handlers.game_setup import update_registration_view
    await update_registration_view(bot, callback.message.chat.id, game)


@router.callback_query(lambda c: c.data == "setup_lang")
async def setup_lang_menu(callback: types.CallbackQuery):
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
                    text=t.LANG_UK_BTN, callback_data="conf_lang_uk"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.LANG_EN_BTN, callback_data="conf_lang_en"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.BACK_BTN, callback_data="game_settings"
                )
            ],
        ]
    )
    await callback.message.edit_text(t.SET_LANG_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("conf_lang_"))
async def confirm_lang(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.language = callback.data.replace("conf_lang_", "")
    await show_settings(callback)


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
                    text=f"✨ {d.name}", callback_data=f"conf_words_custom_{d.name}"
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


@router.callback_query(lambda c: c.data == "game_cancel")
async def cancel_registration(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return

    game = manager.get_game(callback.message.chat.id)
    if not game:
        return await callback.answer()

    t = get_text(game.language)

    if callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(t.ONLY_ADMIN_STOP, show_alert=True)

    manager.end_game(callback.message.chat.id)
    try:
        await bot.unpin_chat_message(
            callback.message.chat.id, callback.message.message_id
        )
    except Exception:
        pass

    await callback.message.edit_text(t.GAME_STOPPED)
    await callback.answer()


@router.message(Command("cnstop"))
async def cmd_stop(message: types.Message, bot: Bot, settings):
    game = manager.get_game(message.chat.id)
    if not game:
        return

    t = get_text(game.language)

    if message.chat.type != "private" and message.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ONLY_ADMIN_STOP)

    manager.end_game(message.chat.id)

    try:
        if game.board_msg_id:
            await bot.unpin_chat_message(message.chat.id, game.board_msg_id)
        elif game.metadata.get("registration_msg_id"):
            await bot.unpin_chat_message(
                message.chat.id, game.metadata["registration_msg_id"]
            )
    except Exception:
        pass

    await message.answer(t.GAME_STOPPED)


@router.callback_query(lambda c: c.data == "setup_toggle_auto_bot")
async def setup_auto_bot_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Check if user is bot admin (not chat admin)
    if callback.from_user.id != settings.admin_id:
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
    await callback.answer()
