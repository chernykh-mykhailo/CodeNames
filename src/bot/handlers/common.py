from typing import Any
from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame
from src.core.platform.base_game import GamePlayer
from src.core.database.service import db_service

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, bot: Bot):
    if command.args and command.args.startswith("join_"):
        chat_id = int(command.args.replace("join_", ""))
        game = manager.get_game(chat_id)
        
        if not game:
            return await message.answer("❌ Гра вже закінчилася або не знайдена.")
            
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
                    [types.InlineKeyboardButton(text="⬅️ Повернутися до гри", url=chat_link)]
                ])

            await message.answer(
                f"✅ Ви приєдналися до гри у чаті!",
                reply_markup=kb
            )
            # Update the message in the group
            await update_registration_view(bot, chat_id, game)
        else:
            await message.answer("ℹ️ Ви вже зареєстровані у цій грі.")
        return

    await message.answer(
        "👋 Вітаємо на платформі <b>Party Games</b>!\n\n"
        "Тут ви можете грати в улюблені настільні ігри прямо в чаті.\n"
        "Доступні ігри:\n"
        "- /game_codenames — Кодові Імена\n\n"
        "📊 Твоя статистика: /stats"
    )
@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    stats = await db_service.get_user_stats(message.from_user.id)
    
    if not stats or stats.total == 0:
        return await message.answer("📊 У вас ще немає зіграних ігор. Час це виправити! /game_codenames")
    
    wins = stats.wins or 0
    losses = stats.losses or 0
    total = stats.total
    winrate = (wins / total * 100) if total > 0 else 0
    
    text = (
        f"📊 <b>Твоя статистика (Codenames)</b>\n\n"
        f"🎮 Всього ігор: <b>{total}</b>\n"
        f"✅ Перемог: <b>{wins}</b>\n"
        f"❌ Поразок: <b>{losses}</b>\n\n"
        f"🏆 Вінрейт: <b>{winrate:.1f}%</b>"
    )
    
    await message.answer(text)


@router.message(Command("game_codenames"))
async def start_codenames(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        return await message.answer("❌ Будь ласка, запустіть гру в груповому чаті!")
        
    game = manager.create_game(message.chat.id, CodeNamesGame, message.message_thread_id)
    
    # Deep link for joining
    join_url = f"https://t.me/{bot.username}?start=join_{message.chat.id}"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🙋‍♂️ Приєднатися", url=join_url)],
        [types.InlineKeyboardButton(text="🚀 Розпочати", callback_data="game_start")],
        [types.InlineKeyboardButton(text="⚙️ Налаштування", callback_data="game_settings")]
    ])
    
    sent_msg = await message.answer(
        "📝 <b>Реєстрація на гру Кодові Імена</b>\n"
        "Натисніть кнопку нижче, щоб приєднатися до гри.",
        reply_markup=kb
    )
    # Store message_id for later updates
    game.metadata["registration_msg_id"] = sent_msg.message_id

async def update_registration_view(bot: Bot, chat_id: int, game: Any):
    msg_id = game.metadata.get("registration_msg_id")
    if not msg_id:
        return
        
    mentions = []
    for p in game.players.values():
        link = f'<a href="tg://user?id={p.user_id}">{p.full_name}</a>'
        mentions.append(f"- {link}")

    text = (
        f"📝 <b>Реєстрація на гру Кодові Імена</b>\n"
        f"Гравців: {len(game.players)}\n\n"
        f"Поточний склад:\n" + "\n".join(mentions)
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🙋‍♂️ Приєднатися", url=f"https://t.me/{bot.username}?start=join_{chat_id}")],
        [types.InlineKeyboardButton(text="🚀 Розпочати", callback_data="game_start")],
        [types.InlineKeyboardButton(text="⚙️ Налаштування", callback_data="game_settings")]
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
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🌐 Мова: {game.language.upper()}", callback_data="setup_lang")],
        [types.InlineKeyboardButton(text=f"📚 Словник: {game.word_set}", callback_data="setup_words")],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="setup_back")]
    ])
    
    await callback.message.edit_text("⚙️ <b>Налаштування гри</b>", reply_markup=kb)

@router.callback_query(lambda c: c.data == "setup_back")
async def settings_back(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    await update_registration_view(bot, callback.message.chat.id, game)

@router.callback_query(lambda c: c.data == "setup_lang")
async def setup_lang_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Українська 🇺🇦", callback_data="conf_lang_uk")],
        [types.InlineKeyboardButton(text="English 🇺🇸", callback_data="conf_lang_en")],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="game_settings")]
    ])
    await callback.message.edit_text("🌐 <b>Оберіть мову слів:</b>", reply_markup=kb)

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
    
    buttons = []
    for s in sets:
        buttons.append([types.InlineKeyboardButton(text=f"📖 {s}", callback_data=f"conf_words_{s}")])
    buttons.append([types.InlineKeyboardButton(text="⬅️ Назад", callback_data="game_settings")])
    
    await callback.message.edit_text("📚 <b>Оберіть набір слів:</b>", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data.startswith("conf_words_"))
async def confirm_word_set(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    game.word_set = callback.data.replace("conf_words_", "")
    await show_settings(callback)
