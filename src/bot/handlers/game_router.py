import logging
import asyncio
from typing import Optional, Any
from aiogram import Router, types, Bot, F
from aiogram.types import (
    BufferedInputFile,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame
from src.games.codenames.engine import CardColor, Team
from src.assets.texts import get_text, b
from src.core.database.service import db_service
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router()

def get_cn_game(chat_id: int) -> Optional[CodeNamesGame]:
    """Typed wrapper around manager.get_game() for Pyright."""
    game = manager.get_game(chat_id)
    if isinstance(game, CodeNamesGame):
        return game
    return None

def find_game_for_user(user_id: int) -> Optional[CodeNamesGame]:
    """Find an active CodeNames game where the given user is a spymaster."""
    for game in manager.sessions.values():
        if isinstance(game, CodeNamesGame) and game.status == "in_progress":
            if user_id in game.spymasters.values():
                return game
    return None

def _is_clue_too_similar(clue: str, board_words: list[str]) -> list[str]:
    """Check if clue is too similar to any board word (cognate/root match)."""
    clue_lower = clue.lower().strip()
    similar = []
    for bw in board_words:
        bw_lower = bw.lower().strip()
        # Exact match
        if clue_lower == bw_lower:
            similar.append(bw)
            continue
        # Substring containment (one inside the other)
        if len(clue_lower) >= 3 and len(bw_lower) >= 3:
            if clue_lower in bw_lower or bw_lower in clue_lower:
                similar.append(bw)
                continue
        # Shared prefix >= 4 characters
        prefix_len = 0
        for a, b in zip(clue_lower, bw_lower):
            if a == b:
                prefix_len += 1
            else:
                break
        if prefix_len >= 4 and prefix_len >= min(len(clue_lower), len(bw_lower)) * 0.6:
            similar.append(bw)
            continue
        # Simple edit distance check (Levenshtein <= 2 for words of len >= 4)
        if len(clue_lower) >= 4 and len(bw_lower) >= 4 and abs(len(clue_lower) - len(bw_lower)) <= 2:
            dist = 0
            for a, b in zip(clue_lower, bw_lower):
                if a != b:
                    dist += 1
            dist += abs(len(clue_lower) - len(bw_lower))
            if dist <= 2 and dist > 0:
                similar.append(bw)
                continue
    return similar

def get_past_clues_html(game: CodeNamesGame) -> str:
    if not game.metadata.get("show_past_clues", True) or not game.engine or not game.engine.clues_history:
        return ""
    # Group clues by team
    green_clues = []
    red_clues = []
    for item in game.engine.clues_history:
        display_count = item.get('display', str(item['count']))
        formatted = f"{item['clue'].upper()} ({display_count})"
        if item["team"] == "green":
            green_clues.append(formatted)
        else:
            red_clues.append(formatted)
    parts = []
    if green_clues:
        parts.append(f"🟢 {', '.join(green_clues)}")
    if red_clues:
        parts.append(f"🔴 {', '.join(red_clues)}")
    history_str = " | ".join(parts)
    t = get_text(game.language)
    return f"<blockquote>{t.PAST_CLUES_LABEL.format(history=history_str)}</blockquote>"

async def get_game_keyboard(game: CodeNamesGame, bot: Bot):
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
                    # Apply unicode long solidus (slash) overlay instead of strikethrough to prevent underline rendering
                    text = "".join(c + "\u0338" for c in card["word"])
                    style = None

                    if game.engine.mode == "duet":
                        if color_val == CardColor.GREEN.value:
                            style = "success"
                        elif color_val == CardColor.ASSASSIN.value:
                            style = "secondary"
                    else:
                        if color_val == CardColor.GREEN.value:
                            style = "success"
                        elif color_val == CardColor.RED.value:
                            style = "danger"
                        elif color_val == CardColor.ASSASSIN.value:
                            style = "secondary"

                    row.append(
                        types.InlineKeyboardButton(
                            text=text,
                            callback_data=f"reveal_{j}",
                            style=style,
                        )
                    )
                else:
                    row.append(
                        types.InlineKeyboardButton(
                            text=card["word"], callback_data=f"reveal_{j}"
                        )
                    )
            buttons.append(row)

    # Hint / Choose Word Logic
    if not game.engine.clue:
        buttons.append(
            [
                types.InlineKeyboardButton(
                    text=t.GIVE_HINT_BTN,
                    switch_inline_query_current_chat="hint ",
                )
            ]
        )
    else:
        if not game.button_board:
            buttons.append(
                [
                    types.InlineKeyboardButton(
                        text=t.CHOOSE_WORD_BTN,
                        switch_inline_query_current_chat="reveal",
                    )
                ]
            )

    buttons.append(
        [
            types.InlineKeyboardButton(
                text=t.GOTO_BOT_CARD_BTN, url=f"https://t.me/{bot.username}"
            )
        ]
    )
    if game.metadata.get("spymaster_sheet"):
        buttons.append(
            [
                types.InlineKeyboardButton(
                    text=t.SPYMASTER_SHEET_BTN,
                    callback_data="spymaster_sheet_alert"
                )
            ]
        )
    
    # Check if pass is allowed in settings
    chat_settings = await db_service.get_chat_settings(game.chat_id)
    allow_pass = game.metadata.get("allow_pass", chat_settings.allow_pass)
    
    if allow_pass:
        buttons.append(
            [types.InlineKeyboardButton(text=t.PASS_BTN, callback_data="board_pass")]
        )

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

async def update_main_board(message: types.Message, game: CodeNamesGame, bot: Bot, update_pm: bool = True):
    caption = game.get_status_message()
    is_over = game.engine.is_over if game.engine else False

    kb = await get_game_keyboard(game, bot) if not is_over else None
    board_img = await game.get_board_image(spymaster_view=is_over)
    
    # Try auto-bot hint after board update
    if not is_over and game.engine:
        await game.try_auto_bot_hint(bot)

    tasks = []

    # Task 1: Update main board
    async def update_group_board():
        board_id = getattr(game, 'board_msg_id', None) or game.metadata.get('board_msg_id')
        if not board_id:
            return
        try:
            board_img.seek(0)
            await bot.edit_message_media(
                chat_id=game.chat_id,
                message_id=board_id,
                media=types.InputMediaPhoto(
                    media=BufferedInputFile(board_img.read(), filename="board.png"),
                    caption=caption,
                    parse_mode="HTML",
                ),
                reply_markup=kb,
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                logger.error(f"Board update failed: {e}")

    # Await main board update immediately to make the chat feel snappy
    await update_group_board()

    if update_pm:
        # Update spymasters' views in PM asynchronously in background tasks
        t = get_text(game.language)
        updated_sms = set()
        for team, sm_id in game.spymasters.items():
            if sm_id and sm_id not in updated_sms:
                updated_sms.add(sm_id)
                msg_id = game.metadata.get(f"sm_msg_id_{sm_id}")
                if msg_id:
                    side = (
                        "a"
                        if team == Team.GREEN
                        else "b"
                        if game.engine.mode == "duet"
                        else None
                    )
                    
                    async def update_sm_pm(s_id=sm_id, m_id=msg_id, s_side=side, s_team=team):
                        try:
                            # In classic modes, the spymaster view is identical for all spymasters.
                            # So we can reuse the same image!
                            if game.engine.mode != "duet":
                                # We can generate the spymaster view once and share it
                                if not hasattr(update_main_board, "_cached_sm_img"):
                                    setattr(update_main_board, "_cached_sm_img", await game.get_board_image(spymaster_view=True))
                                sm_img = getattr(update_main_board, "_cached_sm_img")
                            else:
                                sm_img = await game.get_board_image(spymaster_view=True, side=s_side)
                            
                            chat_id_str = str(game.chat_id)
                            board_id = getattr(game, 'board_msg_id', None) or game.metadata.get('board_msg_id')
                            builder = InlineKeyboardBuilder()
                            if chat_id_str.startswith("-100") and board_id:
                                link = f"https://t.me/c/{chat_id_str[4:]}/{board_id}"
                                builder.row(types.InlineKeyboardButton(text=t.GOTO_GROUP_MAP_BTN, url=link))
                            builder.row(types.InlineKeyboardButton(
                                text=t.GIVE_HINT_BTN,
                                switch_inline_query_current_chat="hint "
                            ))
                            kb_sm = builder.as_markup()

                            if game.engine.mode == "duet":
                                role_msg = t.DUET_ROLE_DESC
                            elif game.engine.mode == "3p":
                                current_team_str = "🟢 Зелених" if game.engine.current_turn == Team.GREEN else "🔴 Червоних"
                                if game.language == "en":
                                    current_team_str = "🟢 Green" if game.engine.current_turn == Team.GREEN else "🔴 Red"
                                if game.engine.clue:
                                    role_msg = t.SPYMASTER_DUAL_ROLE + f"\n\n⏳ Зараз відгадують: {current_team_str}" if game.language == "uk" else f"\n\n⏳ Now guessing: {current_team_str}"
                                else:
                                    role_msg = t.SPYMASTER_DUAL_ROLE + f"\n\n🎯 Зараз дайте підказку для: <b>{current_team_str}</b>" if game.language == "uk" else f"\n\n🎯 Now give a clue for: <b>{current_team_str}</b>"
                            else:
                                role_msg = t.SPYMASTER_ROLE.format(
                                    team=t.TEAM_GREEN if s_team == Team.GREEN else t.TEAM_RED
                                )

                            sm_img.seek(0)
                            await bot.edit_message_media(
                                chat_id=s_id,
                                message_id=m_id,
                                media=types.InputMediaPhoto(
                                    media=BufferedInputFile(sm_img.read(), filename="board.png"),
                                    caption=f"{role_msg}\n\n{t.SPYMASTER_INSTRUCTIONS}",
                                    parse_mode="HTML"
                                ),
                                reply_markup=kb_sm
                            )
                        except Exception as e:
                            if "message is not modified" not in str(e):
                                logger.error(f"Failed to update PM board for spymaster {s_id}: {e}")

                    # Run PM updates in background tasks so they do not block main group chat flow
                    asyncio.create_task(update_sm_pm())

    # Clear SM cached image helper if defined on the function
    if hasattr(update_main_board, "_cached_sm_img"):
        delattr(update_main_board, "_cached_sm_img")

@router.callback_query(lambda c: c.data == "game_start")
async def start_game(callback: types.CallbackQuery, bot: Bot, settings):
    game = get_cn_game(callback.message.chat.id)
    if not game:
        return await callback.answer(get_text().GAME_NOT_FOUND_ALERT)

    if game.status == "in_progress":
        return await callback.answer() # already started, ignore double click

    if game.metadata.get("_starting"):
        return await callback.answer() # already starting in another task

    game.metadata["_starting"] = True
    manager.save_game(game.chat_id)

    t = get_text(game.language)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    game.dark_mode = chat_settings.dark_mode
    game.button_board = chat_settings.button_board
    game.board_size = chat_settings.board_size
    game.metadata["spymaster_sheet"] = chat_settings.spymaster_sheet
    game.metadata["show_past_clues"] = chat_settings.show_past_clues
    game.metadata["strict_clues"] = chat_settings.strict_clues
    game.metadata["allow_pass"] = chat_settings.allow_pass

    # Save finalized settings to DB for future games
    chat_settings.language = game.language
    chat_settings.last_word_set = game.word_set
    chat_settings.last_reg_timer = game.reg_timer
    chat_settings.last_turn_timer = game.turn_timer
    chat_settings.last_mode = game.metadata.get("mode", "classic")
    chat_settings.board_size = game.board_size
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    if not chat_settings.allow_everyone_start and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            game.metadata.pop("_starting", None)
            manager.save_game(game.chat_id)
            return await callback.answer(t.ADMIN_ONLY_ERROR, show_alert=True)

    # Allow single player if auto-bot is enabled (auto-bot acts as spymaster)
    if len(game.players) < 2 and not game.metadata.get("auto_bot_enabled", False):
        game.metadata.pop("_starting", None)
        manager.save_game(game.chat_id)
        return await callback.answer(t.MIN_PLAYERS, show_alert=True)

    try:
        start_msg = await game.start()
    except Exception as e:
        game.metadata.pop("_starting", None)
        manager.save_game(game.chat_id)
        logger.error(f"Error starting game: {e}")
        return await callback.answer("Помилка під час запуску гри.", show_alert=True)
    board_img = await game.get_board_image(spymaster_view=False)
    kb = await get_game_keyboard(game, bot)

    # Delete redundant join messages for all players
    for player in game.players.values():
        if getattr(player, 'join_msg_id', None):
            try:
                await bot.delete_message(player.user_id, player.join_msg_id)
            except:
                pass

    # Unpin and delete the registration/lobby message
    reg_msg_id = game.metadata.get("registration_msg_id")
    if reg_msg_id:
        try:
            await bot.unpin_chat_message(chat_id=game.chat_id, message_id=reg_msg_id)
        except Exception:
            pass
        try:
            await bot.delete_message(chat_id=game.chat_id, message_id=reg_msg_id)
        except Exception:
            pass

    sent_board = await bot.send_photo(
        callback.message.chat.id,
        photo=BufferedInputFile(board_img.read(), filename="board.png"),
        caption=start_msg,
        reply_markup=kb,
        message_thread_id=game.thread_id,
    )
    game.board_msg_id = sent_board.message_id
    # Persist board_msg_id to Redis immediately so restart doesn't break link/updates
    manager.save_game(game.chat_id)

    # Trigger auto-bot hint immediately after game start if auto-bot is enabled
    if game.metadata.get("auto_bot_enabled", False) and game.engine:
        await game.try_auto_bot_hint(bot)

    if chat_settings.pin_message:
        try:
            await bot.pin_chat_message(
                callback.message.chat.id,
                sent_board.message_id,
                disable_notification=True
            )
            try:
                await bot.delete_message(callback.message.chat.id, sent_board.message_id + 1)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to pin board message: {e}")

    if game.engine.mode == "3p":
        # In 3P mode, there is one shared spymaster
        sm_id = game.spymasters[Team.GREEN]
        sm_img = await game.get_board_image(spymaster_view=True)
        role_msg = t.SPYMASTER_DUAL_ROLE
        
        try:
            chat_id_str = str(game.chat_id)
            builder = InlineKeyboardBuilder()
            if chat_id_str.startswith("-100") and game.board_msg_id:
                link = f"https://t.me/c/{chat_id_str[4:]}/{game.board_msg_id}"
                builder.row(types.InlineKeyboardButton(text=t.GOTO_GROUP_MAP_BTN, url=link))
            builder.row(types.InlineKeyboardButton(
                text=t.GIVE_HINT_BTN,
                switch_inline_query_current_chat="hint "
            ))
            kb_sm = builder.as_markup()
            
            sent_sm = await bot.send_photo(
                sm_id,
                photo=BufferedInputFile(sm_img.read(), filename="board.png"),
                caption=f"{role_msg}\n\n{t.SPYMASTER_INSTRUCTIONS}",
                reply_markup=kb_sm
            )
            game.metadata[f"sm_msg_id_{sm_id}"] = sent_sm.message_id
        except Exception as e:
            logger.error(f"Failed to send DM to 3p spymaster {sm_id}: {e}")
            await bot.send_message(
                game.chat_id,
                t.SPYMASTER_DM_ERROR.format(mention=game.players[sm_id].mention),
                message_thread_id=game.thread_id,
            )
    else:
        for team, sm_id in game.spymasters.items():
            if sm_id:
                side = (
                    "a"
                    if team == Team.GREEN
                    else "b"
                    if game.engine.mode == "duet"
                    else None
                )
                sm_img = await game.get_board_image(spymaster_view=True, side=side)
                if game.engine.mode == "duet":
                    role_msg = t.DUET_ROLE_DESC
                else:
                    role_msg = t.SPYMASTER_ROLE.format(
                        team=t.TEAM_GREEN if team == Team.GREEN else t.TEAM_RED
                    )
                try:
                    chat_id_str = str(game.chat_id)
                    builder = InlineKeyboardBuilder()
                    if chat_id_str.startswith("-100") and game.board_msg_id:
                        link = f"https://t.me/c/{chat_id_str[4:]}/{game.board_msg_id}"
                        builder.row(types.InlineKeyboardButton(text=t.GOTO_GROUP_MAP_BTN, url=link))
                    builder.row(types.InlineKeyboardButton(
                        text=t.GIVE_HINT_BTN,
                        switch_inline_query_current_chat="hint "
                    ))
                    kb_sm = builder.as_markup()
    
                    sent_sm = await bot.send_photo(
                        sm_id,
                        photo=BufferedInputFile(sm_img.read(), filename="board.png"),
                        caption=f"{role_msg}\n\n{t.SPYMASTER_INSTRUCTIONS}",
                        reply_markup=kb_sm,
                    )
                    game.metadata[f"sm_msg_id_{sm_id}"] = sent_sm.message_id
                except Exception as e:
                    logger.error(f"Failed to send DM to spymaster {sm_id}: {e}")
                    await bot.send_message(
                        game.chat_id,
                        t.SPYMASTER_DM_ERROR.format(
                            mention=game.players[sm_id].mention
                        ),
                        message_thread_id=game.thread_id,
                    )

async def trigger_game_over(chat_id: int, bot: Bot, game: CodeNamesGame, message: types.Message, custom_msg_text: str = None, chat_title: str = None):
    import datetime
    t = get_text(game.language)
    if game.metadata.get("_ending"):
        manager.save_game(game.chat_id)
        return
    game.metadata["_ending"] = True
    winner_text = t.WIN_GREEN if game.engine.winner == Team.GREEN else t.WIN_RED
    if game.engine.mode == "duet":
        winner_text = t.WIN_DUET if game.engine.winner else t.LOSE_DUET

    # Credit Coins to Winners
    rewards_summary = []
    
    # Save chat title for leaderboard
    if chat_title:
        await db_service.ensure_chat(game.chat_id, chat_title)
    if "points" not in game.metadata:
        game.metadata["points"] = {}
        
    winning_team = game.engine.winner
    for pid, p in game.players.items():
        p_points = game.metadata["points"].get(pid, 0)
        is_winner = False
        if game.engine.mode == "duet":
            is_winner = bool(game.engine.winner) # True if they successfully won Duet
        else:
            if p.team and winning_team:
                is_winner = (p.team == winning_team.value)
        
        # Fetch stats tracked during game
        p_stats = game.metadata.get("stats", {}).get(pid, {
            "guessed_words": 0,
            "assassins_hit": 0,
            "opponent_words_hit": 0
        })
        
        # Save game outcome and update user statistics
        mode_val = game.engine.mode
        hardcore_mode = game.metadata.get("hardcore_mode", "off")
        hc_suffix = {"hard": "_hardcore", "light": "_light_hardcore", "roulette": "_roulette_hardcore"}.get(hardcore_mode, "")
        mode_val = f"{mode_val}{hc_suffix}"

        player_result = "win" if is_winner else "loss"

        await db_service.save_game_result(
            user_id=pid,
            full_name=p.full_name,
            username=p.username or "",
            game_type="codenames",
            result=player_result,
            guessed_words=p_stats["guessed_words"],
            assassins_hit=p_stats["assassins_hit"],
            opponent_words_hit=p_stats["opponent_words_hit"],
            mode=mode_val,
            chat_id=game.chat_id
        )
        
        # Team emoji — captains get 👨‍✈️ instead of team color
        if p.role in ("spymaster", "dual_spymaster"):
            team_emoji = "👨‍✈️"
        else:
            if game.engine.mode == "duet":
                team_emoji = "🅰️" if p.team == "green" else "🅱️" if p.team == "red" else "👤"
            else:
                team_emoji = "🟢" if p.team == "green" else "🔴" if p.team == "red" else "👤"
        player_display = f"{team_emoji} {p.mention}"
        
        if is_winner:
            # Переможець без особистих очок не отримує монет (нічого не робив)
            if p_points > 0:
                coins_earned = 5 + max(0, p_points) * 2
                await db_service.update_user_coins(pid, coins_earned)
                rewards_summary.append(t.SCORE_REWARDS_PLAYER.format(name=player_display, points=p_points, coins=coins_earned))
            else:
                rewards_summary.append(
                    f"{player_display}: {p_points} " + b(game.language, "очок", "points")
                )
        else:
            # Той, хто програв, отримує монетки якщо вгадав хоч слово АБО якщо має очки (капітан)
            if p_points > 0 or p_stats.get("guessed_words", 0) > 0:
                coins_earned = max(0, 2 + max(0, p_points))
                await db_service.update_user_coins(pid, coins_earned)
                rewards_summary.append(
                    f"{player_display}: {p_points} " + b(game.language, "очок", "points") +
                    f" (🪙 +{coins_earned})"
                )
            else:
                rewards_summary.append(
                    f"{player_display}: {p_points} " + b(game.language, "очок", "points")
                )

    rewards_str = "\n".join(rewards_summary)
    
    # Send reveal result first (as a separate message)
    if custom_msg_text:
        await bot.send_message(
            game.chat_id,
            custom_msg_text,
            message_thread_id=game.thread_id,
            parse_mode="HTML"
        )
    
    # Update the main board to spymaster view
    await update_main_board(message, game, bot, update_pm=False)
    
    # Send the fully-revealed board image as a photo with final scores + game duration
    final_board_img = await game.get_board_image(spymaster_view=True)
    duration_str = ""
    if getattr(game, 'game_start_time', None):
        elapsed_seconds = int((datetime.datetime.now().timestamp() - game.game_start_time.timestamp()))
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        if hours > 0:
            duration_str = t.GAME_STATS.format(duration=f"{hours}:{minutes:02d}:{seconds:02d}", found=sum(1 for c in game.engine.board if c.is_revealed) if game.engine else "?", total=len(game.engine.board) if game.engine else "?")
        else:
            duration_str = t.GAME_STATS.format(duration=f"{minutes}:{seconds:02d}", found=sum(1 for c in game.engine.board if c.is_revealed) if game.engine else "?", total=len(game.engine.board) if game.engine else "?")

    await bot.send_photo(
        game.chat_id,
        photo=BufferedInputFile(final_board_img.read(), filename="final_board.png"),
        caption=(
            f"{t.GAME_ENDED_TITLE.format(winner=winner_text)}\n"
            f"{duration_str}\n\n"
            f"{t.SCORE_REWARDS_TITLE}\n{rewards_str}"
        ),
        message_thread_id=game.thread_id,
        parse_mode="HTML"
    )
    manager.end_game(game.chat_id)


@router.callback_query(lambda c: c.data.startswith("reveal_"))
async def handle_reveal(callback: types.CallbackQuery, bot: Bot):
    game = get_cn_game(callback.message.chat.id)
    if not game or game.status != "in_progress":
        return await callback.answer()

    # Guard: if the game already ended (e.g. another reveal was processed first),
    # silently ignore this late callback to avoid sending duplicate game-over messages.
    if game.engine and game.engine.is_over:
        return await callback.answer()

    # Prevent duplicate game-over processing from rapid clicks
    if game.metadata.get("_ending"):
        return await callback.answer()

    t = get_text(game.language)
    idx = int(callback.data.replace("reveal_", ""))

    # Permission logic
    player = game.players.get(callback.from_user.id)
    if not player:
        return await callback.answer(t.NOT_A_PLAYER, show_alert=True)

    current_team = game.engine.current_turn

    # Robust duet check: engine mode OR metadata mode
    is_duet = game.engine.mode == "duet" or game.metadata.get("mode", "").lower() == "duet"
    if is_duet:
        current_spymaster_id = game.spymasters.get(current_team)

        # Determine which TEAM should be GUESSING
        # In Duet, if Green spymaster gives clue, Red team guesses, and vice versa
        guessing_team_val = "red" if current_team == Team.GREEN else "green"

        # If player belongs to the team that should give clue (or is the spymaster himself)
        if player.team != guessing_team_val:
            return await callback.answer(t.DUET_TURN_GIVER_WAIT, show_alert=True)

        # Check if clue was already created by opposite team's spymaster
        if not game.engine.clue:
            return await callback.answer(t.DUET_TURN_GIVER_HINT_WAIT, show_alert=True)
    else:
        if player.role == "spymaster" or player.role == "dual_spymaster":
            return await callback.answer(t.SPYMASTER_GUESS_ERROR, show_alert=True)
        if player.team != current_team.value:
            return await callback.answer(t.NOT_YOUR_TURN, show_alert=True)

    if not game.engine.clue:
        return await callback.answer(t.SPYMASTER_WAIT, show_alert=True)

    turn_before = game.engine.current_turn
    card_word = game.engine.get_board_state(revealed_only=False)[idx]["word"]

    # Default color_name and armor_saved to prevent UnboundLocalError if reveal_card returns False
    color_name = b(game.language, "⚪ Нейтральне", "⚪ Neutral")
    armor_saved = False

    if game.engine.reveal_card(idx):
        # Update spymaster queue for Duet if turn changed
        if game.engine.mode == "duet" and game.engine.current_turn != turn_before:
            game.update_duet_spymaster_queue(previous_turn=turn_before)

        await update_main_board(callback.message, game, bot)

        # Check if armor buff saved the team from assassin
        armor_saved = False
        if game.engine.is_armor_triggered:
            game.engine.is_armor_triggered = False  # Reset for next use
            armor_saved = True

        # Send guess result notification
        color_val = game.engine.board[idx].revealed_color
        
        # Calculate points
        is_correct = False
        if game.engine.mode == "duet":
            is_correct = (color_val == CardColor.GREEN)
        else:
            is_correct = (color_val.value == current_team.value)
            
        spymaster_id = game.spymasters.get(current_team)
        operative_id = callback.from_user.id
        
        if "points" not in game.metadata:
            game.metadata["points"] = {}
            
        if operative_id not in game.metadata["points"]:
            game.metadata["points"][operative_id] = 0
        if spymaster_id and spymaster_id not in game.metadata["points"]:
            game.metadata["points"][spymaster_id] = 0
            
        if is_correct:
            game.metadata["points"][operative_id] += 1
            if spymaster_id:
                game.metadata["points"][spymaster_id] += 1
        else:
            game.metadata["points"][operative_id] -= 1
            if spymaster_id:
                game.metadata["points"][spymaster_id] -= 1

        if "stats" not in game.metadata:
            game.metadata["stats"] = {}
        if operative_id not in game.metadata["stats"]:
            game.metadata["stats"][operative_id] = {
                "guessed_words": 0,
                "assassins_hit": 0,
                "opponent_words_hit": 0
            }

        if color_val == CardColor.ASSASSIN:
            game.metadata["stats"][operative_id]["assassins_hit"] += 1
        elif color_val != CardColor.BYSTANDER:
            if game.engine.mode == "duet":
                if color_val == CardColor.GREEN:
                    game.metadata["stats"][operative_id]["guessed_words"] += 1
            else:
                if (player.team == "green" and color_val == CardColor.GREEN) or (player.team == "red" and color_val == CardColor.RED):
                    game.metadata["stats"][operative_id]["guessed_words"] += 1
                else:
                    game.metadata["stats"][operative_id]["opponent_words_hit"] += 1

        if game.engine.mode == "duet":
            if color_val == CardColor.GREEN:
                color_name = b(game.language, "🟢 Агент (Зелене)", "🟢 Agent (Green)")
            elif color_val == CardColor.ASSASSIN:
                color_name = b(game.language, "💀 Вбивця", "💀 Assassin")
            else:
                color_name = b(game.language, "⚪ Нейтральне", "⚪ Neutral")
        else:
            if color_val == CardColor.GREEN:
                color_name = b(game.language, "🟢 Зелена команда", "🟢 Green Team")
            elif color_val == CardColor.RED:
                color_name = b(game.language, "🔴 Червона команда", "🔴 Red Team")
            elif color_val == CardColor.ASSASSIN:
                color_name = b(game.language, "💀 Вбивця", "💀 Assassin")
            else:
                color_name = b(game.language, "⚪ Нейтральне", "⚪ Neutral")

    msg_text = t.REVEAL_RESULT_MSG.format(name=player.full_name, word=card_word.upper(), color=color_name)
    # If armor saved the team from assassin, append the notification
    if armor_saved:
        if game.language == "uk":
            msg_text += "\n\n🛡️ <b>Бронежилет врятував ваше життя!</b> Гра триває!"
        else:
            msg_text += "\n\n🛡️ <b>Armor saved your life!</b> The game continues!"
    kb = None

    if game.engine.is_over:
        try:
            await callback.answer()
        except Exception:
            pass
        chat_title = callback.message.chat.title if callback.message.chat.title else None
        await trigger_game_over(game.chat_id, bot, game, callback.message, custom_msg_text=msg_text, chat_title=chat_title)
    else:
        turn_after = game.engine.current_turn
        if turn_before != turn_after:
            btn_rows = []
            btn_rows.append(types.InlineKeyboardButton(
                text=t.GOTO_BOT_CARD_BTN, url=f"https://t.me/{bot.username}"
            ))
            btn_rows.append(types.InlineKeyboardButton(
                text=t.GIVE_HINT_BTN,
                switch_inline_query_current_chat="hint "
            ))
            kb = types.InlineKeyboardMarkup(inline_keyboard=[btn_rows])
            
            if game.engine.mode == "duet":
                giver_id = game.spymasters.get(turn_after)
                giver_mention = game.players[giver_id].mention if giver_id in game.players else b(game.language, "Напарник", "Partner")
                msg_text += "\n" + t.TURN_SWITCH_GIVER.format(name=giver_mention)
            else:
                team_name = b(game.language, "🔴 Червоних", "🔴 Red") if turn_after == Team.RED else b(game.language, "🟢 Зелених", "🟢 Green")
                # Show which spymaster should give the hint
                spymaster_id = game.spymasters.get(turn_after)
                if spymaster_id and spymaster_id in game.players:
                    sm_mention = game.players[spymaster_id].mention
                    msg_text += "\n" + t.TURN_SWITCH_TEAM.format(name=team_name)
                    msg_text += "\n" + t.TURN_SWITCH_GIVER.format(name=sm_mention)
                else:
                    msg_text += "\n" + t.TURN_SWITCH_TEAM.format(name=team_name)
            msg_text += get_past_clues_html(game)
        else:
            if not game.button_board:
                kb = types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text=t.CHOOSE_WORD_BTN, switch_inline_query_current_chat="reveal")
                ]])

        await bot.send_message(
            game.chat_id,
            msg_text,
            message_thread_id=game.thread_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

    manager.save_game(game.chat_id)
    await callback.answer()

@router.callback_query(lambda c: c.data == "board_pass")
async def handle_pass(callback: types.CallbackQuery, bot: Bot, settings):
    game = get_cn_game(callback.message.chat.id)
    if not game:
        return await callback.answer()

    t = get_text(game.language)
    player = game.players.get(callback.from_user.id)
    is_admin = False

    # Check if pass is allowed in settings
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    allow_pass = game.metadata.get("allow_pass", chat_settings.allow_pass)
    
    if not allow_pass:
        return await callback.answer(
            t.SETTING_ALLOW_PASS.split(":")[0] + " ❌",
            show_alert=True
        )
    
    if callback.from_user.id in settings.admin_ids:
        is_admin = True
    elif callback.message.chat.type in ["group", "supergroup"]:
        try:
            member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
            if member.status in ["administrator", "creator"]:
                is_admin = True
        except Exception:
            pass

    # Allow if it's their turn OR if they are an admin
    if game.engine.mode == "duet":
        guessing_team_val = "red" if game.engine.current_turn == Team.GREEN else "green"
        is_their_turn = player and player.team == guessing_team_val
    else:
        is_their_turn = player and player.team == game.engine.current_turn.value
    
    if not is_admin and not is_their_turn:
        return await callback.answer(
            get_text(game.language).NOT_YOUR_TURN, show_alert=True
        )

    # Require double-click confirmation for admin force-skip
    if is_admin and not is_their_turn:
        import time
        now = time.time()
        confirm_data = game.metadata.get("admin_pass_confirm") or {}
        
        if confirm_data.get("user_id") != callback.from_user.id or (now - confirm_data.get("time", 0) > 10):
            game.metadata["admin_pass_confirm"] = {"user_id": callback.from_user.id, "time": now}
            return await callback.answer(
                t.ADMIN_PASS_SKIP_PROMPT,
                show_alert=True
            )
        else:
            # Confirmed within 10 seconds, clear the state
            game.metadata["admin_pass_confirm"] = None

    turn_before = game.engine.current_turn
    game.engine.end_turn()
    if game.engine.mode == "duet":
        game.update_duet_spymaster_queue(previous_turn=turn_before)
    await update_main_board(callback.message, game, bot)
    
    player_name = player.full_name if player else callback.from_user.full_name
    turn_after = game.engine.current_turn
    
    if is_admin and not is_their_turn:
        msg_text = t.ADMIN_PASS_SKIP_MSG.format(name=callback.from_user.full_name)
    else:
        msg_text = t.PLAYER_PASSED_MSG.format(name=player_name)

    if game.engine.mode == "duet":
        giver_id = game.spymasters.get(turn_after)
        giver_mention = game.players[giver_id].mention if giver_id in game.players else t.ROLE_PARTNER
        msg_text += "\n" + t.TURN_SWITCH_GIVER.format(name=giver_mention)
    else:
        team_name = t.TEAM_RED_NAME if turn_after == Team.RED else t.TEAM_GREEN_NAME
        
        spymaster_id = game.spymasters.get(turn_after)
        if spymaster_id and spymaster_id in game.players:
            sm_mention = game.players[spymaster_id].mention
            msg_text += "\n" + t.TURN_SWITCH_TEAM.format(name=team_name)
        else:
            msg_text += "\n" + t.TURN_SWITCH_TEAM.format(name=team_name)

    btn_rows = []
    btn_rows.append(types.InlineKeyboardButton(
        text=t.GOTO_BOT_CARD_BTN, url=f"https://t.me/{bot.username}"
    ))
    btn_rows.append(types.InlineKeyboardButton(
        text=t.GIVE_HINT_BTN,
        switch_inline_query_current_chat="hint "
    ))
    kb = types.InlineKeyboardMarkup(inline_keyboard=[btn_rows])

    msg_text += get_past_clues_html(game)

    await bot.send_message(
        game.chat_id,
        msg_text,
        message_thread_id=game.thread_id,
        reply_markup=kb,
        parse_mode="HTML"
    )
    manager.save_game(game.chat_id)
    await callback.answer()

@router.callback_query(lambda c: c.data == "spymaster_sheet_alert")
async def handle_spymaster_sheet_alert(callback: types.CallbackQuery, bot: Bot):
    game = get_cn_game(callback.message.chat.id)
    if not game or game.status != "in_progress":
        return await callback.answer(b(game.language if game else "uk", "❌ Гра не знайдена або вже завершена", "❌ Game not found or finished"), show_alert=True)

    is_spymaster = callback.from_user.id in game.spymasters.values()
    if not is_spymaster:
        return await callback.answer(
            b(game.language, "🚫 Ця кнопка доступна тільки для Капітанів!", "🚫 This button is only available for Spymasters!"),
            show_alert=True
        )

    lines = []

    if game.engine.mode == "duet":
        side = "a" if callback.from_user.id == game.spymasters.get(Team.GREEN) else "b"
        my_agents = []
        my_assassins = []

        for i, card in enumerate(game.engine.board):
            color = game.engine.get_duet_color(i, side)
            word_str = card.word.upper()
            if card.is_revealed:
                word_str = f"~{word_str}~"
                
            if color == CardColor.GREEN:
                my_agents.append(word_str)
            elif color == CardColor.ASSASSIN:
                my_assassins.append(word_str)

        lines.append(f"💀: {', '.join(my_assassins)}")
        lines.append(f"🟢: {', '.join(my_agents)}")

    else:
        current_team_val = game.engine.current_turn.value
        other_team_val = "red" if current_team_val == "green" else "green"

        my_words = []
        opp_words = []
        assassins = []

        for card in game.engine.board:
            word_str = card.word.upper()
            if card.is_revealed:
                word_str = f"~{word_str}~"
                
            color = card.color
            if color.value == current_team_val:
                my_words.append(word_str)
            elif color.value == other_team_val:
                opp_words.append(word_str)
            elif color == CardColor.ASSASSIN:
                assassins.append(word_str)

        emoji_my = "🟢" if current_team_val == "green" else "🔴"
        emoji_opp = "🔴" if current_team_val == "green" else "🟢"

        lines.append(f"💀: {', '.join(assassins)}")
        lines.append(f"{emoji_my}: {', '.join(my_words)}")
        lines.append(f"{emoji_opp}: {', '.join(opp_words)}")

    alert_text = "\n".join(lines)
    if len(alert_text) > 200:
        alert_text = alert_text[:197] + "..."
    await callback.answer(alert_text, show_alert=True)

@router.inline_query(lambda q: q.query.startswith("hint"))
async def inline_hint(query: InlineQuery):
    # Support both "hint_<chat_id> word count" and just "hint word count"
    parts = query.query.strip().split(" ")
    first_part = parts[0]  # e.g. "hint_-100123" or "hint"
    
    chat_id = None
    if "_" in first_part:
        try:
            chat_id = int(first_part.split("_")[1])
        except ValueError:
            pass

    user_id = query.from_user.id
    game = None
    if chat_id:
        game = get_cn_game(chat_id)
    
    # If not found via chat_id, look up the game session where the user is currently a player.
    # Also support detecting active game by inspecting open sessions if there is only one active game,
    # or if the query comes from a chat that has an active game.
    # Note: query.chat_type can be "group", "supergroup" or "channel" if inline is invoked from a chat.
    if not game:
        # 1. Search by player membership
        for sess in manager.sessions.values():
            if isinstance(sess, CodeNamesGame) and user_id in sess.players:
                game = sess
                chat_id = sess.chat_id
                break
        
        # 2. If still not found, check if there's an active session in any chat (fallback if only 1 active session exists globally)
        if not game:
            active_sessions = [sess for sess in manager.sessions.values() if isinstance(sess, CodeNamesGame)]
            if len(active_sessions) == 1:
                game = active_sessions[0]
                chat_id = game.chat_id

    if not game:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id="hint_no_game",
                    title=b("uk", "Гра не знайдена або вже завершена", "Game not found or finished"),
                    description=b("uk", "Створіть нову гру за допомогою /codenames", "Create a new game with /codenames"),
                    input_message_content=InputTextMessageContent(
                        message_text=b("uk", "Гра вже завершена. Створіть нову гру за допомогою /codenames", "Game finished. Create a new game with /codenames")
                    ),
                )
            ],
            cache_time=1,
        )

    t = get_text(game.language)
    user_id = query.from_user.id

    player = game.players.get(user_id)
    if not player:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"hint_join_{chat_id}",
                    title=t.NOT_A_PLAYER,
                    description=t.NOT_A_PLAYER_DESC,
                    input_message_content=InputTextMessageContent(
                        message_text="/cn_join"
                    ),
                )
            ],
            cache_time=1,
        )

    if not game.engine:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"hint_no_engine_{chat_id}",
                    title=b(game.language, "Гра завершена", "Game ended"),
                    description=b(game.language, "Гра вже завершена", "Game already ended"),
                    input_message_content=InputTextMessageContent(
                        message_text=b(game.language, "Гра вже завершена", "Game already ended")
                    ),
                )
            ],
            cache_time=1,
        )

    is_turn = game.spymasters.get(game.engine.current_turn) == user_id
    if not is_turn:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"hint_not_turn_{chat_id}",
                    title=t.NOT_YOUR_TURN,
                    description=t.NOT_YOUR_TURN_DESC,
                    input_message_content=InputTextMessageContent(
                        message_text=b(game.language, "Я чекаю своєї черги.", "I'm waiting for my turn.")
                    ),
                )
            ],
            cache_time=1,
        )

    parts = query.query.strip().split(" ")
    if len(parts) >= 3:
        word = parts[1]
        count = parts[2]
# Перевіряємо абсолютно всі варіанти безліміту, включаючи знак нескінченності
        is_unlimited = count in ["-", "НЕОБМЕЖЕНО", "UNLIMITED", "unlim", "необ", "∞"]
        
        # Безпечна перевірка: спочатку дивимося, чи це безліміт, 
        # а якщо ні — перевіряємо, чи це звичайний рядок із цифрами
        if is_unlimited or (isinstance(count, str) and count.isdigit()):
            # Strict clue validation
            if game.metadata.get("strict_clues", False):
                board_words = [c.word for c in game.engine.board if not c.is_revealed]
                similar = _is_clue_too_similar(word, board_words)
                if similar:
                    similar_list = ", ".join(similar[:5])
                    return await query.answer(
                        [
                            InlineQueryResultArticle(
                                id=f"hint_strict_{chat_id}",
                                title=t.STRICT_CLUE_ERROR_TITLE,
                                description=t.STRICT_CLUE_ERROR_DESC.format(words=similar_list),
                                input_message_content=InputTextMessageContent(
                                    message_text=t.STRICT_CLUE_ERROR_MSG.format(word=word, words=similar_list)
                                ),
                            )
                        ],
                        cache_time=1,
                    )
            chat_id_str = str(chat_id)
            board_msg_id = getattr(game, 'board_msg_id', None) or game.metadata.get('board_msg_id')
            if chat_id_str.startswith("-100") and board_msg_id:
                link = f"https://t.me/c/{chat_id_str[4:]}/{board_msg_id}"
            else:
                link = f"https://t.me/{query.bot.username}" if query.bot else ""
            
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🗺️ До карти", url=link)]
            ]) if link else None

            # Determine turn description
            current_team = game.engine.current_turn
            guessers = []
            if game.engine.mode == "duet":
                guesser_team = Team.RED if current_team == Team.GREEN else Team.GREEN
                guesser_id = game.spymasters.get(guesser_team)
                if guesser_id in game.players:
                    guessers.append(game.players[guesser_id])
            else:
                for pid, p in game.players.items():
                    if p.team == current_team.value and p.role == "agent":
                        guessers.append(p)

            if guessers:
                guessers_formatted = []
                for p in guessers:
                    p_emoji = ("🅰️" if p.team == "green" else "🅱️") if game.engine.mode == "duet" else ("🟢" if p.team == "green" else "🔴")
                    if p.username:
                        guessers_formatted.append(f"{p_emoji} @{p.username}")
                    else:
                        guessers_formatted.append(f"{p_emoji} <b>{p.full_name}</b>")
                guesser_mentions = ", ".join(guessers_formatted)
                turn_info = t.TURN_INFO_GUESS.format(mentions=guesser_mentions)
            else:
                if game.engine.mode == "duet":
                    team_color_name = b(game.language, "🅰️ Сторони A", "🅰️ Side A") if current_team == Team.GREEN else b(game.language, "🅱️ Сторони B", "🅱️ Side B")
                else:
                    team_color_name = b(game.language, "🟢 Зелених", "🟢 Green") if current_team == Team.GREEN else b(game.language, "🔴 Червоних", "🔴 Red")
                turn_info = t.TURN_INFO_OPERATIVES.format(team=team_color_name)

# Чітко розділяємо нуль та нескінченність для виведення на екран
            if count in ["0", 0]:
                display_count = "0"
            elif count in ["-", "НЕОБМЕЖЕНО", "UNLIMITED", "unlim", "необ"]:
                display_count = "∞"
            else:
                display_count = count

            msg_text = t.HINT_ANNOUNCE.format(word=word.upper(), count=display_count, info=turn_info)

            await query.answer(
                [
                    InlineQueryResultArticle(
                        id=f"hint_{chat_id}",
                        title=t.INLINE_VALID_HINT_TITLE.format(word=word, count=display_count),
                        input_message_content=InputTextMessageContent(
                            message_text=msg_text,
                            parse_mode="HTML"
                        ),
                        reply_markup=kb,
                        callback_data=f"set_hint_{chat_id}_{word}_{count}",
                    )
                ],
                cache_time=1,
            )
    elif len(parts) == 2:
        word = parts[1]
        await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"hint_typing_{chat_id}",
                    title=t.INLINE_INVALID_HINT_TITLE,
                    description=t.INLINE_INVALID_HINT_DESC.format(input=word),
                    input_message_content=InputTextMessageContent(
                        message_text=t.HINT_COUNT_REQUIRED.format(word=word)
                    ),
                )
            ],
            cache_time=1,
        )
    else:
        await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"hint_empty_{chat_id}",
                    title=t.INLINE_HINT_TITLE,
                    description=t.INLINE_HINT_DESC,
                    input_message_content=InputTextMessageContent(
                        message_text=t.HINT_EMPTY_QUERY
                    ),
                )
            ],
            cache_time=1,
        )

@router.inline_query(lambda q: q.query.startswith("reveal"))
async def inline_reveal(query: InlineQuery):
    # Support both "reveal_<chat_id> [search]" and just "reveal [search]"
    parts = query.query.strip().split(" ")
    first_part = parts[0]  # e.g. "reveal_-100123" or "reveal"
    
    chat_id = None
    if "_" in first_part:
        try:
            chat_id = int(first_part.split("_")[1])
        except ValueError:
            pass

    user_id = query.from_user.id
    game = None
    if chat_id:
        game = get_cn_game(chat_id)
    
    # Fallback to search game session the user is currently playing.
    # If still not found, check if there's only one active session globally.
    if not game:
        for sess in manager.sessions.values():
            if isinstance(sess, CodeNamesGame) and user_id in sess.players:
                game = sess
                chat_id = sess.chat_id
                break
        
        if not game:
            active_sessions = [sess for sess in manager.sessions.values() if isinstance(sess, CodeNamesGame)]
            if len(active_sessions) == 1:
                game = active_sessions[0]
                chat_id = game.chat_id

    if not game:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id="reveal_no_game",
                    title=b("uk", "Гра не знайдена або вже завершена", "Game not found or finished"),
                    description=b("uk", "Створіть нову гру за допомогою /codenames", "Create a new game with /codenames"),
                    input_message_content=InputTextMessageContent(
                        message_text=b("uk", "Гра вже завершена. Створіть нову гру за допомогою /codenames", "Game finished. Create a new game with /codenames")
                    ),
                )
            ],
            cache_time=1,
        )

    t = get_text(game.language)
    user_id = query.from_user.id

    player = game.players.get(user_id)
    if not player:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"reveal_join_{chat_id}",
                    title=t.NOT_A_PLAYER,
                    description=t.NOT_A_PLAYER_DESC,
                    input_message_content=InputTextMessageContent(
                        message_text="/cn_join"
                    ),
                )
            ],
            cache_time=1,
        )

    current_team = game.engine.current_turn
    # Robust duet check: engine mode OR metadata mode
    is_duet = game.engine.mode == "duet" or game.metadata.get("mode", "").lower() == "duet"
    if not is_duet and (
        player.role == "spymaster" or player.role == "dual_spymaster"
    ):
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"reveal_spymaster_{chat_id}",
                    title=t.SPYMASTER_GUESS_ERROR,
                    description=t.REVEAL_CAPTAIN_ERROR,
                    input_message_content=InputTextMessageContent(
                        message_text=b(game.language, "Я лише капітан.", "I am just a captain.")
                    ),
                )
            ],
            cache_time=1,
        )

    if player.team != current_team.value and not is_duet:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"reveal_not_turn_{chat_id}",
                    title=t.NOT_YOUR_TURN,
                    description=t.NOT_YOUR_TURN_DESC,
                    input_message_content=InputTextMessageContent(
                        message_text=b(game.language, "Я чекаю своєї черги.", "I'm waiting for my turn.")
                    ),
                )
            ],
            cache_time=1,
        )

    if not game.engine.clue:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"reveal_wait_{chat_id}",
                    title=b(game.language, "Зачекайте", "Wait"),
                    description=t.SPYMASTER_WAIT,
                    input_message_content=InputTextMessageContent(
                        message_text=t.REVEAL_WAIT_CLUE
                    ),
                )
            ],
            cache_time=1,
        )

    parts = query.query.strip().split(" ")
    search_term = parts[1].lower() if len(parts) > 1 else ""

    results = []
    for i, card in enumerate(game.engine.board):
        if not card.is_revealed:
            if search_term and search_term not in card.word.lower():
                continue
            results.append(
                InlineQueryResultArticle(
                    id=f"reveal_{chat_id}_{i}",
                    title=card.word,
                    input_message_content=InputTextMessageContent(
                        message_text=t.REVEAL_WORD_MSG.format(word=card.word.upper()),
                        parse_mode="HTML"
                    ),
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text=t.CHOOSE_WORD_BTN, switch_inline_query_current_chat=f"reveal_{chat_id}")]
                    ])
                )
            )

    if not results:
        results.append(
            InlineQueryResultArticle(
                id=f"reveal_not_found_{chat_id}",
                title=b(game.language, "Не знайдено", "Not found"),
                description=t.REVEAL_NOT_FOUND,
                input_message_content=InputTextMessageContent(message_text="..."),
            )
        )

    # Telegram inline queries are limited to 50 results, we have at most 25
    await query.answer(results, cache_time=1)

@router.message(Command("debug_autobot"))
async def cmd_debug_autobot(message: types.Message, bot: Bot):
    """Admin command to show auto-bot clue associations (debug mode)."""
    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
        return await message.answer("❌ No active game found or game is not in progress")

    # Check if user is admin
    is_admin = False
    if message.chat.type in ["group", "supergroup"]:
        try:
            member = await bot.get_chat_member(message.chat.id, message.from_user.id)
            if member.status in ["administrator", "creator"]:
                is_admin = True
        except Exception:
            pass
    else:
        is_admin = True  # Allow in private chats for testing

    if not is_admin:
        return await message.answer("🚫 This command is only available for admins")

    # Check if auto-bot is enabled
    if not game.metadata.get("auto_bot_enabled", False):
        return await message.answer("ℹ️ Auto-bot is not enabled in this game")

    # Import AI bot
    from src.games.codenames.ai_bot import AIBot

    # Create AI bot instance
    ai_bot = AIBot(language=game.language, difficulty=game.metadata.get("auto_bot_difficulty", "medium"))

    # Generate clue with debug info
    clue_result = ai_bot.generate_clue(game.engine, game.engine.current_turn)

    if not clue_result:
        return await message.answer("❌ Auto-bot could not generate a clue for the current board state")

    clue_word, count, explanation = clue_result

    # Send debug info to admin
    debug_msg = f"🔍 <b>Auto-Bot Debug Info</b>\n"
    display_count = "∞" if count == 0 else count
    debug_msg += f"📢 Clue: <b>{clue_word.upper()} {display_count}</b>\n"
    debug_msg += f"💡 Explanation: <i>{explanation}</i>\n"
    debug_msg += f"\n🎯 Current Team: {'🟢 Green' if game.engine.current_turn == Team.GREEN else '🔴 Red'}\n"

    # Add board state info
    team_words = []
    other_words = []
    assassin_words = []
    bystander_words = []

    for card in game.engine.board:
        if not card.is_revealed:
            if game.engine.mode == "duet":
                color_a = game.engine.get_duet_color(card.index, "a")
                color_b = game.engine.get_duet_color(card.index, "b")
                if color_a == CardColor.GREEN or color_b == CardColor.GREEN:
                    team_words.append(card.word)
                elif color_a == CardColor.ASSASSIN or color_b == CardColor.ASSASSIN:
                    assassin_words.append(card.word)
                else:
                    bystander_words.append(card.word)
            else:
                if card.color.value == game.engine.current_turn.value:
                    team_words.append(card.word)
                elif card.color == CardColor.ASSASSIN:
                    assassin_words.append(card.word)
                elif card.color in [CardColor.GREEN, CardColor.RED]:
                    other_words.append(card.word)
                else:
                    bystander_words.append(card.word)

    debug_msg += f"\n🟢 Target Words: {', '.join(team_words) if team_words else 'None'}\n"
    debug_msg += f"🔴 Other Team Words: {', '.join(other_words) if other_words else 'None'}\n"
    debug_msg += f"💀 Assassin Words: {', '.join(assassin_words) if assassin_words else 'None'}\n"
    debug_msg += f"⚪ Bystander Words: {', '.join(bystander_words) if bystander_words else 'None'}"

    try:
        await message.answer(debug_msg, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Error sending debug info: {e}")

@router.message(lambda m: m.text and (m.text.startswith("🔎 Обрано слово: ") or m.text.startswith("REVEAL: ")))
async def process_reveal_text(message: types.Message, bot: Bot):
    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
        return

    # Guard: ignore if the game already ended
    if game.engine and game.engine.is_over:
        return

    t = get_text(game.language)
    clean_text = message.text
    idx = -1
    
    if clean_text.startswith("🔎 Обрано слово: "):
        word_text = clean_text.replace("🔎 Обрано слово: ", "").strip().lower()
        if game.engine:
            for i, card in enumerate(game.engine.board):
                if card.word.lower() == word_text:
                    idx = i
                    break
    else:
        try:
            idx = int(clean_text.replace("REVEAL: ", "").strip())
        except ValueError:
            return

    if idx == -1:
        return

    player = game.players.get(message.from_user.id)
    if not player:
        return

    current_team = game.engine.current_turn
    if game.engine.mode == "duet":
        guessing_team_val = "red" if current_team == Team.GREEN else "green"
        if player.team != guessing_team_val:
            return
    else:
        if player.role == "spymaster" or player.role == "dual_spymaster":
            return
        if player.team != current_team.value:
            return

    if not game.engine.clue:
        return

    turn_before = game.engine.current_turn
    card_word = game.engine.get_board_state(revealed_only=False)[idx]["word"]

    if game.engine.reveal_card(idx):
        await update_main_board(message, game, bot)

        # Send guess result notification
        color_val = game.engine.board[idx].revealed_color

        if game.engine.mode == "duet":
            if color_val == CardColor.GREEN:
                color_name = b(game.language, "🟢 Агент (Зелене)", "🟢 Agent (Green)")
            elif color_val == CardColor.ASSASSIN:
                color_name = b(game.language, "💀 Вбивця", "💀 Assassin")
            else:
                color_name = b(game.language, "⚪ Нейтральне", "⚪ Neutral")
        else:
            if color_val == CardColor.GREEN:
                color_name = b(game.language, "🟢 Зелена команда", "🟢 Green Team")
            elif color_val == CardColor.RED:
                color_name = b(game.language, "🔴 Червона команда", "🔴 Red Team")
            elif color_val == CardColor.ASSASSIN:
                color_name = b(game.language, "💀 Вбивця", "💀 Assassin")
            else:
                color_name = b(game.language, "⚪ Нейтральне", "⚪ Neutral")

        msg_text = t.REVEAL_RESULT_MSG.format(name=player.full_name, word=card_word.upper(), color=color_name)
        kb = None

        if game.engine.is_over:
            winner_text = t.WIN_GREEN if game.engine.winner == Team.GREEN else t.WIN_RED
            if game.engine.mode == "duet":
                winner_text = t.WIN_DUET if game.engine.winner else t.LOSE_DUET

            await bot.send_message(
                game.chat_id,
                f"{msg_text}\n\n{t.GAME_ENDED_TITLE.format(winner=winner_text)}",
                message_thread_id=game.thread_id,
                parse_mode="HTML"
            )
            
            try:
                board_id = getattr(game, 'board_msg_id', None) or game.metadata.get('board_msg_id')
                if board_id:
                    await bot.unpin_chat_message(chat_id=game.chat_id, message_id=board_id)
                elif game.metadata.get("registration_msg_id"):
                    await bot.unpin_chat_message(
                        chat_id=game.chat_id, message_id=game.metadata["registration_msg_id"]
                    )
            except Exception:
                pass

            manager.end_game(game.chat_id)
        else:
            turn_after = game.engine.current_turn
            if turn_before != turn_after:
                btn_rows = []
                btn_rows.append(types.InlineKeyboardButton(
                    text=t.GOTO_BOT_CARD_BTN, url=f"https://t.me/{bot.username}"
                ))
                btn_rows.append(types.InlineKeyboardButton(
                    text=t.GIVE_HINT_BTN,
                    switch_inline_query_current_chat="hint "
                ))
                kb = types.InlineKeyboardMarkup(inline_keyboard=[btn_rows])
                
                if game.engine.mode == "duet":
                    giver_id = game.spymasters.get(turn_after)
                    giver_mention = game.players[giver_id].mention if giver_id in game.players else "Напарник"
                    msg_text += f"\nХід переходить до: {giver_mention} (дає підказку)!"
                else:
                    team_name = "🔴 Червоних" if turn_after == Team.RED else "🟢 Зелених"
                    if game.language == "en":
                        team_name = "🔴 Red" if turn_after == Team.RED else "🟢 Green"
                    msg_text += f"\nХід переходить до команди: <b>{team_name}</b>!"
                msg_text += get_past_clues_html(game)
            else:
                if not game.button_board:
                    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
                        types.InlineKeyboardButton(text="🔍 Обрати слово", switch_inline_query_current_chat="reveal")
                    ]])

            await bot.send_message(
                game.chat_id,
                msg_text,
                message_thread_id=game.thread_id,
                reply_markup=kb,
                parse_mode="HTML"
            )

    manager.save_game(game.chat_id)
    try:
        await message.delete()
    except Exception:
        pass

@router.message(lambda m: m.text and (m.text.startswith("📢 Підказка: ") or m.text.startswith("HINT: ")))
async def process_hint_text(message: types.Message, bot: Bot):
    # This captures the spymaster's hint sent via inline
    game = get_cn_game(message.chat.id)
    if not game:
        # If message is from PM, try to find the game where this user is a spymaster
        game = find_game_for_user(message.from_user.id)
    if not game:
        return

    user_id = message.from_user.id
    player = game.players.get(user_id)
    if not player:
        return

    is_turn = game.spymasters.get(game.engine.current_turn) == user_id
    if not is_turn:
        return

    clean_text = message.text.split("\n")[0]
    if clean_text.startswith("📢 Підказка: "):
        clean_text = clean_text.replace("📢 Підказка: ", "")
    else:
        clean_text = clean_text.replace("HINT: ", "")

    parts = clean_text.strip().split(" ")
    if len(parts) == 2:
        word, count_str = parts[0], parts[1]
        
        # 1. Перевіряємо, чи ввів користувач будь-який безліміт
        if count_str in ["-", "НЕОБМЕЖЕНО", "UNLIMITED", "∞", "unlim", "необ"]:
            game.engine.set_clue(word, 0, display="∞")
            count = "∞"
        elif count_str == "0":
            game.engine.set_clue(word, 0, display="0")
            count = "0"
        else:
            count = int(count_str)
            game.engine.set_clue(word, count, display=count_str)
        
        # Тепер функція виведе в чат правильний count (число, 0 або ∞)
        await update_main_board(message, game, bot, update_pm=False)

        # If the hint was sent from PM, also send the announcement to the group chat
        if message.chat.type == "private":
            # Reconstruct the display count
            if count_str in ["-", "НЕОБМЕЖЕНО", "UNLIMITED", "∞", "unlim", "необ"]:
                display_count = "∞"
            elif count_str == "0":
                display_count = "0"
            else:
                display_count = count_str

            # Build turn info for the group announcement
            current_team = game.engine.current_turn
            t = get_text(game.language)
            chat_id_str = str(game.chat_id)
            board_id = getattr(game, 'board_msg_id', None) or game.metadata.get('board_msg_id')
            if chat_id_str.startswith("-100") and board_id:
                link = f"https://t.me/c/{chat_id_str[4:]}/{board_id}"
            else:
                link = f"https://t.me/{bot.username}"

            announce_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🗺️ До карти", url=link)]
            ])

            guessers = []
            if game.engine.mode == "duet":
                guesser_team = Team.RED if current_team == Team.GREEN else Team.GREEN
                guesser_id = game.spymasters.get(guesser_team)
                if guesser_id in game.players:
                    guessers.append(game.players[guesser_id])
            else:
                for pid, p in game.players.items():
                    if p.team == current_team.value and p.role == "agent":
                        guessers.append(p)

            if guessers:
                guessers_formatted = []
                for p in guessers:
                    p_emoji = ("🅰️" if p.team == "green" else "🅱️") if game.engine.mode == "duet" else ("🟢" if p.team == "green" else "🔴")
                    if p.username:
                        guessers_formatted.append(f"{p_emoji} @{p.username}")
                    else:
                        guessers_formatted.append(f"{p_emoji} <b>{p.full_name}</b>")
                guesser_mentions = ", ".join(guessers_formatted)
                turn_info = t.TURN_INFO_GUESS.format(mentions=guesser_mentions)
            else:
                if game.engine.mode == "duet":
                    team_color_name = b(game.language, "🅰️ Сторони A", "🅰️ Side A") if current_team == Team.GREEN else b(game.language, "🅱️ Сторони B", "🅱️ Side B")
                else:
                    team_color_name = b(game.language, "🟢 Зелених", "🟢 Green") if current_team == Team.GREEN else b(game.language, "🔴 Червоних", "🔴 Red")
                turn_info = t.TURN_INFO_OPERATIVES.format(team=team_color_name)

            announce_text = t.HINT_ANNOUNCE.format(word=word.upper(), count=display_count, info=turn_info)
            await bot.send_message(
                game.chat_id,
                announce_text,
                message_thread_id=game.thread_id,
                reply_markup=announce_kb,
                parse_mode="HTML"
            )
    manager.save_game(game.chat_id)

@router.callback_query(F.data == "none")
async def cb_none(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()

@router.callback_query(F.data == "game_shop")
async def cb_game_shop(callback: types.CallbackQuery, bot: Bot):
    game = get_cn_game(callback.message.chat.id)
    if not game:
        return await callback.answer(b("uk", "❌ Гра не знайдена або вже завершена! Створіть нову.", "❌ Game not found or finished! Create a new one."), show_alert=True)

    t = get_text(game.language)
    player = game.players.get(callback.from_user.id)
    if not player:
        return await callback.answer(t.NOT_A_PLAYER, show_alert=True)

    balance = await db_service.get_user_diamonds(callback.from_user.id)

    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()

    # Armor Buff
    if Team(player.team) not in game.engine.team_armor:
        kb.row(
            types.InlineKeyboardButton(
                text=f"{t.BUFF_ARMOR_NAME} — {t.BUFF_ARMOR_PRICE} 💎",
                callback_data=f"buy_buff_{game.chat_id}_armor",
            )
        )

    # Intercept Buff
    if Team(player.team) not in game.engine.team_interception:
        kb.row(
            types.InlineKeyboardButton(
                text=f"{t.BUFF_INTERCEPT_NAME} — {t.BUFF_INTERCEPT_PRICE} 💎",
                callback_data=f"buy_buff_{game.chat_id}_intercept",
            )
        )

    # Detector Buff
    kb.row(
        types.InlineKeyboardButton(
            text=f"{t.BUFF_DETECTOR_NAME} — {t.BUFF_DETECTOR_PRICE} 💎",
            callback_data=f"buy_buff_{game.chat_id}_detector",
        )
    )

    # Reveal Buff
    kb.row(
        types.InlineKeyboardButton(
            text=f"{t.REVEAL_BUFF_NAME} — {200} 💎",
            callback_data=f"buy_buff_{game.chat_id}_reveal",
        )
    )

    # Remap Buff
    kb.row(
        types.InlineKeyboardButton(
            text=f"{t.BUFF_REMAP_NAME} — {t.BUFF_REMAP_PRICE} 💎",
            callback_data=f"buy_buff_{game.chat_id}_remap",
        )
    )

    kb.row(types.InlineKeyboardButton(text=t.CLOSE_BTN, callback_data="none"))

    text = (
        f"{t.SHOP_TITLE}\n"
        f"{t.SHOP_BALANCE.format(balance=balance)}\n\n"
        f"{t.SHOP_ITEM_DESC.format(name=t.BUFF_ARMOR_NAME, price=t.BUFF_ARMOR_PRICE, desc=t.BUFF_ARMOR_DESC)}\n"
        f"{t.SHOP_ITEM_DESC.format(name=t.BUFF_INTERCEPT_NAME, price=t.BUFF_INTERCEPT_PRICE, desc=t.BUFF_INTERCEPT_DESC)}\n"
        f"{t.SHOP_ITEM_DESC.format(name=t.BUFF_DETECTOR_NAME, price=t.BUFF_DETECTOR_PRICE, desc=t.BUFF_DETECTOR_DESC)}\n"
        f"{t.SHOP_ITEM_DESC.format(name=t.BUFF_REMAP_NAME, price=t.BUFF_REMAP_PRICE, desc=t.BUFF_REMAP_DESC)}\n"
    )

    try:
        await bot.send_message(
            callback.from_user.id, text, reply_markup=kb.as_markup(), parse_mode="HTML"
        )
        await callback.answer(t.BUFF_MENU_SENT, show_alert=True)
    except Exception:
        await callback.answer(t.BUFF_MENU_DM_ERROR, show_alert=True)

@router.message(Command("b1", "b2", "b3", "b4", "b5"))
async def cmd_quick_buy_buff(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        return
        
    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
        return
        
    t = get_text(game.language)
    player = game.players.get(message.from_user.id)
    if not player:
        return await message.answer(t.NOT_A_PLAYER)

    cmd = message.text.split()[0][1:].lower() # "b1" ... "b5"
    
    # Map command to buff key
    buff_map = {
        "b1": "armor",
        "b2": "intercept",
        "b3": "detector",
        "b4": "reveal",
        "b5": "remap"
    }
    buff_type = buff_map.get(cmd)
    
    team = Team(player.team)
    if game.engine.current_turn != team and game.engine.mode != "duet":
        return await message.answer(t.NOT_YOUR_TURN)

    balance = await db_service.get_user_diamonds(message.from_user.id)
    inv = await db_service.get_user_inventory(message.from_user.id)
    
    prices = {
        "armor": t.BUFF_ARMOR_PRICE,
        "intercept": t.BUFF_INTERCEPT_PRICE,
        "detector": t.BUFF_DETECTOR_PRICE,
        "remap": t.BUFF_REMAP_PRICE,
        "reveal": 20,
    }
    
    price = prices.get(buff_type, 9999)
    use_inventory = inv.get(buff_type, 0) > 0
    
    if not use_inventory and balance < price:
        return await message.answer(t.BUY_FAIL)

    success = False
    result_msg = ""
    team_name = b(game.language, "🟢 Зелених", "🟢 Green") if team == Team.GREEN else b(game.language, "🔴 Червоних", "🔴 Red")

    if buff_type == "armor":
        if team in game.engine.team_armor:
            return await message.answer(t.BUFF_USED_ERROR)
        game.engine.team_armor.append(team)
        success = True
        result_msg = t.BUFF_ARMOR_APPLIED.format(name=t.BUFF_ARMOR_NAME)

    elif buff_type == "intercept":
        if team in game.engine.team_interception:
            return await message.answer(t.BUFF_USED_ERROR)
        game.engine.team_interception.append(team)
        success = True
        result_msg = t.BUFF_INTERCEPT_APPLIED.format(name=t.BUFF_INTERCEPT_NAME)

    elif buff_type == "detector":
        word = game.engine.use_buff_detector()
        if word:
            success = True
            result_msg = t.BUFF_DETECTOR_RESULT.format(word=word.upper())
        else:
            return await message.answer(t.BUFF_NOT_AVAILABLE)

    elif buff_type == "reveal":
        word = game.engine.use_buff_reveal()
        if word:
            success = True
            result_msg = t.REVEAL_BUFF_RESULT.format(word=word.upper())
        else:
            return await message.answer(t.BUFF_NOT_AVAILABLE)

    elif buff_type == "remap":
        if game.engine.use_buff_replace_all():
            success = True
            result_msg = t.BUFF_REMAP_APPLIED.format(buff=t.BUFF_REMAP_NAME)
        else:
            return await message.answer(t.BUFF_REMAP_ERROR)

    if success:
        announcement = await handle_buff_usage(
            user_id=message.from_user.id,
            buff_type=buff_type,
            use_inventory=use_inventory,
            price=price,
            team_name=team_name,
            player_name=player.full_name,
            result_msg=result_msg,
            db_service=db_service,
            t=t
        )
        
        # Send group notification
        await bot.send_message(
            game.chat_id,
            announcement,
            message_thread_id=game.thread_id,
            parse_mode="HTML"
        )

        manager.save_game(game.chat_id)
        # Update board if it was a reveal or remap action
        if buff_type in ["detector", "reveal", "remap"]:
            await update_main_board(message, game, bot)
            
@router.message(Command("b1", "b2", "b3", "b4", "b5"))
async def cmd_quick_use_buff(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        return await message.answer(b("uk", "🎮 Будь ласка, використовуйте швидкі команди бафів у групі, де йде гра!", "🎮 Please use quick buff commands in the group where the game is!"))

    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
        return await message.answer(b("uk", "❌ Зараз немає активної гри у цьому чаті!", "❌ No active game in this chat!"))

    t = get_text(game.language)
    player = game.players.get(message.from_user.id)
    if not player:
        return await message.answer(t.NOT_A_PLAYER)

    team = Team(player.team)
    if game.engine.current_turn != team and game.engine.mode != "duet":
        return await message.answer(t.NOT_YOUR_TURN)

    cmd = message.text.split()[0][1:].lower() # e.g. "b1"
    buff_map = {
        "b1": "armor",
        "b2": "intercept",
        "b3": "detector",
        "b4": "reveal",
        "b5": "remap"
    }
    buff_type = buff_map.get(cmd)
    if not buff_type:
        return
    balance = await db_service.get_user_diamonds(message.from_user.id)
    inv = await db_service.get_user_inventory(message.from_user.id)
    
    prices = {
        "armor": t.BUFF_ARMOR_PRICE,
        "intercept": t.BUFF_INTERCEPT_PRICE,
        "detector": t.BUFF_DETECTOR_PRICE,
        "reveal": 20,
        "remap": t.BUFF_REMAP_PRICE
    }

    price = prices.get(buff_type, 9999)
    use_inventory = inv.get(buff_type, 0) > 0
    
    if not use_inventory and balance < price:
        return await message.answer(t.BUY_FAIL)

    success = False
    result_msg = ""
    team_name = b(game.language, "🟢 Зелених", "🟢 Green") if team == Team.GREEN else b(game.language, "🔴 Червоних", "🔴 Red")

    if buff_type == "armor":
        if team in game.engine.team_armor:
            return await message.answer(t.BUFF_USED_ERROR)
        game.engine.team_armor.append(team)
        success = True
        result_msg = t.BUFF_ARMOR_APPLIED.format(name=t.BUFF_ARMOR_NAME)

    elif buff_type == "intercept":
        if team in game.engine.team_interception:
            return await message.answer(t.BUFF_USED_ERROR)
        game.engine.team_interception.append(team)
        success = True
        result_msg = t.BUFF_INTERCEPT_APPLIED.format(name=t.BUFF_INTERCEPT_NAME)

    elif buff_type == "detector":
        word = game.engine.use_buff_detector()
        if word:
            success = True
            result_msg = t.BUFF_DETECTOR_RESULT.format(word=word.upper())
        else:
            return await message.answer(t.BUFF_NOT_AVAILABLE)

    elif buff_type == "reveal":
        word = game.engine.use_buff_reveal()
        if word:
            success = True
            result_msg = t.REVEAL_BUFF_RESULT.format(word=word.upper())
        else:
            return await message.answer(t.BUFF_NOT_AVAILABLE)

    elif buff_type == "remap":
        if game.engine.use_buff_replace_all():
            success = True
            result_msg = t.BUFF_REMAP_APPLIED.format(buff=t.BUFF_REMAP_NAME)
        else:
            return await message.answer(t.BUFF_REMAP_ERROR)

    if success:
        announcement = await handle_buff_usage(
            user_id=message.from_user.id,
            buff_type=buff_type,
            use_inventory=use_inventory,
            price=price,
            team_name=team_name,
            player_name=player.full_name,
            result_msg=result_msg,
            db_service=db_service,
            t=t
        )

        # Send group notification
        await bot.send_message(
            game.chat_id, announcement, message_thread_id=game.thread_id, parse_mode="HTML"
        )

        manager.save_game(game.chat_id)
        # Update board if it was a reveal or remap action
        if buff_type in ["detector", "reveal", "remap"]:
            await update_main_board(message, game, bot)
        try:
            await message.delete()
        except:
            pass

@router.message(Command("cn_buffs"))

async def cmd_game_buffs(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        return await message.answer(b("uk", "🎮 Будь ласка, використовуйте команду /buffs у групі, де йде гра!", "🎮 Please use /buffs command in the group where the game is!"))

    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
        return await message.answer(b("uk", "❌ Зараз немає активної гри у цьому чаті!", "❌ No active game in this chat!"))

    t = get_text(game.language)
    player = game.players.get(message.from_user.id)
    if not player:
        return await message.answer(t.NOT_A_PLAYER)

    balance = await db_service.get_user_diamonds(message.from_user.id)
    inv = await db_service.get_user_inventory(message.from_user.id)

    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()

    # Armor Buff
    if Team(player.team) not in game.engine.team_armor:
        kb.row(
            types.InlineKeyboardButton(
                text=f"{t.BUFF_ARMOR_NAME} — {t.BUFF_ARMOR_PRICE} 💎",
                callback_data=f"buy_buff_{game.chat_id}_armor",
            )
        )

    # Intercept Buff
    if Team(player.team) not in game.engine.team_interception:
        kb.row(
            types.InlineKeyboardButton(
                text=f"{t.BUFF_INTERCEPT_NAME} — {t.BUFF_INTERCEPT_PRICE} 💎",
                callback_data=f"buy_buff_{game.chat_id}_intercept",
            )
        )

    # Detector Buff
    kb.row(
        types.InlineKeyboardButton(
            text=f"{t.BUFF_DETECTOR_NAME} — {t.BUFF_DETECTOR_PRICE} 💎",
            callback_data=f"buy_buff_{game.chat_id}_detector",
        )
    )

    # Reveal Buff
    kb.row(
        types.InlineKeyboardButton(
            text=f"{t.REVEAL_BUFF_NAME} — 20 💎",
            callback_data=f"buy_buff_{game.chat_id}_reveal",
        )
    )

    # Remap Buff
    kb.row(
        types.InlineKeyboardButton(
            text=f"{t.BUFF_REMAP_NAME} — {t.BUFF_REMAP_PRICE} 💎",
            callback_data=f"buy_buff_{game.chat_id}_remap",
        )
    )

    kb.row(types.InlineKeyboardButton(text="❌ Закрити", callback_data="none"))

    text = (
        f"{t.SHOP_TITLE}\n"
        f"{t.SHOP_BALANCE.format(balance=balance)}\n\n"
        f"<b>{t.BUFF_ARMOR_NAME}</b> — {t.BUFF_ARMOR_PRICE} 💎 (Маєте: {inv['armor']})\n<i>{t.BUFF_ARMOR_DESC}</i>\n\n"
        f"<b>{t.BUFF_INTERCEPT_NAME}</b> — {t.BUFF_INTERCEPT_PRICE} 💎 (Маєте: {inv['intercept']})\n<i>{t.BUFF_INTERCEPT_DESC}</i>\n\n"
        f"<b>{t.BUFF_DETECTOR_NAME}</b> — {t.BUFF_DETECTOR_PRICE} 💎 (Маєте: {inv['detector']})\n<i>{t.BUFF_DETECTOR_DESC}</i>\n\n"
        f"<b>{t.REVEAL_BUFF_NAME}</b> — 20 💎 (Маєте: {inv['reveal']})\n<i>{t.REVEAL_BUFF_DESC}</i>\n\n"
        f"<b>{t.BUFF_REMAP_NAME}</b> — {t.BUFF_REMAP_PRICE} 💎 (Маєте: {inv['remap']})\n<i>{t.BUFF_REMAP_DESC}</i>\n"
    )

    try:
        await bot.send_message(
            message.from_user.id, text, reply_markup=kb.as_markup(), parse_mode="HTML"
        )
        sent = await message.answer(t.BUFF_MENU_SENT)

        async def delete_after(sec: int):
            await asyncio.sleep(sec)
            try:
                await sent.delete()
            except:
                pass
            try:
                await message.delete()
            except:
                pass

        import asyncio
        asyncio.create_task(delete_after(7))
    except Exception:
        await message.answer(t.SPYMASTER_DM_ERROR.format(mention=player.mention))

@router.callback_query(F.data.startswith("buy_buff_"))
async def process_buy_buff(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    chat_id = int(parts[2])
    buff_type = parts[3]

    game = get_cn_game(chat_id)
    if not game or game.status != "in_progress":
        return await callback.answer(b(game.language if game else "uk", "Гра не знайдена або завершена", "Game not found or finished"), show_alert=True)

    t = get_text(game.language)
    player = game.players.get(callback.from_user.id)
    if not player:
        return await callback.answer(t.NOT_A_PLAYER, show_alert=True)

    team = Team(player.team)
    if game.engine.current_turn != team and game.engine.mode != "duet":
        return await callback.answer(t.NOT_YOUR_TURN, show_alert=True)

    balance = await db_service.get_user_diamonds(callback.from_user.id)
    inv = await db_service.get_user_inventory(callback.from_user.id)

    prices = {
        "armor": t.BUFF_ARMOR_PRICE,
        "intercept": t.BUFF_INTERCEPT_PRICE,
        "detector": t.BUFF_DETECTOR_PRICE,
        "remap": t.BUFF_REMAP_PRICE,
        "reveal": 20,
    }

    price = prices.get(buff_type, 9999)
    use_inventory = inv.get(buff_type, 0) > 0

    if not use_inventory and balance < price:
        return await callback.answer(t.BUY_FAIL, show_alert=True)

    # Apply buff logic
    success = False
    result_msg = ""
    team_name = b(game.language, "🟢 Зелених", "🟢 Green") if team == Team.GREEN else b(game.language, "🔴 Червоних", "🔴 Red")

    if buff_type == "armor":
        if team in game.engine.team_armor:
            return await callback.answer(t.BUFF_USED_ERROR, show_alert=True)
        game.engine.team_armor.append(team)
        success = True
        result_msg = t.BUFF_ARMOR_APPLIED.format(name=t.BUFF_ARMOR_NAME)

    elif buff_type == "intercept":
        if team in game.engine.team_interception:
            return await callback.answer(t.BUFF_USED_ERROR, show_alert=True)
        game.engine.team_interception.append(team)
        success = True
        result_msg = t.BUFF_INTERCEPT_APPLIED.format(name=t.BUFF_INTERCEPT_NAME)

    elif buff_type == "detector":
        word = game.engine.use_buff_detector()
        if word:
            success = True
            result_msg = t.BUFF_DETECTOR_RESULT.format(word=word.upper())
        else:
            return await callback.answer(t.BUFF_NOT_AVAILABLE, show_alert=True)

    elif buff_type == "reveal":
        word = game.engine.use_buff_reveal()
        if word:
            success = True
            result_msg = t.REVEAL_BUFF_RESULT.format(word=word.upper())
        else:
            return await callback.answer(t.BUFF_NOT_AVAILABLE, show_alert=True)

    elif buff_type == "remap":
        if game.engine.use_buff_replace_all():
            success = True
            result_msg = t.BUFF_REMAP_APPLIED.format(buff=t.BUFF_REMAP_NAME)
        else:
            return await callback.answer(t.BUFF_REMAP_ERROR, show_alert=True)

    if success:
        announcement = await handle_buff_usage(
            user_id=callback.from_user.id,
            buff_type=buff_type,
            use_inventory=use_inventory,
            price=price,
            team_name=team_name,
            player_name=player.full_name,
            result_msg=result_msg,
            db_service=db_service,
            t=t
        )

        await callback.answer(t.BUY_SUCCESS, show_alert=True)

        # Send group notification
        await bot.send_message(
            chat_id, announcement, message_thread_id=game.thread_id, parse_mode="HTML"
        )

        manager.save_game(game.chat_id)
        # Update board if it was a reveal or remap action
        if buff_type in ["detector", "reveal", "remap"]:
            await update_main_board(callback.message, game, bot)
        # Delete PM menu message
        try:
            await callback.message.delete()
        except:
            pass

async def handle_buff_usage(
    user_id: int,
    buff_type: str,
    use_inventory: bool,
    price: int,
    team_name: str,
    player_name: str,
    result_msg: str,
    db_service: Any,
    t: Any,
) -> str:
    """
    Helper function to handle buff usage and generate the appropriate announcement.
    """
    if use_inventory:
        await db_service.update_user_buff(user_id, buff_type, -1)
        announcement = t.BUFF_USED_INVENTORY.format(
            name=player_name,
            team=team_name,
            result=result_msg
        )
    else:
        await db_service.update_user_diamonds(user_id, -price)
        announcement = t.BUFF_USED_DIAMONDS.format(
            name=player_name,
            team=team_name,
            price=price,
            result=result_msg
        )
    return announcement


@router.message(Command("cn_skip"))
async def cmd_skip(message: types.Message, bot: Bot, settings):
    if message.from_user.id not in settings.admin_ids:
        return

    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
        return

    t = get_text(game.language)
    turn_before = game.engine.current_turn
    game.engine.end_turn()
    if game.engine.mode == "duet":
        game.update_duet_spymaster_queue(previous_turn=turn_before)

    await update_main_board(message, game, bot)
    manager.save_game(game.chat_id)
    await message.answer("⏭ Хід пропущено адміністратором.")


@router.message(Command("cn_solve"))
async def cmd_solve(message: types.Message, bot: Bot, settings):
    if message.from_user.id not in settings.admin_ids:
        return

    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
        return

    player = game.players.get(message.from_user.id)
    if not player or not player.team:
        await message.answer("⚠️ Ви не зареєстровані як гравець команди!")
        return

    team_color = player.team  # "green" or "red"
    revealed_words = []
    
    if game.engine.mode == "duet":
        side = "a" if team_color == "green" else "b"
        for i, card in enumerate(game.engine.board):
            if not card.is_revealed:
                effective_color = game.engine.get_duet_color(i, side)
                if effective_color == CardColor.GREEN:
                    card.is_revealed = True
                    card.revealed_color = CardColor.GREEN
                    revealed_words.append(card.word)
    else:
        target_color = CardColor.GREEN if team_color == "green" else CardColor.RED
        for card in game.engine.board:
            if not card.is_revealed and card.color == target_color:
                card.is_revealed = True
                card.revealed_color = target_color
                revealed_words.append(card.word)

    if not revealed_words:
        await message.answer("ℹ️ Немає невідгаданих карт вашого кольору.")
        return

    game.engine.check_win()
    manager.save_game(game.chat_id)

    words_str = ", ".join([f"<b>{w}</b>" for w in revealed_words])
    msg_text = f"✅ Відгадано всі карти вашого кольору: {words_str}"

    await update_main_board(message, game, bot)

    if game.engine.is_over:
        chat_title = message.chat.title if message.chat.title else None
        await trigger_game_over(game.chat_id, bot, game, message, custom_msg_text=msg_text, chat_title=chat_title)
    else:
        await message.answer(msg_text, parse_mode="HTML")


