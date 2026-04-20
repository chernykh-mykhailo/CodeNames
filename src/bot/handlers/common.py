from typing import Any
import asyncio
from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame
from src.core.platform.base_game import GamePlayer
from src.core.database.service import db_service
from src.assets.texts import get_text

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, bot: Bot):
    if command.args and command.args.startswith("join_"):
        chat_id = int(command.args.replace("join_", ""))
        game = manager.get_game(chat_id)
        
        t = get_text()
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
            
            # Try to construct a link to the message
            # For supergroups, ID starts with -100
            internal_chat_id = str(chat_id)
            if internal_chat_id.startswith("-100"):
                clean_id = internal_chat_id.replace("-100", "")
                chat_link = f"https://t.me/c/{clean_id}/{msg_id}"
            
            kb = None
            if chat_link:
                kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=t.RETURN_BTN, url=chat_link)]
                ])

            await message.answer(
                t.JOIN_SUCCESS,
                reply_markup=kb
            )
            # Update the message in the group
            await update_registration_view(bot, chat_id, game)
        else:
            await message.answer(t.ALREADY_JOINED)
        return

    t = get_text()
    await message.answer(t.WELCOME)
@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    stats = await db_service.get_user_stats(message.from_user.id)
    
    t = get_text()
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


@router.message(Command("codenames"))
async def start_codenames(message: types.Message, bot: Bot):
    t = get_text()
    if message.chat.type == "private":
        return await message.answer(f"❌ {t.MIN_PLAYERS}")
        
    game = manager.create_game(message.chat.id, CodeNamesGame, message.message_thread_id)
    
    # Deep link for joining
    join_url = f"https://t.me/{bot.username}?start=join_{message.chat.id}"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.JOIN_BTN, url=join_url)],
        [types.InlineKeyboardButton(text=t.START_BTN, callback_data="game_start")],
        [types.InlineKeyboardButton(text=t.SETTINGS_BTN, callback_data="game_settings")]
    ])
    
    sent_msg = await message.answer(
        t.REGISTRATION_TITLE.format(count=0),
        reply_markup=kb
    )
    # Store message_id for later updates
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
        [types.InlineKeyboardButton(text=t.START_BTN, callback_data="game_start")],
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
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.SET_MODE.format(mode=game.metadata.get('mode', 'Classic')), callback_data="setup_mode")],
        [types.InlineKeyboardButton(text=t.SET_LANG.format(lang=game.language.upper()), callback_data="setup_lang")],
        [types.InlineKeyboardButton(text=t.SET_WORDS.format(words=game.word_set), callback_data="setup_words")],
        [types.InlineKeyboardButton(text=t.SET_TIMER_REG.format(time=game.reg_timer//60), callback_data="setup_timer_reg")],
        [types.InlineKeyboardButton(text=t.SET_TIMER_TURN.format(time=game.turn_timer//60), callback_data="setup_timer_turn")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="setup_back")]
    ])
    
    await callback.message.edit_text(t.SETTINGS_TITLE, reply_markup=kb)

@router.callback_query(lambda c: c.data == "setup_timer_reg")
async def setup_timer_reg_menu(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
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
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    game.reg_timer = int(callback.data.replace("conf_tmreg_", ""))
    await show_settings(callback)

@router.callback_query(lambda c: c.data == "setup_timer_turn")
async def setup_timer_turn_menu(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
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
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    game.turn_timer = int(callback.data.replace("conf_tmturn_", ""))
    await show_settings(callback)

@router.callback_query(lambda c: c.data == "setup_mode")
async def setup_mode_menu(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.MODE_CLASSIC_BTN, callback_data="conf_mode_Classic")],
        [types.InlineKeyboardButton(text=t.MODE_DUET_BTN, callback_data="conf_mode_Duet")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")]
    ])
    await callback.message.edit_text(t.SET_MODE_TITLE, reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("conf_mode_"))
async def confirm_mode(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    game.metadata["mode"] = callback.data.replace("conf_mode_", "")
    await show_settings(callback)

@router.callback_query(lambda c: c.data == "setup_back")
async def settings_back(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    await update_registration_view(bot, callback.message.chat.id, game)

@router.callback_query(lambda c: c.data == "setup_lang")
async def setup_lang_menu(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Українська 🇺🇦", callback_data="conf_lang_uk")],
        [types.InlineKeyboardButton(text="English 🇺🇸", callback_data="conf_lang_en")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")]
    ])
    await callback.message.edit_text(t.SET_LANG_TITLE, reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("conf_lang_"))
async def confirm_lang(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    game.language = callback.data.replace("conf_lang_", "")
    await show_settings(callback)

@router.callback_query(lambda c: c.data == "setup_words")
async def setup_words_menu(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    
    from src.games.codenames.words import WordRepository
    repo = WordRepository()
    sets = repo.list_available_sets(game.language)
    
    t = get_text(game.language)
    buttons = []
    for s in sets:
        buttons.append([types.InlineKeyboardButton(text=f"📖 {s}", callback_data=f"conf_words_{s}")])
    
    await callback.message.edit_text(
        t.SET_WORDS_TITLE, 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons + [[types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_settings")]])
    )

@router.callback_query(lambda c: c.data.startswith("conf_words_"))
async def confirm_word_set(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    game.word_set = callback.data.replace("conf_words_", "")
    await show_settings(callback)
