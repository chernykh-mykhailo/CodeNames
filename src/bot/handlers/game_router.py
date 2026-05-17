import asyncio
import logging
from typing import Optional, List, Dict
from aiogram import Router, types, Bot
from aiogram.types import BufferedInputFile, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame
from src.games.codenames.engine import CardColor, Team
from src.assets.texts import get_text
from src.core.database.service import db_service

logger = logging.getLogger(__name__)
router = Router()

async def get_game_keyboard(game: CodeNamesGame):
    t = get_text(game.language)
    buttons = []

    if game.button_board:
        # Render the board as styled buttons
        state = game.engine.get_board_state(revealed_only=False)
        for i in range(0, len(state), game.board_size):
            row = []
            for j in range(i, i + game.board_size):
                card = state[j]
                if card["is_revealed"]:
                    color_val = card["color"]
                    text = card["word"]
                    style = None
                    emoji = "⚪ "
                    
                    if game.engine.mode == "duet":
                        if color_val == CardColor.BLUE.value:
                            style = "success"
                            emoji = "🟢 "
                        elif color_val == CardColor.ASSASSIN.value:
                            style = "danger"
                            emoji = "💀 "
                    else:
                        if color_val == CardColor.GREEN.value:
                            style = "success"
                            emoji = "🟢 "
                        elif color_val == CardColor.BLUE.value:
                            style = "primary"
                            emoji = "🔵 "
                        elif color_val == CardColor.ASSASSIN.value:
                            style = "danger"
                            emoji = "💀 "
                    
                    row.append(types.InlineKeyboardButton(
                        text=f"{emoji}{text}", 
                        callback_data=f"reveal_{j}",
                        style=style
                    ))
                else:
                    row.append(types.InlineKeyboardButton(
                        text=card["word"], 
                        callback_data=f"reveal_{j}"
                    ))
            buttons.append(row)
        buttons.append([types.InlineKeyboardButton(text="—" * 10, callback_data="none")])

    # Hint / Choose Word Logic
    if not game.engine.clue:
        buttons.append([
            types.InlineKeyboardButton(
                text=t.GIVE_HINT_BTN,
                switch_inline_query_current_chat=f"hint_{game.chat_id} ",
            )
        ])
    else:
        if not game.button_board:
            buttons.append([
                types.InlineKeyboardButton(
                    text=t.CHOOSE_WORD_BTN,
                    switch_inline_query_current_chat=f"reveal_{game.chat_id}",
                )
            ])

    buttons.append([types.InlineKeyboardButton(text=t.PASS_BTN, callback_data="board_pass")])

    settings = await db_service.get_chat_settings(game.chat_id)
    if game.status == "in_progress" and settings.allow_buffs:
        buttons.append([types.InlineKeyboardButton(text=t.SHOP_BTN, callback_data="game_shop")])

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

async def update_main_board(message: types.Message, game: CodeNamesGame, bot: Bot):
    t = get_text(game.language)
    
    status_text = t.DUET_HEADER if game.engine.mode == "duet" else t.CLASSIC_HEADER.format(
        team=t.TEAM_RED if game.engine.current_turn == Team.GREEN else t.TEAM_BLUE
    )
    
    clue_text = ""
    if game.engine.clue:
        clue_text = f"\n{t.NEW_CLUE.format(clue=game.engine.clue, count=game.engine.clue_count)}"
        clue_text += f"\n🤔 Спроб залишилось: <b>{game.engine.remaining_guesses}</b>"
    
    # Calculate stats for caption
    found = 0
    total_to_find = 0
    if game.engine.mode == "duet":
        # In duet total agents is 15
        total_to_find = 15
        for i in range(len(game.engine.board)):
            if game.engine.board[i].is_revealed:
                ca = game.engine.get_duet_color(i, "a")
                cb = game.engine.get_duet_color(i, "b")
                if ca == CardColor.BLUE or cb == CardColor.BLUE:
                    found += 1
    else:
        total_to_find = (game.board_size * game.board_size // 3) + 1
        found = sum(1 for c in game.engine.board if c.is_revealed and c.color.value == game.engine.current_turn.value)

    caption = f"{status_text}\n{clue_text}\n\n{t.GAME_STATS.format(duration='...', found=found, total=total_to_find)}"
    
    kb = await get_game_keyboard(game)
    board_img = game.get_board_image(spymaster_view=False)
    
    try:
        await bot.edit_message_media(
            chat_id=game.chat_id,
            message_id=game.board_msg_id,
            media=types.InputMediaPhoto(
                media=BufferedInputFile(board_img.read(), filename="board.png"),
                caption=caption,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Board update failed: {e}")

@router.callback_query(lambda c: c.data == "game_start")
async def start_game(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game: return await callback.answer("❌ Гра не знайдена")
    
    t = get_text(game.language)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    game.dark_mode = chat_settings.dark_mode
    game.button_board = chat_settings.button_board
    
    if not chat_settings.allow_everyone_start:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(t.ADMIN_ONLY_ERROR, show_alert=True)
            
    if len(game.players) < 2:
        return await callback.answer(t.MIN_PLAYERS, show_alert=True)
        
    start_msg = await game.start()
    board_img = game.get_board_image(spymaster_view=False)
    kb = await get_game_keyboard(game)
    
    sent_board = await bot.send_photo(
        callback.message.chat.id,
        photo=BufferedInputFile(board_img.read(), filename="board.png"),
        caption=start_msg,
        reply_markup=kb,
        message_thread_id=game.thread_id
    )
    game.board_msg_id = sent_board.message_id
    
    for team, sm_id in game.spymasters.items():
        if sm_id:
            sm_img = game.get_board_image(spymaster_view=True)
            role_msg = t.SPYMASTER_ROLE.format(team=t.TEAM_RED if team == Team.GREEN else t.TEAM_BLUE)
            try:
                await bot.send_photo(sm_id, photo=BufferedInputFile(sm_img.read(), filename="map.png"), caption=f"{role_msg}\n\n{t.SPYMASTER_INSTRUCTIONS}")
            except:
                await callback.message.answer(t.SPYMASTER_DM_ERROR.format(mention=f"ID {sm_id}"))

    await callback.message.delete()
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("reveal_"))
async def handle_reveal(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game or game.status != "in_progress": return await callback.answer()
    
    t = get_text(game.language)
    idx = int(callback.data.replace("reveal_", ""))
    
    # Permission logic
    player = game.players.get(callback.from_user.id)
    if not player: return await callback.answer(t.NOT_A_PLAYER, show_alert=True)
    
    current_team = game.engine.current_turn
    # In Codenames, spymaster gives clue, agents guess.
    # If it's GREEN turn, GREEN spymaster gave clue, GREEN agents guess.
    if player.role == "spymaster" or player.role == "dual_spymaster":
        return await callback.answer(t.SPYMASTER_GUESS_ERROR, show_alert=True)
        
    if player.team != current_team.value and game.engine.mode != "duet":
        return await callback.answer(t.NOT_YOUR_TURN, show_alert=True)

    if not game.engine.clue:
        return await callback.answer(t.SPYMASTER_WAIT, show_alert=True)

    if game.engine.reveal_card(idx):
        await update_main_board(callback.message, game, bot)
        
        if game.engine.is_over:
            winner_text = t.WIN_RED if game.engine.winner == Team.GREEN else t.WIN_BLUE
            if game.engine.mode == "duet":
                winner_text = t.WIN_DUET if game.engine.winner else t.LOSE_DUET
            
            await bot.send_message(game.chat_id, t.GAME_ENDED_TITLE.format(winner=winner_text), message_thread_id=game.thread_id)
            manager.end_game(game.chat_id)
    
    await callback.answer()

@router.callback_query(lambda c: c.data == "board_pass")
async def handle_pass(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game: return await callback.answer()
    
    player = game.players.get(callback.from_user.id)
    if not player or player.team != game.engine.current_turn.value:
        return await callback.answer(get_text(game.language).NOT_YOUR_TURN, show_alert=True)
        
    game.engine.end_turn()
    await update_main_board(callback.message, game, bot)
    await callback.answer()

@router.inline_query(lambda q: q.query.startswith("hint_"))
async def inline_hint(query: InlineQuery):
    chat_id = int(query.query.split("_")[1].split(" ")[0])
    game = manager.get_game(chat_id)
    if not game: return
    
    t = get_text(game.language)
    parts = query.query.strip().split(" ")
    
    if len(parts) >= 3:
        word = parts[1]
        count = parts[2]
        if count.isdigit():
            await query.answer([
                InlineQueryResultArticle(
                    id=f"hint_{chat_id}",
                    title=t.INLINE_VALID_HINT_TITLE.format(word=word, count=count),
                    input_message_content=InputTextMessageContent(message_text=f"HINT: {word} {count}"),
                    callback_data=f"set_hint_{chat_id}_{word}_{count}"
                )
            ], cache_time=1)

@router.message(lambda m: m.text and m.text.startswith("HINT: "))
async def process_hint_text(message: types.Message, bot: Bot):
    # This captures the spymaster's hint sent via inline
    game = manager.get_game(message.chat.id)
    if not game: return
    
    parts = message.text.replace("HINT: ", "").split(" ")
    if len(parts) == 2:
        word, count = parts[0], int(parts[1])
        game.engine.set_clue(word, count)
        await update_main_board(message, game, bot)
        await message.delete()

@router.callback_query(lambda c: c.data == "none")
async def cb_none(callback: types.CallbackQuery):
    await callback.answer()

@router.callback_query(lambda c: c.data == "game_shop")
async def cb_game_shop(callback: types.CallbackQuery):
    # Delegate to shop handler
    await callback.answer("Opening shop...")
