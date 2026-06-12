import asyncio
import logging
import time
import random
from aiogram import Bot

from src.core.platform.game_manager import manager
from src.games.codenames.engine import Team, CardColor
from src.bot.handlers.game_router import update_main_board
from src.assets.texts import get_text, b

logger = logging.getLogger(__name__)

async def check_turn_timers(bot: Bot):
    """Background task to check active game turn timers and registration lobby timers."""
    while True:
        try:
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
                        
                        is_spymaster_phase = (game.engine.clue is None)
                        card_word = ""
                        color_name = ""
                        
                        if is_spymaster_phase:
                            # Spymaster phase timeout: just pass turn (no auto-reveal)
                            turn_before = game.engine.current_turn
                            game.engine.end_turn()
                            if game.engine.mode == "duet":
                                game.update_duet_spymaster_queue(previous_turn=turn_before)
                            
                            msg_text = b(
                                game.language,
                                "⏰ <b>Час капітана вичерпано!</b> Підказку не було дано.",
                                "⏰ <b>Captain's time is up!</b> No hint was given."
                            )
                        else:
                            # Guessers phase timeout:
                            # Only reveal a random card if no guesses were made during this turn yet
                            should_auto_reveal = (game.engine.guesses_made == 0)
                            
                            # Find all unrevealed cards
                            unrevealed_indices = [i for i, card in enumerate(game.engine.board) if not card.is_revealed]
                            if should_auto_reveal and unrevealed_indices:
                                idx = random.choice(unrevealed_indices)
                                card = game.engine.board[idx]
                                card_word = card.word
                                
                                turn_before = game.engine.current_turn
                                game.engine.reveal_card(idx)
                                
                                # Determine color description
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
                                
                                # Since the turn timed out, force turn end if game is not over and turn hasn't changed
                                if not game.engine.is_over:
                                    if game.engine.current_turn == turn_before:
                                        game.engine.end_turn()
                                        if game.engine.mode == "duet":
                                            game.update_duet_spymaster_queue(previous_turn=turn_before)
                            else:
                                # Fallback/pass if guesses were already made during this turn
                                turn_before = game.engine.current_turn
                                game.engine.end_turn()
                                if game.engine.mode == "duet":
                                    game.update_duet_spymaster_queue(previous_turn=turn_before)
                            
                            if card_word:
                                msg_text = b(
                                    game.language,
                                    f"⏰ <b>Час вичерпано!</b>\n🔎 Автоматично обрано слово: <b>{card_word.upper()}</b> ({color_name}).",
                                    f"⏰ <b>Time is up!</b>\n🔎 Automatically revealed word: <b>{card_word.upper()}</b> ({color_name})."
                                )
                            else:
                                msg_text = f"⏰ {t.TIME_UP}"

                        manager.save_game(game.chat_id)

                        if game.engine.is_over:
                            # Full game over announcement (sends photo, stats, map, scores, and unpins board)
                            from src.bot.handlers.game_router import trigger_game_over
                            await trigger_game_over(game.chat_id, bot, game, message=None, custom_msg_text=msg_text)
                        else:
                            # Continue game: announce next turn
                            turn_after = game.engine.current_turn
                            if game.engine.mode == "duet":
                                giver_id = game.spymasters.get(turn_after)
                                giver_mention = game.players[giver_id].mention if (giver_id and giver_id in game.players) else ("Напарник" if game.language == "uk" else "Partner")
                                next_turn_text = b(game.language, f"Хід переходить до: {giver_mention} (дає підказку)!", f"Turn passes to: {giver_mention} (giving hint)!")
                            else:
                                team_name = "🔴 Червоних" if turn_after == Team.RED else "🟢 Зелених"
                                if game.language == "en":
                                    team_name = "🔴 Red" if turn_after == Team.RED else "🟢 Green"
                                next_turn_text = b(game.language, f"Хід переходить до команди: <b>{team_name}</b>!", f"Turn passes to team: <b>{team_name}</b>!")
                            
                            full_msg = f"{msg_text}\n\n{next_turn_text}"
                            
                            # Send the message
                            await bot.send_message(
                                game.chat_id,
                                full_msg,
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
            logger.error(f"Error checking turn/reg timers: {e}", exc_info=True)
            
        await asyncio.sleep(5)
