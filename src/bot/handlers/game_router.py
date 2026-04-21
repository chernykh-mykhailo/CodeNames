import logging
from typing import Optional
from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame, Team
from src.games.codenames.engine import CardColor
from src.assets.texts import get_text
from src.core.database.service import db_service
from src.core.platform.base_game import GamePlayer
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.games.codenames.words import WordRepository
import random

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("stop_game"))
@router.message(Command("stop"))
async def cmd_stop(message: types.Message, bot: Bot):
    game = manager.get_game(message.chat.id)
    if not game:
        return
        
    t = get_text(game.language)
    
    # Check permissions
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"] and message.from_user.id not in game.players:
        return await message.answer(t.ONLY_ADMIN_STOP)
        
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅", callback_data="confirm_stop")],
        [types.InlineKeyboardButton(text="❌", callback_data="cancel_stop")]
    ])
    
    await message.answer(t.GAME_STOPPED_CONFIRM, reply_markup=kb)

@router.callback_query(lambda c: c.data == "confirm_stop")
async def confirm_stop(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return await callback.message.delete()
        
    t = get_text(game.language)
    
    # Permission check for callback
    member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if member.status not in ["administrator", "creator"] and callback.from_user.id not in game.players:
        return await callback.answer(t.ONLY_ADMIN_STOP, show_alert=True)
        
    # Unpin board
    if game.board_msg_id:
        try:
            await bot.unpin_chat_message(callback.message.chat.id, game.board_msg_id)
        except Exception:
            pass
            
    # Delete last turn
    if game.last_turn_msg_id:
        try:
            await bot.delete_message(callback.message.chat.id, game.last_turn_msg_id)
        except Exception:
            pass
            
    manager.end_game(callback.message.chat.id)
    await callback.message.edit_text(t.GAME_STOPPED)

@router.callback_query(lambda c: c.data == "cancel_stop")
async def cancel_stop(callback: types.CallbackQuery):
    await callback.message.delete()

@router.message(Command("leave"))
async def cmd_leave(message: types.Message, bot: Bot):
    game = manager.get_game(message.chat.id)
    if not game:
        return
        
    t = get_text(game.language)
    if message.from_user.id not in game.players:
        return
        
    player_name = game.players[message.from_user.id].full_name
    del game.players[message.from_user.id]
    
    await message.answer(t.PLAYER_LEFT.format(name=player_name))
    
    if game.status == "registration":
        from src.bot.handlers.common import update_registration_view
        await update_registration_view(bot, message.chat.id, game)
    elif game.status == "in_progress":
        if not game.players:
            # Cleanup turn msg before ending
            if game.last_turn_msg_id:
                try:
                    await bot.delete_message(message.chat.id, game.last_turn_msg_id)
                except Exception:
                    pass
            # Unpin board
            if game.board_msg_id:
                try:
                    await bot.unpin_chat_message(message.chat.id, game.board_msg_id)
                except Exception:
                    pass
            manager.end_game(message.chat.id)
            await message.answer(t.GAME_STOPPED)
        else:
            await update_main_board(message, game, bot)


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
        sent_board = await bot.send_photo(
            callback.message.chat.id,
            photo=BufferedInputFile(board_img.read(), filename="board.png"),
            caption=game.get_status_message(),
            reply_markup=await get_game_keyboard(game),
            message_thread_id=game.thread_id,
        )
        game.board_msg_id = sent_board.message_id
        
        # Pin the board
        try:
            await bot.pin_chat_message(callback.message.chat.id, sent_board.message_id, disable_notification=True)
        except Exception:
            pass
            
        await announce_turn(callback.message.chat.id, game, bot)

        # Notify spymasters in PM
        notified_spymasters = set()
        t = get_text(game.language)
        for team, uid in game.spymasters.items():
            if uid in notified_spymasters:
                continue

            try:
                duet_side = None
                if game.metadata.get("mode") == "Duet":
                    duet_side = "a" if team == Team.RED else "b"
                
                sp_img = game.get_board_image(spymaster_view=True, duet_side=duet_side)

                mode = game.metadata.get("mode")
                if mode == "Duet":
                    role_text = t.DUET_HEADER
                elif len(set(game.spymasters.values())) == 1 and len(game.players) == 3:
                    role_text = t.SPYMASTER_DUAL_ROLE
                else:
                    team_name = t.TEAM_RED_GEN if team == Team.RED else t.TEAM_BLUE_GEN
                    role_text = t.SPYMASTER_ROLE.format(team=team_name)

                await bot.send_photo(
                    uid,
                    photo=BufferedInputFile(
                        sp_img.read(), filename="spymaster_board.png"
                    ),
                    caption=f"{role_text}\n\n{t.SPYMASTER_INSTRUCTIONS}",
                )
                notified_spymasters.add(uid)
            except Exception:
                player = game.players.get(uid)
                name = player.full_name if player else f"ID: {uid}"
                mention = f'<a href="tg://user?id={uid}">{name}</a>'
                await bot.send_message(
                    callback.message.chat.id,
                    t.SPYMASTER_DM_ERROR.format(mention=mention),
                    message_thread_id=game.thread_id,
                )
        game.start_timer(bot, callback.message)
        await announce_turn(callback.message.chat.id, game, bot)


async def get_game_keyboard(game: CodeNamesGame):
    t = get_text(game.language)
    buttons = []

    # If it's spymaster's turn to give a clue
    if not game.engine.clue:
        buttons.append(
            [
                types.InlineKeyboardButton(
                    text=t.GIVE_HINT_BTN,
                    switch_inline_query_current_chat=f"hint_{game.chat_id} ",
                )
            ]
        )
    else:
        # If it's operative's turn to guess
        buttons.append(
            [
                types.InlineKeyboardButton(
                    text=t.CHOOSE_WORD_BTN,
                    switch_inline_query_current_chat=f"reveal_{game.chat_id}",
                )
            ]
        )

    buttons.append(
        [types.InlineKeyboardButton(text=t.PASS_BTN, callback_data="board_pass")]
    )

    # Add Shop button if the game is in progress and buffs are allowed
    settings = await db_service.get_chat_settings(game.chat_id)
    if game.status == "in_progress" and settings.allow_buffs:
        buttons.append(
            [types.InlineKeyboardButton(text=t.SHOP_BTN, callback_data="game_shop")]
        )

    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return kb


@router.callback_query(lambda c: c.data.startswith("board_"))
async def handle_board_action(callback: types.CallbackQuery, bot: Bot):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game or not isinstance(game, CodeNamesGame):
        return await callback.answer(get_text().GAME_NOT_FOUND, show_alert=True)

    t = get_text(game.language)

    if callback.data == "board_words":
        # Show words as buttons
        buttons = []
        for i, card in enumerate(game.engine.board):
            if not card.is_revealed:
                buttons.append(
                    types.InlineKeyboardButton(
                        text=card.word, callback_data=f"reveal_{i}"
                    )
                )

        # Chunk buttons by 2
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        rows.append(
            [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="board_back")]
        )

        await callback.message.edit_reply_markup(
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=rows)
        )

    elif callback.data == "board_back":
        await callback.message.edit_reply_markup(reply_markup=get_game_keyboard(game))

    elif callback.data == "board_pass":
        # Check if it's actually guessing phase (clue exists)
        if not game.engine.clue:
            return await callback.answer(t.SPYMASTER_WAIT, show_alert=True)
            
        # Check if this player is the one WHO should guess
        # In Duet, if current_turn is RED, BLUE side guesses.
        current_team = game.engine.current_turn
        guesser_team = Team.BLUE if current_team == Team.RED else Team.RED
        if callback.from_user.id != game.spymasters.get(guesser_team):
            return await callback.answer(t.NOT_YOUR_TURN, show_alert=True)

        game.engine.end_turn()
        game.start_timer(bot, callback.message)
        await announce_turn(callback.message.chat.id, game, bot)
        await update_main_board(callback.message, game, bot)


@router.callback_query(lambda c: c.data.startswith("reveal_"))
async def handle_reveal(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game or not isinstance(game, CodeNamesGame):
        return await callback.answer(get_text().GAME_NOT_FOUND, show_alert=True)

    idx = int(callback.data.split("_")[-1])
    t = get_text(game.language)
    
    # NEW: Check for targeted remap
    pending_user = game.metadata.get("pending_remap_user")
    if pending_user:
        if pending_user != callback.from_user.id:
            return await callback.answer(t.SPYMASTER_REMAP_ONLY, show_alert=True)
            
        # Perform swap
        repo = WordRepository()
        words = repo.get_set(game.language, game.word_set)
        existing = [c.word for c in game.engine.board]
        available = [w for w in words if w not in existing]
        new_word = random.choice(available) if available else "???"
        
        if game.engine.use_buff_remap(idx, new_word):
            game.metadata.pop("pending_remap_user")
            await callback.answer(t.BUY_SUCCESS)
            await update_main_board(callback.message, game, bot)
        else:
            await callback.answer(t.ALREADY_REVEALED, show_alert=True)
        return

    # SECURITY: Check if guessing phase and right player
    t = get_text(game.language)
    if not game.engine.clue:
        return await callback.answer(t.SPYMASTER_WAIT, show_alert=True)
        
    current_team = game.engine.current_turn
    guesser_team = Team.BLUE if current_team == Team.RED else Team.RED
    if callback.from_user.id != game.spymasters.get(guesser_team):
        return await callback.answer(t.NOT_YOUR_TURN, show_alert=True)

    game.engine.reveal_card(idx)
    await update_main_board(callback.message, game, bot)


async def update_main_board(
    message: types.Message, 
    game: CodeNamesGame, 
    bot: Bot, 
    prev_turn: Optional[Team] = None
):
    if prev_turn is None:
        prev_turn = game.engine.current_turn
        
    msg_id = game.board_msg_id
    if not msg_id:
        # Fallback to the message that triggered the update
        msg_id = getattr(message, "message_id", None)
        if not msg_id:
            return

    board_img = game.get_board_image(spymaster_view=False)
    try:
        await bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=msg_id,
            media=types.InputMediaPhoto(
                media=BufferedInputFile(board_img.read(), filename="board.png"),
                caption=game.get_status_message(),
            ),
            reply_markup=await get_game_keyboard(game),
        )
    except Exception as e:
        if "message is not modified" in str(e):
            return
        logger.error(f"Failed to update board: {e}")

    if game.engine.current_turn != prev_turn:
        game.start_timer(bot, message)
        await announce_turn(message.chat.id, game, bot)

    # If game ended
    if game.engine.is_over:
        manager.end_game(message.chat.id)
        t = get_text(game.language)
        
        mode = game.metadata.get("mode", "Classic").lower()
        
        # Calculate duration
        import time
        duration_sec = int(time.time() - game.start_time) if game.start_time else 0
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        duration_str = f"{minutes:02d}:{seconds:02d}"
        
        # Stats: found words
        if mode == "duet":
            # 15 unique agent positions in Duet
            found = 0
            for i in range(25):
                color_a = game.engine.get_duet_color(i, "a")
                color_b = game.engine.get_duet_color(i, "b")
                if (color_a == CardColor.BLUE or color_b == CardColor.BLUE) and game.engine.board[i].is_revealed:
                    found += 1
            total = 15
        else:
            # Classic
            winner_team = game.engine.winner
            # Found words for the winner
            found = len([c for c in game.engine.board if c.is_revealed and c.color.value == winner_team.value])
            total = 9 if game.engine.first_team == winner_team else 8
            
        stats_text = t.GAME_STATS.format(duration=duration_str, found=found, total=total)

        # Result title
        if mode == "duet":
            if game.engine.is_assassin_hit:
                res_title = t.LOSE_DUET
            else:
                res_title = t.WIN_DUET
        else:
            res_title = t.GAME_ENDED_TITLE.format(winner=game.engine.winner.value.upper())

        # Save results to DB
        if mode != "duet":
            winner_val = game.engine.winner.value
            for player in game.players.values():
                result = "win" if player.team == winner_val else "loss"
                await db_service.save_game_result(
                    player.user_id, player.full_name, player.username, "codenames", result
                )
        else:
            # Everyone wins/loses together in Duet
            result = "win" if not game.engine.is_assassin_hit else "loss"
            for player in game.players.values():
                await db_service.save_game_result(
                    player.user_id, player.full_name, player.username, "codenames", result
                )

        await bot.send_message(
            message.chat.id,
            f"{res_title}\n\n{stats_text}",
            message_thread_id=game.thread_id,
        )
        
        # Unpin board
        if game.board_msg_id:
            try:
                await bot.unpin_chat_message(message.chat.id, game.board_msg_id)
            except Exception:
                pass
            
        # Delete last turn announcement
        if game.last_turn_msg_id:
            try:
                await bot.delete_message(message.chat.id, game.last_turn_msg_id)
                game.last_turn_msg_id = None
            except Exception:
                pass


@router.inline_query()
async def inline_word_search(query: types.InlineQuery, bot: Bot):
    query_parts = query.query.split(" ", 1)
    query_text = query_parts[1].lower() if len(query_parts) > 1 else ""
    
    if query.query.startswith("reveal_"):
        chat_id_str = query_parts[0].replace("reveal_", "")
        action = "reveal"
    elif query.query.startswith("hint_"):
        chat_id_str = query_parts[0].replace("hint_", "")
        action = "hint"
    else:
        return

    try:
        chat_id = int(chat_id_str)
    except ValueError:
        return

    game = manager.get_game(chat_id)
    t = get_text(game.language if game else "uk")
    
    if not game or not isinstance(game, CodeNamesGame) or not game.engine:
        # Return a result inviting to start a new game
        return await query.answer(
            [
                types.InlineQueryResultArticle(
                    id="no_game",
                    title=t.NO_GAME_IN_CHAT,
                    description=t.START_GAME_BTN,
                    input_message_content=types.InputTextMessageContent(
                        message_text="/codenames"
                    ),
                )
            ],
            cache_time=1,
            is_personal=True
        )
    
    # 1. Identify User Status and Performer
    player = game.players.get(query.from_user.id)
    current_team = game.engine.current_turn
    is_spymaster_turn = not bool(game.engine.clue)
    
    can_perform = False
    if player:
        if action == "hint":
            # Only current spymaster can give a hint and only if it's their turn phase
            if is_spymaster_turn:
                current_spymaster_id = game.spymasters.get(current_team)
                if query.from_user.id == current_spymaster_id:
                    can_perform = True
        elif action == "reveal":
            # Operatives' phase
            if not is_spymaster_turn:
                mode = game.metadata.get("mode", "Classic").lower()
                if mode == "duet":
                    # In Duet, the OPPOSITE side guesses
                    other_side = Team.BLUE if current_team == Team.RED else Team.RED
                    if player.user_id == game.spymasters.get(other_side):
                        can_perform = True
                else:
                    # Classic: Same team, role is agent
                    if player.team == current_team.value and player.role == "agent":
                        can_perform = True
                    elif player.team == current_team.value and player.role == "dual_spymaster":
                        # Dual spymaster can't reveal! 
                        can_perform = False

    if not can_perform:
        if not player:
            # Result for non-players: Offer to join
            me = await bot.me()
            join_url = f"https://t.me/{me.username}?start=join_{chat_id}"
            return await query.answer(
                [
                    types.InlineQueryResultArticle(
                        id="not_a_player",
                        title=t.NOT_A_PLAYER,
                        description=t.NOT_A_PLAYER_DESC,
                        input_message_content=types.InputTextMessageContent(
                            message_text=t.NOT_A_PLAYER
                        ),
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                            [types.InlineKeyboardButton(text=t.JOIN_BTN, url=join_url)]
                        ])
                    )
                ],
                cache_time=1,
                is_personal=True
            )
        else:
            # Result for players whose turn it isn't
            return await query.answer(
                [
                    types.InlineQueryResultArticle(
                        id="not_your_turn",
                        title=t.NOT_YOUR_TURN,
                        description=t.NOT_YOUR_TURN_DESC,
                        input_message_content=types.InputTextMessageContent(
                            message_text="⏳" 
                        ),
                    )
                ],
                cache_time=1,
                is_personal=True
            )

    results = []

    if action == "reveal":
        # Get unrevealed words, filtered by query_text
        for i, card in enumerate(game.engine.board):
            if not card.is_revealed and (not query_text or query_text in card.word.lower()):
                results.append(
                    types.InlineQueryResultArticle(
                        id=f"word_{i}",
                        title=card.word,
                        input_message_content=types.InputTextMessageContent(
                            message_text=card.word
                        ),
                    )
                )
    elif action == "hint":
        # Check if query has "hint_ID message"
        parts = query.query.split(" ", 1)
        user_input = parts[1].strip() if len(parts) > 1 else ""

        if not user_input:
            # Show instruction as an article
            results.append(
                types.InlineQueryResultArticle(
                    id="hint_instruction",
                    title=t.INLINE_HINT_TITLE,
                    description=t.INLINE_HINT_DESC,
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"{t.INLINE_HINT_TITLE}\n{t.INLINE_HINT_DESC}"
                    )
                )
            )
        else:
            input_parts = user_input.split()
            word = " ".join(input_parts[:-1]) if len(input_parts) > 1 else user_input
            count = (
                input_parts[-1]
                if len(input_parts) > 1 and input_parts[-1].isdigit()
                else "?"
            )

            if count != "?":
                results.append(
                    types.InlineQueryResultArticle(
                        id="valid_hint",
                        title=t.INLINE_VALID_HINT_TITLE.format(
                            word=word.upper(), count=count
                        ),
                        description=t.INLINE_VALID_HINT_DESC,
                        input_message_content=types.InputTextMessageContent(
                            message_text=f"💡 {word.upper()} {count}"  # We add an emoji to distinguish it
                        ),
                    )
                )
            else:
                example = user_input if user_input else t.EXAMPLE_WORD
                results.append(
                    types.InlineQueryResultArticle(
                        id="invalid_hint",
                        title=t.INLINE_INVALID_HINT_TITLE,
                        description=t.INLINE_INVALID_HINT_DESC.format(input=example),
                        input_message_content=types.InputTextMessageContent(
                            message_text="?"
                        ),
                    )
                )

    await query.answer(results, cache_time=1, is_personal=True)


# Handler for processing the word selected via inline or typed manually
@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    # If in group, settings for the current game
    game = manager.get_game(message.chat.id)
    if game:
        t = get_text(game.language)
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=t.SET_MODE.format(
                            mode=game.metadata.get("mode", "Classic")
                        ),
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
                        text=t.BACK_BTN, callback_data="setup_back"
                    )
                ],
            ]
        )
        await message.answer(t.REG_START_DESC, reply_markup=kb)
    else:
        t = get_text()
        await message.answer(t.START_GAME_FIRST)


@router.message()
async def handle_game_input(message: types.Message, bot: Bot):
    # First, try to find an active game in THIS chat
    game = manager.get_game(message.chat.id)

    if game and isinstance(game, CodeNamesGame) and game.status == "in_progress":
        t = get_text(game.language)
        text = message.text.strip().upper()

        # 1. Check if it's a word revelation (Guessing)
        if not text.startswith("💡"):
            for i, card in enumerate(game.engine.board):
                if card.word.strip().upper() == text and not card.is_revealed:
                    # Check if current user is an operative of the correct team/role
                    player = game.players.get(message.from_user.id)
                    if not player:
                        return
                        
                    is_spymaster_turn = not bool(game.engine.clue)
                    if is_spymaster_turn:
                        # Cannot guess if hint phase!
                        return

                    mode = game.metadata.get("mode", "Classic").lower()
                    can_guess = False
                    
                    if mode == "duet":
                        # In Duet, the OTHER side guesses
                        other_side = Team.BLUE if game.engine.current_turn == Team.RED else Team.RED
                        if player.user_id == game.spymasters.get(other_side):
                            can_guess = True
                    else:
                        # Classic
                        if player.team == game.engine.current_turn.value and player.role == "agent":
                            can_guess = True
                    
                    if not can_guess:
                        if player.role in ["spymaster", "dual_spymaster"]:
                            return await message.reply(t.SPYMASTER_GUESS_ERROR)
                        return # Wrong team/performer

                    game.engine.reveal_card(i)
                    await update_main_board(message, game, bot)
                    return

        # 2. Check if it's a spymaster clue
        res = await game.handle_message(message.from_user.id, message.text)
        if res.get("clue_set"):
            game.start_timer(bot, message)
            await announce_turn(message.chat.id, game, bot)
            await update_main_board(message, game, bot)
            logger.info(f"Sending NEW_CLUE to chat {message.chat.id} thread {game.thread_id}")
            await bot.send_message(
                message.chat.id,
                t.NEW_CLUE.format(clue=res["clue"], count=res["count"]),
                message_thread_id=game.thread_id,
                parse_mode="HTML"
            )
            await update_main_board(message, game, bot)
            try:
                await message.delete()
            except Exception:
                pass
        elif res.get("error"):
            await message.answer(res["error"])


@router.callback_query(lambda c: c.data == "game_refresh")
async def game_refresh_handler(callback: types.CallbackQuery, bot: Bot):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    await callback.message.edit_reply_markup(reply_markup=await get_game_keyboard(game))


@router.callback_query(lambda c: c.data == "game_shop")
async def show_shop(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game or game.status != "in_progress":
        return

    t = get_text(game.language)
    
    # Check if this user is a spymaster
    is_spymaster = callback.from_user.id in game.spymasters.values()
    if not is_spymaster:
        return await callback.answer(t.SPYMASTER_BUFF_ONLY, show_alert=True)

    diamonds = await db_service.get_user_diamonds(callback.from_user.id)
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text=f"{t.BUFF_ARMOR_NAME} ({t.BUFF_ARMOR_PRICE} 💎)", callback_data="buy_armor"))
    kb.row(types.InlineKeyboardButton(text=f"{t.BUFF_DETECTOR_NAME} ({t.BUFF_DETECTOR_PRICE} 💎)", callback_data="buy_detector"))
    kb.row(types.InlineKeyboardButton(text=f"{t.BUFF_INTERCEPT_NAME} ({t.BUFF_INTERCEPT_PRICE} 💎)", callback_data="buy_intercept"))
    kb.row(types.InlineKeyboardButton(text=f"{t.BUFF_REMAP_NAME} ({t.BUFF_REMAP_PRICE} 💎)", callback_data="buy_remap"))
    kb.row(types.InlineKeyboardButton(text=f"{t.BUFF_TARGETED_REMAP_NAME} ({t.BUFF_TARGETED_REMAP_PRICE} 💎)", callback_data="buy_targeted_remap"))
    kb.row(types.InlineKeyboardButton(text=t.REVEAL_BUFF_NAME, callback_data="buff_reveal"))
    
    kb.row(types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="game_refresh"))

    text = (
        f"{t.SHOP_TITLE}\n"
        f"{t.SHOP_BALANCE.format(balance=diamonds)}\n\n"
        f"🛡 <b>{t.BUFF_ARMOR_NAME}</b>: {t.BUFF_ARMOR_DESC}\n"
        f"📡 <b>{t.BUFF_DETECTOR_NAME}</b>: {t.BUFF_DETECTOR_DESC}\n"
        f"⚡ <b>{t.BUFF_INTERCEPT_NAME}</b>: {t.BUFF_INTERCEPT_DESC}\n"
        f"🗺 <b>{t.BUFF_REMAP_NAME}</b>: {t.BUFF_REMAP_DESC}\n"
        f"🎯 <b>{t.BUFF_TARGETED_REMAP_NAME}</b>: {t.BUFF_TARGETED_REMAP_DESC}"
    )
    
    await callback.message.edit_caption(caption=text, reply_markup=kb.as_markup())

@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_buff_handler(callback: types.CallbackQuery, bot: Bot):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game or game.status != "in_progress":
        return

    t = get_text(game.language)
    buff_type = callback.data.replace("buy_", "")
    
    # Identify team
    team = None
    for t_color, uid in game.spymasters.items():
        if uid == callback.from_user.id:
            team = t_color
            break
    if not team:
        return

    # Map prices
    prices = {
        "armor": t.BUFF_ARMOR_PRICE,
        "detector": t.BUFF_DETECTOR_PRICE,
        "intercept": t.BUFF_INTERCEPT_PRICE,
        "remap": t.BUFF_REMAP_PRICE,
        "targeted_remap": t.BUFF_TARGETED_REMAP_PRICE
    }
    price = prices.get(buff_type, 999)

    # Transaction
    success = await db_service.update_user_diamonds(callback.from_user.id, -price)
    if not success:
        return await callback.answer(t.BUY_FAIL, show_alert=True)

    # Apply effect
    if buff_type == "armor":
        game.engine.team_armor.append(team)
        await callback.answer(t.BUY_SUCCESS)
    elif buff_type == "detector":
        word = game.engine.use_buff_detector()
        if word:
            await callback.answer(f"{t.BUY_SUCCESS}\n{t.REVEAL_BUFF_RESULT.format(word=word)}", show_alert=True)
        else:
            await db_service.update_user_diamonds(callback.from_user.id, price) # Refund
            return await callback.answer(t.NO_REVEAL_WORDS, show_alert=True)
    elif buff_type == "intercept":
        game.engine.team_interception.append(team)
        await callback.answer(t.BUY_SUCCESS)
    elif buff_type == "remap":
        # Get random unrevealed word index
        unrevealed = [i for i, c in enumerate(game.engine.board) if not c.is_revealed]
        if unrevealed:
            idx = random.choice(unrevealed)
            # Get a new word from repo
            repo = WordRepository()
            words = repo.get_set(game.language, game.word_set)
            # Filter out existing words
            existing = [c.word for c in game.engine.board]
            available = [w for w in words if w not in existing]
            new_word = random.choice(available) if available else "???"
            game.engine.use_buff_remap(idx, new_word)
            await callback.answer(t.BUY_SUCCESS)
        else:
            await db_service.update_user_diamonds(callback.from_user.id, price) # Refund
            return await callback.answer(t.NO_REVEAL_WORDS, show_alert=True)
    elif buff_type == "targeted_remap":
        game.metadata["pending_remap_user"] = callback.from_user.id
        await callback.answer(t.BUY_SUCCESS)
        # Update text to show instruction
        await callback.message.edit_caption(caption=t.SELECT_TARGETED_REMAP, reply_markup=await get_game_keyboard(game))
        return

    await update_main_board(callback.message, game, bot)

@router.callback_query(lambda c: c.data == "buff_reveal")
async def buff_reveal_handler(callback: types.CallbackQuery, bot: Bot):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game or game.status != "in_progress":
        return

    t = get_text(game.language)
    used_buffs = game.metadata.setdefault("used_buffs", [])

    # Find team
    team = None
    for t_color, uid in game.spymasters.items():
        if uid == callback.from_user.id:
            team = t_color
            break

    if not team:
        return

    # Let's make "Recon" a simple free daily buff or just a cheap 50 gems one
    # For now keep it as it was but maybe with gems?
    # User didn't specify price for Recon, let's keep it 50 gems or keep legacy logic
    team_buff_key = f"{team}_reveal"
    if team_buff_key in used_buffs:
        return await callback.answer(t.BUFF_USED_ERROR, show_alert=True)

    word = game.engine.use_buff_reveal()
    if word:
        used_buffs.append(team_buff_key)
        await callback.answer(t.REVEAL_BUFF_RESULT.format(word=word), show_alert=True)
        await update_main_board(callback.message, game, bot)
    else:
        await callback.answer(t.NO_REVEAL_WORDS)

def _get_player_name(player: GamePlayer, user_id: int):
    # Fallback for dots or empty names
    name = player.full_name if player and len(player.full_name.strip()) > 1 else None
    if not name and player and player.username:
        name = f"@{player.username}"
    if not name:
        name = f"Гравець {user_id}"
    return name

def _get_turn_mention(game: CodeNamesGame, t):
    current_team = game.engine.current_turn
    current_spy_id = game.spymasters.get(current_team)
    is_spymaster_turn = not bool(game.engine.clue)
    
    if is_spymaster_turn:
        player = game.players.get(current_spy_id)
        name = _get_player_name(player, current_spy_id)
        mention = f'<a href="tg://user?id={current_spy_id}">{name}</a>'
    else:
        if game.metadata.get("mode") == "Duet":
            target_team = Team.BLUE if current_team == Team.RED else Team.RED
            target_id = game.spymasters.get(target_team)
            player = game.players.get(target_id)
            name = _get_player_name(player, target_id)
            mention = f'<a href="tg://user?id={target_id}">{name}</a>'
        else:
            team_name = t.TEAM_RED_GEN if current_team == Team.RED else t.TEAM_BLUE_GEN
            # Add prefix "Team" for better flow: "Команда ЧЕРВОНИХ, ваш хід!"
            mention = f"👥 {t.TEAM_SIMPLE} {team_name}"
    return mention

async def announce_turn(chat_id: int, game: CodeNamesGame, bot: Bot):
    async with game.turn_lock:
        t = get_text(game.language)
        mention = _get_turn_mention(game, t)
        
        # Delete previous announcement if exists
        if game.last_turn_msg_id:
            try:
                await bot.delete_message(chat_id, game.last_turn_msg_id)
            except Exception:
                pass
            game.last_turn_msg_id = None

        is_spymaster_turn = not bool(game.engine.clue)
        icon = "🔍" if is_spymaster_turn else "🕵️"
        
        # Use full minutes for the first announcement
        time_str = f"{game.turn_timer // 60}м"
        
        text = t.TURN_NOTIFICATION.format(
            icon=icon,
            mention=mention,
            time=time_str
        )
        
        if not is_spymaster_turn and game.engine.clue:
            text += f"\n\n💡 <b>{game.engine.clue.upper()}</b>"

        sent_msg = None
        try:
            # Try to reply to the board if possible
            reply_id = game.board_msg_id
            sent_msg = await bot.send_message(
                chat_id,
                text,
                reply_to_message_id=reply_id,
                message_thread_id=game.thread_id,
                parse_mode="HTML"
            )
        except Exception:
            # Fallback to plain message
            sent_msg = await bot.send_message(
                chat_id,
                text,
                message_thread_id=game.thread_id,
                parse_mode="HTML"
            )

        if sent_msg:
            game.last_turn_msg_id = sent_msg.message_id

async def update_turn_notification(chat_id: int, game: CodeNamesGame, bot: Bot, remaining: int):
    async with game.turn_lock:
        if not game.last_turn_msg_id:
            return
            
        t = get_text(game.language)
        mention = _get_turn_mention(game, t)
        
        if remaining >= 60:
            time_str = f"{remaining // 60}м" if remaining % 60 == 0 else f"{remaining} {t.SECONDS}"
        else:
            time_str = f"{remaining} {t.SECONDS}"
            
        is_spymaster_turn = not bool(game.engine.clue)
        icon = "🔍" if is_spymaster_turn else "🕵️"

        text = t.TURN_NOTIFICATION.format(
            icon=icon,
            mention=mention,
            time=time_str
        )
        
        if not is_spymaster_turn and game.engine.clue:
            text += f"\n\n💡 <b>{game.engine.clue.upper()}</b>"
        
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=game.last_turn_msg_id,
                text=text,
                parse_mode="HTML"
            )
        except Exception:
            # Message might be deleted or content is same
            pass
