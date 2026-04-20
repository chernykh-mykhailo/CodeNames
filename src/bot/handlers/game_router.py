from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame, Team
from src.assets.texts import get_text
from src.core.database.service import db_service

router = Router()

@router.callback_query(lambda c: c.data == "game_start")
async def start_game(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game:
        t = get_text()
        return await callback.answer(t.GAME_NOT_FOUND, show_alert=True)
        
    if isinstance(game, CodeNamesGame):
        res = await game.start()
        if "❌" in res:
            return await callback.answer(res, show_alert=True)
            
        await callback.message.delete()
        
        # Send initial board
        board_img = game.get_board_image(spymaster_view=False)
        await bot.send_photo(
            callback.message.chat.id,
            photo=BufferedInputFile(board_img.read(), filename="board.png"),
            caption=game.get_status_message(),
            reply_markup=get_game_keyboard(game),
            message_thread_id=game.thread_id
        )
        
        # Notify spymasters in PM
        notified_spymasters = set()
        t = get_text(game.language)
        for team, uid in game.spymasters.items():
            if uid in notified_spymasters:
                continue
            
            try:
                sp_img = game.get_board_image(spymaster_view=True)
                
                if len(set(game.spymasters.values())) == 1 and len(game.players) == 3:
                    role_text = t.SPYMASTER_DUAL_ROLE
                else:
                    team_name = t.TEAM_RED_GEN if team == Team.RED else t.TEAM_BLUE_GEN
                    role_text = t.SPYMASTER_ROLE.format(team=team_name)

                await bot.send_photo(
                    uid,
                    photo=BufferedInputFile(sp_img.read(), filename="spymaster_board.png"),
                    caption=f"{role_text}\n\n{t.SPYMASTER_INSTRUCTIONS}"
                )
                notified_spymasters.add(uid)
            except Exception as e:
                player = game.players.get(uid)
                name = player.full_name if player else f"ID: {uid}"
                mention = f'<a href="tg://user?id={uid}">{name}</a>'
                await bot.send_message(
                    callback.message.chat.id, 
                    t.SPYMASTER_DM_ERROR.format(mention=mention),
                    message_thread_id=game.thread_id
                )
        game.start_timer(bot, callback.message)

def get_game_keyboard(game: CodeNamesGame):
    t = get_text(game.language)
    buttons = []
    
    # If it's spymaster's turn to give a clue
    if not game.engine.clue:
        buttons.append([types.InlineKeyboardButton(
            text=t.GIVE_HINT_BTN, 
            switch_inline_query_current_chat=f"hint_{game.chat_id} "
        )])
    else:
        # If it's operative's turn to guess
        buttons.append([types.InlineKeyboardButton(
            text=t.CHOOSE_WORD_BTN, 
            switch_inline_query_current_chat=f"reveal_{game.chat_id}"
        )])
        
    buttons.append([types.InlineKeyboardButton(text=t.PASS_BTN, callback_data="board_pass")])
    
    # Add Buffs button if the game is in progress
    if game.status == "in_progress":
        buttons.append([types.InlineKeyboardButton(text=t.BUFF_BTN, callback_data="game_buffs")])
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return kb

@router.callback_query(lambda c: c.data.startswith("board_"))
async def handle_board_action(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game or not isinstance(game, CodeNamesGame):
        return await callback.answer(get_text().GAME_NOT_FOUND, show_alert=True)
    
    t = get_text(game.language)
        
    if callback.data == "board_words":
        # Show words as buttons
        buttons = []
        for i, card in enumerate(game.engine.board):
            if not card.is_revealed:
                buttons.append(types.InlineKeyboardButton(text=card.word, callback_data=f"reveal_{i}"))
        
        # Chunk buttons by 2
        rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        rows.append([types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="board_back")])
        
        await callback.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=rows))
        
    elif callback.data == "board_back":
        await callback.message.edit_reply_markup(reply_markup=get_game_keyboard(game))
        
    elif callback.data == "board_pass":
        game.engine.end_turn()
        game.start_timer(bot, callback.message)
        await update_main_board(callback.message, game, bot)

@router.callback_query(lambda c: c.data.startswith("reveal_"))
async def handle_reveal(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game or not isinstance(game, CodeNamesGame):
        return await callback.answer(get_text().GAME_NOT_FOUND, show_alert=True)
        
    idx = int(callback.data.split("_")[1])
    game.engine.reveal_card(idx)
    
    await update_main_board(callback.message, game, bot)

async def update_main_board(message: types.Message, game: CodeNamesGame, bot: Bot):
    prev_turn = game.engine.current_turn
    board_img = game.get_board_image(spymaster_view=False)
    await message.edit_media(
        media=types.InputMediaPhoto(
            media=BufferedInputFile(board_img.read(), filename="board.png"),
            caption=game.get_status_message()
        ),
        reply_markup=get_game_keyboard(game)
    )
    
    if game.engine.current_turn != prev_turn:
        game.start_timer(bot, message)
    
    # If game ended
    if game.engine.winner:
        manager.end_game(message.chat.id)
        
        winner_team = game.engine.winner.value
        for player in game.players.values():
            result = "win" if player.team == winner_team else "loss"
            # For 3-player mode, the dual spymaster technically "wins" if they helped the winning team,
            # but we'll record it based on the primary winning team flag.
            await db_service.save_game_result(
                player.user_id, player.full_name, player.username, 
                "codenames", result
            )

        await bot.send_message(
            message.chat.id, 
            f"🎉 ГРУ ЗАКІНЧЕНО! Перемогли <b>{game.engine.winner.value.upper()}</b>",
            message_thread_id=game.thread_id
        )

@router.inline_query()
async def inline_word_search(query: types.InlineQuery):
    if query.query.startswith("reveal_"):
        chat_id_str = query.query.replace("reveal_", "")
        action = "reveal"
    elif query.query.startswith("hint_"):
        chat_id_str = query.query.replace("hint_", "").split(" ")[0]
        action = "hint"
    else:
        return
        
    try:
        chat_id = int(chat_id_str)
    except ValueError:
        return
        
    game = manager.get_game(chat_id)
    if not game or not isinstance(game, CodeNamesGame) or not game.engine:
        return await query.answer([], cache_time=1)
        
    results = []
    
    if action == "reveal":
        # Get unrevealed words
        for i, card in enumerate(game.engine.board):
            if not card.is_revealed:
                results.append(types.InlineQueryResultArticle(
                    id=f"word_{i}",
                    title=card.word,
                    input_message_content=types.InputTextMessageContent(message_text=card.word)
                ))
    elif action == "hint":
        # Check if query has "hint_ID message"
        parts = query.query.split(" ", 1)
        user_input = parts[1] if len(parts) > 1 else ""
        
        if user_input:
            input_parts = user_input.split()
            word = " ".join(input_parts[:-1]) if len(input_parts) > 1 else user_input
            count = input_parts[-1] if len(input_parts) > 1 and input_parts[-1].isdigit() else "?"
            
            if count != "?":
                results.append(types.InlineQueryResultArticle(
                    id="valid_hint",
                    title=f"✅ Підказка: {word.upper()} ({count})",
                    description="Натисніть сюди, щоб відправити",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"💡 {word.upper()} {count}" # We add an emoji to distinguish it
                    )
                ))
            else:
                results.append(types.InlineQueryResultArticle(
                    id="invalid_hint",
                    title="⚠️ Введіть слово та число",
                    description=f"Наприклад: {user_input if user_input else 'Дерево'} 2",
                    input_message_content=types.InputTextMessageContent(message_text="?")
                ))
            
    await query.answer(results, cache_time=1, is_personal=True)

# Handler for processing the word selected via inline or typed manually
@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    # If in group, settings for the current game
    game = manager.get_game(message.chat.id)
    if game:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=f"🎮 Режим: {game.metadata.get('mode', 'Classic')}", callback_data="setup_mode")],
            [types.InlineKeyboardButton(text=f"🌐 Мова: {game.language.upper()}", callback_data="setup_lang")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="setup_back")]
        ])
        await message.answer("⚙️ <b>Налаштування Codenames Master</b>", reply_markup=kb)
    else:
        await message.answer("ℹ️ Запустіть гру спочатку: /game_codenames")

@router.message()
async def handle_game_input(message: types.Message, bot: Bot):
    # First, try to find an active game in THIS chat
    game = manager.get_game(message.chat.id)
    
    if game and isinstance(game, CodeNamesGame) and game.status == "in_progress":
        text = message.text.strip().upper()
        
        # 1. Check if it's a word revelation (Guessing)
        # (Exclude messages that start with 💡 as they are hints)
        if not text.startswith("💡"):
            for i, card in enumerate(game.engine.board):
                if card.word == text and not card.is_revealed:
                    # Check if current user is an operative of the current team
                    player = game.players.get(message.from_user.id)
                    if not player or player.team != game.engine.current_turn.value:
                        if not (player and player.role == "dual_spymaster"): 
                            return 
                    
                    if player.role in ["spymaster", "dual_spymaster"]:
                        return await message.reply("🧙‍♂️ Капітанам не можна відгадувати слова!")

                    game.engine.reveal_card(i)
                    await update_main_board(message, game, bot)
                    return

        # 2. Check if it's a spymaster clue
        # Clean up the emoji if present
        hint_text = text.replace("💡", "").strip()
        res = await game.handle_message(message.from_user.id, hint_text)
        if res.get("clue_set"):
            game.start_timer(bot, message)
            await bot.send_message(
                message.chat.id, 
                f"🔎 Нова підказка: <b>{res['clue']}</b> ({res['count']})",
                message_thread_id=game.thread_id
            )
            await update_main_board(message, game, bot)
            return

@router.callback_query(lambda c: c.data == "game_refresh")
async def game_refresh_handler(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game: return
    await callback.message.edit_reply_markup(reply_markup=get_game_keyboard(game))

@router.callback_query(lambda c: c.data == "game_buffs")
async def show_buffs(callback: types.CallbackQuery):
    game = manager.get_game(callback.message.chat.id)
    if not game or game.status != "in_progress": return
    
    # Check if this user is a spymaster or it's Duet (everyone can use?)
    is_spymaster = callback.from_user.id in game.spymasters.values()
    if not is_spymaster:
        return await callback.answer("🔒 Тільки капітани можуть використовувати бафи!", show_alert=True)

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🕵️‍♂️ Розвідка (Відкрити 1 слово)", callback_data="buff_reveal")],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="game_refresh")]
    ])
    await callback.message.edit_text(game.get_status_message() + "\n\n⚡ <b>Оберіть баф:</b>", reply_markup=kb)

@router.callback_query(lambda c: c.data == "buff_reveal")
async def buff_reveal_handler(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game or game.status != "in_progress": return
    
    used_buffs = game.metadata.setdefault("used_buffs", [])
    
    # Find team
    team = None
    for t, uid in game.spymasters.items():
        if uid == callback.from_user.id:
            team = t
            break
    
    if not team: return
    
    team_buff_key = f"{team}_reveal"
    if team_buff_key in used_buffs:
        return await callback.answer("❌ Цей баф вже використано вашою командою!", show_alert=True)
    
    word = game.engine.use_buff_reveal()
    if word:
        used_buffs.append(team_buff_key)
        await callback.answer(f"🔍 Розвідка відкрила слово: {word}", show_alert=True)
        # Force update board image
        await update_main_board(callback.message, game, bot)
    else:
        await callback.answer("❌ Немає слів для розвідки.")
