from typing import Any
import asyncio
from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame
from src.core.platform.base_game import GamePlayer
from src.core.database.service import db_service
from src.assets.texts import get_text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from src.core.utils.logging import send_log

logger = logging.getLogger(__name__)

class FeedbackState(StatesGroup):
    waiting_for_feedback = State()

router = Router()

async def process_join_game(message: types.Message, chat_id: int, bot: Bot):
    game = manager.get_game(chat_id)
    settings = await db_service.get_chat_settings(chat_id)
    t = get_text(settings.language)
    if not game:
        return await message.answer(t.GAME_NOT_FOUND)
        
    player = GamePlayer(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    
    if game.add_player(player):
        msg_id = game.metadata.get("registration_msg_id")
        chat_link = None
        
        internal_chat_id = str(chat_id)
        if internal_chat_id.startswith("-100"):
            clean_id = internal_chat_id.replace("-100", "")
            chat_link = f"https://t.me/c/{clean_id}/{msg_id}"
        
        kb = None
        if chat_link:
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=t.RETURN_BTN, url=chat_link)]
            ])

        msg = await message.answer(t.JOIN_SUCCESS, reply_markup=kb)
        if hasattr(player, 'join_msg_id'):
            player.join_msg_id = msg.message_id
            
        try:
            await message.delete()
        except:
            pass
        
        if game.status == "in_progress":
            team_emoji = "🔴" if player.team == "red" else "🔵"
            await bot.send_message(
                chat_id,
                f"➕ {team_emoji} {player.full_name} {t.JOINED_MID_GAME or 'приєднався до гри!'}",
                message_thread_id=game.thread_id
            )
        else:
            await update_registration_view(bot, chat_id, game)
    else:
        await message.answer(t.ALREADY_JOINED)

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, bot: Bot):
    if command.args and command.args.startswith("join_"):
        chat_id = int(command.args.replace("join_", ""))
        return await process_join_game(message, chat_id, bot)

    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)
    await message.answer(t.WELCOME)

@router.message(Command("cn_join"))
async def cmd_cn_join(message: types.Message, command: CommandObject, bot: Bot):
    if not command.args:
        return
    try:
        chat_id = int(command.args)
    except ValueError:
        return
        
    await process_join_game(message, chat_id, bot)
    try:
        await message.delete()
    except Exception:
        pass

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.chat.type != "private":
        return
        
    stats = await db_service.get_user_stats(message.from_user.id)
    
    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)
    if not stats or stats.total == 0:
        return await message.answer(t.NO_STATS)
    
    wins = stats.wins or 0
    losses = stats.losses or 0
    total = stats.total
    winrate = (wins / total * 100) if total > 0 else 0
    
    text = t.STATS_TEMPLATE.format(
        total=total,
        wins=wins,
        losses=losses,
        winrate=winrate
    )
    
    await message.answer(text)

@router.message(Command("feedback"))
async def cmd_feedback(message: types.Message, state: FSMContext):
    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.FINISH_FEEDBACK_BTN, callback_data="finish_feedback")]
    ])
    
    await message.answer(t.FEEDBACK_SESSION_STARTED, reply_markup=kb)
    await state.set_state(FeedbackState.waiting_for_feedback)

@router.callback_query(lambda c: c.data == "finish_feedback")
async def cb_finish_feedback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("✅ Режим фідбеку завершено. Дякуємо!")
    await callback.answer()

@router.message(Command("done"), FeedbackState.waiting_for_feedback)
async def cmd_done_feedback(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Режим фідбеку завершено. Дякуємо!")

@router.message(FeedbackState.waiting_for_feedback)
async def process_feedback_ticket(message: types.Message, state: FSMContext, bot: Bot):
    import time
    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)
    
    # Smart anti-spam check
    data = await state.get_data()
    last_msg_time = data.get("last_msg_time", 0)
    msg_count = data.get("msg_count", 0)
    
    now = time.time()
    if msg_count >= 10 and now - last_msg_time < 1.5:
        # Only apply cooldown after first 10 messages to allow media groups/forwards
        return await message.answer(t.FEEDBACK_TOO_FAST)
    
    if msg_count >= 50: # Increased total cap to 50
        return await message.answer(t.FEEDBACK_LIMIT_REACHED)

    # Check admin log configuration
    log_cfg = await db_service.get_system_setting("log_settings")
    dest = log_cfg.get("destination")
    if not dest or "feedback" not in log_cfg.get("enabled_types", []):
         return await message.answer("⚠️ Функція фідбеку тимчасово недоступна.")

    chat_id = dest.get("chat_id")
    thread_id = dest.get("thread_id")
    
    header = t.FEEDBACK_HEADER.format(
        name=message.from_user.full_name, 
        id=message.from_user.id
    )

    try:
        caption = header
        if message.caption:
            caption += f"\n\n{message.caption}"
            
        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=thread_id,
            caption=caption if message.caption or not message.text else None,
            parse_mode="HTML"
        )
        
        if message.text:
             await bot.send_message(
                 chat_id=chat_id,
                 text=f"{header}\n\n{message.text}",
                 message_thread_id=thread_id,
                 parse_mode="HTML"
             )

        # Update anti-spam data
        await state.update_data(last_msg_time=now, msg_count=msg_count + 1)

        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=t.FINISH_FEEDBACK_BTN, callback_data="finish_feedback")]
        ])
        await message.answer(t.FEEDBACK_SENT, reply_markup=kb)
    except Exception as e:
        await message.answer(f"❌ Помилка надсилання: {e}")

@router.message(Command("codenames"))
async def start_codenames(message: types.Message, bot: Bot):
    logger.info(f"TRACE: start_codenames triggered by {message.from_user.id} in chat {message.chat.id}")
    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)
    if message.chat.type == "private":
        logger.info("TRACE: start_codenames rejected (private chat)")
        return await message.answer(t.MIN_PLAYERS)
        
    # Permission check
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    if not chat_settings.allow_everyone_start:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ADMIN_ONLY_ERROR)

    existing_game = manager.get_game(message.chat.id)
    if existing_game:
        return await message.answer(t.GAME_ALREADY_STARTED or "Гра вже триває або лоббі вже створене!")

    game = manager.create_game(message.chat.id, CodeNamesGame, message.message_thread_id)
    game.language = settings.language
    game.word_set = settings.last_word_set
    game.reg_timer = settings.last_reg_timer
    game.turn_timer = settings.last_turn_timer
    game.metadata["mode"] = settings.last_mode
    game.dark_mode = settings.dark_mode
    game.button_board = settings.button_board
    game.board_size = settings.board_size
    # Deep link for joining
    join_url = f"https://t.me/{bot.username}?start=join_{message.chat.id}"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.JOIN_BTN, url=join_url)],
        [types.InlineKeyboardButton(text=t.START_BTN, callback_data="game_start", style="success")],
        [types.InlineKeyboardButton(text=t.CANCEL_BTN, callback_data="game_cancel", style="danger")],
        [types.InlineKeyboardButton(text=t.SETTINGS_BTN, callback_data="game_settings")]
    ])
    
    sent_msg = await message.answer(
        t.REGISTRATION_TITLE.format(count=0),
        reply_markup=kb
    )
    # Store message_id for later updates
    game.registration_msg_id = sent_msg.message_id
    game.metadata["registration_msg_id"] = sent_msg.message_id
    
    # Start registration timer task
    asyncio.create_task(game.start_reg_timer(bot))

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
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.JOIN_BTN, url=f"https://t.me/{bot.username}?start=join_{chat_id}")],
        [types.InlineKeyboardButton(text=t.START_BTN, callback_data="game_start", style="success")],
        [types.InlineKeyboardButton(text=t.CANCEL_BTN, callback_data="game_cancel", style="danger")],
        [types.InlineKeyboardButton(text=t.SETTINGS_BTN, callback_data="game_settings")]
    ])
    
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=text,
            reply_markup=kb
        )
    except Exception:
        pass # Message might not be modified or deleted

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
    
    kb_list = [
        [types.InlineKeyboardButton(text=t.SET_MODE.format(mode=game.metadata.get('mode', 'Classic')), callback_data="setup_mode")],
        [types.InlineKeyboardButton(text=t.SET_LANG.format(lang=game.language.upper()), callback_data="setup_lang")],
        [types.InlineKeyboardButton(text=t.SETTING_DARK_MODE.format(status=status_dark), callback_data="setup_dark")],
        [types.InlineKeyboardButton(text=t.SET_BOARD_SIZE.format(size=game.board_size), callback_data="setup_board_size")],
        [types.InlineKeyboardButton(text=t.SETTING_BUTTON_BOARD.format(status=status_buttons), callback_data="setup_buttons")],
        [types.InlineKeyboardButton(text=t.SET_WORDS.format(words=game.word_set), callback_data="setup_words")],
        [types.InlineKeyboardButton(text=t.SET_TIMER_REG.format(time=game.reg_timer//60), callback_data="setup_timer_reg")],
        [types.InlineKeyboardButton(text=t.SET_TIMER_TURN.format(time=game.turn_timer//60), callback_data="setup_timer_turn")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="setup_back")]
    ]
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=kb_list)
    await callback.message.edit_text(t.SETTINGS_TITLE, reply_markup=kb)

@router.callback_query(lambda c: c.data == "setup_dark")
async def setup_dark_toggle(callback: types.CallbackQuery, bot: Bot):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    
    # Permission check for groups
    if callback.message.chat.type != "private":
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True)
            
    # Update game and DB
    game.dark_mode = not game.dark_mode
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    settings.dark_mode = game.dark_mode
    await db_service.update_chat_settings(callback.message.chat.id, settings)
    
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
    row1 = [types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}") for i in range(4, 8)]
    buttons.append(row1)
    row2 = [types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}") for i in range(8, 12)]
    buttons.append(row2)
    row3 = [types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}") for i in range(12, 14)]
    buttons.append(row3)
    
    buttons.append([types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="setup_board_size_back")])
    
    await callback.message.edit_text(t.SET_BOARD_SIZE_TITLE, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data.startswith("setup_size_"))
async def setup_board_size_confirm(callback: types.CallbackQuery, bot: Bot):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
        
    # Permission check for groups
    if callback.message.chat.type != "private":
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True)
            
    size = int(callback.data.replace("setup_size_", ""))
    game.board_size = size
    
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    settings.board_size = size
    
    if size > 8:
        game.button_board = False
        settings.button_board = False
        
    await db_service.update_chat_settings(callback.message.chat.id, settings)
    
    await show_settings(callback)
    await callback.answer(f"Size set to {size}x{size}")

@router.callback_query(lambda c: c.data == "setup_board_size_back")
async def setup_board_size_back(callback: types.CallbackQuery):
    await show_settings(callback)

@router.callback_query(lambda c: c.data == "setup_buttons")
async def setup_buttons_toggle(callback: types.CallbackQuery, bot: Bot):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    
    # Permission check for groups
    if callback.message.chat.type != "private":
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True)
            
    if game.board_size > 8:
        return await callback.answer("❌ Слів занадто багато для кнопкового відображення!", show_alert=True)
        
    # Update game and DB
    game.button_board = not game.button_board
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    settings.button_board = game.button_board
    await db_service.update_chat_settings(callback.message.chat.id, settings)
    
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
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.TIME_2M, callback_data="conf_tmreg_120")],
        [types.InlineKeyboardButton(text=t.TIME_5M, callback_data="conf_tmreg_300")],
        [types.InlineKeyboardButton(text=t.TIME_10M, callback_data="conf_tmreg_600")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")]
    ])
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
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.TIME_1M, callback_data="conf_tmturn_60")],
        [types.InlineKeyboardButton(text=t.TIME_2M, callback_data="conf_tmturn_120")],
        [types.InlineKeyboardButton(text=t.TIME_3M, callback_data="conf_tmturn_180")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")]
    ])
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
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.MODE_CLASSIC_BTN, callback_data="conf_mode_Classic")],
        [types.InlineKeyboardButton(text=t.MODE_DUET_BTN, callback_data="conf_mode_Duet")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")]
    ])
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
    await update_registration_view(bot, callback.message.chat.id, game)

@router.callback_query(lambda c: c.data == "setup_lang")
async def setup_lang_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.LANG_UK_BTN, callback_data="conf_lang_uk")],
        [types.InlineKeyboardButton(text=t.LANG_EN_BTN, callback_data="conf_lang_en")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")]
    ])
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
    
    # Get custom dictionaries
    custom_dicts = await db_service.get_custom_dictionaries(callback.message.chat.id)
    
    t = get_text(game.language)
    buttons = []
    for s in sets:
        buttons.append([types.InlineKeyboardButton(text=t.WORD_SET_FORMAT.format(name=s), callback_data=f"conf_words_{s}")])
    
    for d in custom_dicts:
        buttons.append([types.InlineKeyboardButton(text=f"✨ {d.name}", callback_data=f"conf_words_custom_{d.name}")])

    await callback.message.edit_text(
        t.SET_WORDS_TITLE, 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons + [[types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")]])
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
async def cancel_registration(callback: types.CallbackQuery, bot: Bot):
    if not callback.message:
        return
        
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return await callback.answer()
        
    t = get_text(game.language)
    
    # Permission check: Only admin can cancel registration phase
    member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    
    if member.status not in ["administrator", "creator"]:
        return await callback.answer(t.ONLY_ADMIN_STOP, show_alert=True)
        
    manager.end_game(callback.message.chat.id)
    # Unpin if pinned
    try:
        await bot.unpin_chat_message(callback.message.chat.id, callback.message.message_id)
    except Exception:
        pass
        
    await callback.message.edit_text(t.GAME_STOPPED)
    await callback.answer()

@router.message(Command("stop"))
async def cmd_stop(message: types.Message, bot: Bot):
    game = manager.get_game(message.chat.id)
    if not game:
        return
        
    t = get_text(game.language)
    
    # Permission check: Only admin can stop the game
    if message.chat.type != "private":
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ONLY_ADMIN_STOP)
            
    manager.end_game(message.chat.id)
    
    # Unpin if pinned
    try:
        if game.board_msg_id:
            await bot.unpin_chat_message(message.chat.id, game.board_msg_id)
        elif game.metadata.get("registration_msg_id"):
            await bot.unpin_chat_message(message.chat.id, game.metadata["registration_msg_id"])
    except Exception:
        pass
        
    await message.answer(t.GAME_STOPPED)
