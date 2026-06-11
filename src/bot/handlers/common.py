import asyncio
from aiogram import Router, types, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame
from src.core.platform.base_game import GamePlayer
from src.core.database.service import db_service
from src.assets.texts import get_text, b
import logging

logger = logging.getLogger(__name__)

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
        username=message.from_user.username,
    )

    if game.add_player(player):
        if game.status == "in_progress":
            if game.metadata.get("mode", "Classic").lower() != "duet":
                red_count = sum(1 for p in game.players.values() if p.team == "red")
                green_count = sum(1 for p in game.players.values() if p.team == "green")
                if red_count < green_count:
                    player.team = "red"
                elif green_count < red_count:
                    player.team = "green"
                else:
                    import random
                    player.team = random.choice(["red", "green"])
                player.role = "agent"
            else:
                # Duet mode: add to the side with fewer players
                green_count = sum(1 for p in game.players.values() if p.team == "green")
                red_count = sum(1 for p in game.players.values() if p.team == "red")
                if green_count <= red_count:
                    player.team = "green"
                else:
                    player.team = "red"

                # Add to spymaster queue if joining side B (red team)
                if player.team == "red":
                    player.role = "dual_spymaster"
                    # Add to side B spymaster queue
                    queue = game.metadata.get("duet_side_b_queue", [])
                    if player.user_id not in queue:
                        queue.append(player.user_id)
                        game.metadata["duet_side_b_queue"] = queue
                else:
                    player.role = "agent"

        msg_id = game.metadata.get("registration_msg_id") or game.board_msg_id
        chat_link = None

        internal_chat_id = str(chat_id)
        if internal_chat_id.startswith("-100") and msg_id:
            clean_id = internal_chat_id.replace("-100", "")
            chat_link = f"https://t.me/c/{clean_id}/{msg_id}"

        kb = None
        if chat_link:
            kb = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text=t.RETURN_BTN, url=chat_link)]
                ]
            )

        if game.status == "in_progress":
            if game.metadata.get("mode", "Classic").lower() == "duet":
                join_msg = t.JOIN_DUET
            else:
                team_display = t.TEAM_GREEN_NAME if player.team == "green" else t.TEAM_RED_NAME
                join_msg = t.JOIN_TEAM.format(team=team_display)
        else:
            join_msg = t.JOIN_SUCCESS

        # Send the personal join confirmation to PM if joining from group chat
        if game.status == "in_progress" and message.chat.type in ("group", "supergroup"):
            try:
                await bot.send_message(message.from_user.id, join_msg, reply_markup=kb)
            except Exception:
                # Can't send to PM — ask user to start the bot first
                await message.answer(
                    b(game.language, 
                        "📩 Напишіть боту в ПП, щоб отримати деталі!",
                        "📩 Send a message to the bot in PM for details!"),
                )
        else:
            msg = await message.answer(join_msg, reply_markup=kb)
            if hasattr(player, "join_msg_id"):
                player.join_msg_id = msg.message_id

        try:
            await message.delete()
        except:
            pass

        if game.status == "in_progress":
            if game.metadata.get("mode", "Classic").lower() == "duet":
                await bot.send_message(
                    chat_id,
                    t.JOIN_DUET_PLAYER.format(name=player.full_name),
                    message_thread_id=game.thread_id,
                )
            else:
                team_emoji = "🟢" if player.team == "green" else "🔴"
                team_name = t.TEAM_GREEN_GEN_NAME if player.team == "green" else t.TEAM_RED_GEN_NAME
                await bot.send_message(
                    chat_id,
                    t.JOIN_TEAM_PLAYER.format(emoji=team_emoji, name=player.full_name, team=team_name),
                    message_thread_id=game.thread_id,
                )
        else:
            from src.bot.handlers.game_setup import update_registration_view
            await update_registration_view(bot, chat_id, game)
        manager.save_game(chat_id)
    else:
        await message.answer(t.ALREADY_JOINED)


@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, bot: Bot):
    if command.args and command.args.startswith("join_"):
        chat_id = int(command.args.replace("join_", ""))
        return await process_join_game(message, chat_id, bot)

    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)

    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(
            text=t.PROFILE_BACK_BTN.replace("� ", "👤 "), callback_data="profile_back"
        ),
        types.InlineKeyboardButton(
            text=t.PROFILE_BUY_DIAMONDS_BTN, callback_data="profile_shop_diamonds"
        ),
    )

    await message.answer(t.WELCOME, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.message(Command("cn_leave"))
async def cmd_cn_leave(message: types.Message, bot: Bot):
    """Leave the current game lobby or in-progress game."""
    game = manager.get_game(message.chat.id)
    if not game:
        return await message.answer("❓ Немає активної гри в цьому чаті." if message.chat.type != "private" else "❓ No active game.")
    
    if message.from_user.id not in game.players:
        return await message.answer("👋 Ви не в грі." if game.language == "uk" else "👋 You are not in the game.")
    
    leaving_user_id = message.from_user.id
    player = game.players.get(leaving_user_id)
    is_spymaster = False
    spymaster_team = None
    
    if player and hasattr(game, 'spymasters') and game.spymasters:
        for team, sm_id in game.spymasters.items():
            if sm_id == leaving_user_id:
                is_spymaster = True
                spymaster_team = team
                break
    
    game.remove_player(leaving_user_id)
    manager.save_game(game.chat_id)
    
    t = get_text(game.language)
    player_name = message.from_user.full_name
    
    if game.status == "registration":
        from src.bot.handlers.game_setup import update_registration_view
        await update_registration_view(bot, game.chat_id, game)
        await message.answer(t.PLAYER_LEFT.format(name=player_name) if hasattr(t, "PLAYER_LEFT") else f"{player_name} вийшов з гри.")
    else:
        # In-progress game
        await bot.send_message(
            game.chat_id,
            t.PLAYER_LEFT_GAME.format(name=player_name) if hasattr(t, "PLAYER_LEFT_GAME") else f"👋 {player_name} покинув гру.",
            message_thread_id=game.thread_id,
        )
        
        # Check if the game should end due to missing spymaster
        game_mode = game.metadata.get("mode", "Classic").lower()
        should_end = False
        
        if is_spymaster:
            if game_mode in ("3p", "duet"):
                # Trio/Duet: if the spymaster leaves, the game cannot continue
                should_end = True
            elif game_mode == "classic":
                # Classic: check if there's still at least 1 spymaster and 1 agent per team
                green_spymaster = any(
                    game.spymasters.get(team) and 
                    game.players.get(game.spymasters[team]) and
                    team.value == "green"
                    for team in game.spymasters
                ) if hasattr(game, 'spymasters') else False
                red_spymaster = any(
                    game.spymasters.get(team) and 
                    game.players.get(game.spymasters[team]) and
                    team.value == "red"
                    for team in game.spymasters
                ) if hasattr(game, 'spymasters') else False
                
                green_agents = any(p.team == "green" and p.role == "agent" for p in game.players.values())
                red_agents = any(p.team == "red" and p.role == "agent" for p in game.players.values())
                
                if not (green_spymaster and green_agents and red_spymaster and red_agents):
                    should_end = True
        else:
            # Non-spymaster left - check if classic mode still has enough players
            if game_mode == "classic":
                green_spymaster = any(
                    game.spymasters.get(team) and 
                    game.players.get(game.spymasters[team]) and
                    team.value == "green"
                    for team in game.spymasters
                ) if hasattr(game, 'spymasters') else False
                red_spymaster = any(
                    game.spymasters.get(team) and 
                    game.players.get(game.spymasters[team]) and
                    team.value == "red"
                    for team in game.spymasters
                ) if hasattr(game, 'spymasters') else False
                
                green_agents = any(p.team == "green" and p.role == "agent" for p in game.players.values())
                red_agents = any(p.team == "red" and p.role == "agent" for p in game.players.values())
                
                if not (green_spymaster and green_agents and red_spymaster and red_agents):
                    should_end = True
        
        if should_end:
            from aiogram.types import BufferedInputFile
            
            # Determine ending reason
            end_text = b(game.language, 
                f"🏁 Гра завершена, оскільки {player_name} покинув(ла) гру.",
                f"🏁 Game ended because {player_name} left the game.")
            
            # Unpin messages
            try:
                if game.board_msg_id:
                    await bot.unpin_chat_message(chat_id=game.chat_id, message_id=game.board_msg_id)
                if game.metadata.get("registration_msg_id"):
                    await bot.unpin_chat_message(chat_id=game.chat_id, message_id=game.metadata["registration_msg_id"])
            except Exception:
                pass
            
            # Build rewards summary (same logic as normal game end)
            rewards_summary = []
            if "points" not in game.metadata:
                game.metadata["points"] = {}
            
            for pid, p in game.players.items():
                p_points = game.metadata.get("points", {}).get(pid, 0)
                p_stats = game.metadata.get("stats", {}).get(pid, {
                    "guessed_words": 0,
                    "assassins_hit": 0,
                    "opponent_words_hit": 0
                })
                
                # Save game result
                try:
                    await db_service.save_game_result(
                        user_id=pid,
                        full_name=p.full_name,
                        username=p.username or "",
                        game_type="codenames",
                        result="loss",
                        guessed_words=p_stats.get("guessed_words", 0),
                        assassins_hit=p_stats.get("assassins_hit", 0),
                        opponent_words_hit=p_stats.get("opponent_words_hit", 0),
                        mode=game.metadata.get("mode", "classic"),
                        chat_id=game.chat_id,
                    )
                except Exception:
                    pass
                
                # Build rewards line — captains get 👨‍✈️ instead of team color
                if p.role in ("spymaster", "dual_spymaster"):
                    team_emoji = "👨‍✈️"
                else:
                    if game.metadata.get("mode", "").lower() == "duet":
                        team_emoji = "🅰️" if p.team == "green" else "🅱️" if p.team == "red" else "👤"
                    else:
                        team_emoji = "🟢" if p.team == "green" else "🔴" if p.team == "red" else "👤"
                player_display = f"{team_emoji} {p.mention}"
                
                p_stats_local = game.metadata.get("stats", {}).get(pid, {"guessed_words": 0})
                if p_stats_local.get("guessed_words", 0) > 0:
                    coins_earned = max(0, 2 + max(0, p_points))
                    try:
                        await db_service.update_user_coins(pid, coins_earned)
                    except Exception:
                        pass
                    rewards_summary.append(
                        f"{player_display}: {p_points} " + b(game.language, "очок", "points") +
                        f" (🪙 +{coins_earned})"
                    )
                else:
                    rewards_summary.append(
                        f"{player_display}: {p_points} " + b(game.language, "очок", "points")
                    )
            
            rewards_str = "\n".join(rewards_summary)
            
            # Send final board image with results
            try:
                final_board_img = await game.get_board_image(spymaster_view=True)
                caption = f"{end_text}\n\n{t.SCORE_REWARDS_TITLE}\n{rewards_str}"
                await bot.send_photo(
                    game.chat_id,
                    photo=BufferedInputFile(final_board_img.read(), filename="final_board.png"),
                    caption=caption,
                    message_thread_id=game.thread_id,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Failed to send final board image: {e}")
                # Fallback: send text only
                await bot.send_message(
                    game.chat_id,
                    f"{end_text}\n\n{t.SCORE_REWARDS_TITLE}\n{rewards_str}",
                    message_thread_id=game.thread_id,
                    parse_mode="HTML",
                )
            
            manager.end_game(game.chat_id)
    
    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("cn_join"))
async def cmd_cn_join(message: types.Message, command: CommandObject, bot: Bot):
    if not command.args:
        chat_id = message.chat.id
    else:
        try:
            chat_id = int(command.args)
        except ValueError:
            return

    await process_join_game(message, chat_id, bot)
    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("codenames"))
async def start_codenames(message: types.Message, bot: Bot, settings):
    logger.info(
        f"TRACE: start_codenames triggered by {message.from_user.id} in chat {message.chat.id}"
    )
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    if message.chat.type == "private":
        logger.info("TRACE: start_codenames rejected (private chat)")
        return await message.answer(t.MIN_PLAYERS)

    if (
        not chat_settings.allow_everyone_start
        and message.from_user.id not in settings.admin_ids
    ):
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ADMIN_ONLY_ERROR)

    existing_game = manager.get_game(message.chat.id)
    if existing_game:
        # Check if registration lobby is active
        if existing_game.status == "registration":
            reg_msg_id = existing_game.metadata.get("registration_msg_id")
            if reg_msg_id:
                # If there's an active registration message, warn and return early
                await message.answer(
                    t.GAME_ALREADY_STARTED or "Лоббі вже створене і триває реєстрація!"
                )
                return
            else:
                # Restored from Redis but registration message is missing (e.g. after restart)
                game = existing_game
                game.metadata["creator_id"] = message.from_user.id
        elif existing_game.status == "in_progress":
            # Game is still in progress — inform and offer to re-join
            await message.answer(
                t.GAME_ALREADY_STARTED or "Гра вже триває!"
            )
            return
        else:
            return await message.answer(
                t.GAME_ALREADY_STARTED or "Гра вже триває або лоббі вже створене!"
            )
    else:
        game = manager.create_game(
            message.chat.id, CodeNamesGame, message.message_thread_id
        )
    game.metadata["creator_id"] = message.from_user.id
    game.language = chat_settings.language
    game.word_set = chat_settings.last_word_set
    game.reg_timer = chat_settings.last_reg_timer
    game.turn_timer = chat_settings.last_turn_timer
    # Normalize stored mode to match what the engine uses ("Classic"/"Duet").
    _stored_mode = (chat_settings.last_mode or "classic").strip().lower()
    _mode_map = {"classic": "Classic", "duet": "Duet"}
    game.metadata["mode"] = _mode_map.get(_stored_mode, "Classic")
    game.dark_mode = chat_settings.dark_mode
    game.button_board = chat_settings.button_board
    game.board_size = chat_settings.board_size
    game.pin_message = chat_settings.pin_message
    game.metadata["spymaster_sheet"] = chat_settings.spymaster_sheet
    game.metadata["show_past_clues"] = chat_settings.show_past_clues
    game.metadata["strict_clues"] = chat_settings.strict_clues
    game.metadata["allow_pass"] = chat_settings.allow_pass
    # Sync hardcore + admin-only-settings from chat settings so the lobby
    # reflects what is stored in the DB (and chat settings changes propagate).
    game.metadata["hardcore_mode"] = chat_settings.hardcore_mode
    game.metadata["admin_only_settings"] = chat_settings.admin_only_settings
    # Auto-bot also lives in chat settings.
    game.metadata["auto_bot_enabled"] = chat_settings.auto_bot_enabled
    game.metadata["auto_bot_difficulty"] = chat_settings.auto_bot_difficulty

    join_url = f"https://t.me/{bot.username}?start=join_{message.chat.id}"

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=t.JOIN_BTN, url=join_url)],
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

    sent_msg = await message.answer(
        t.REGISTRATION_TITLE.format(count=0), reply_markup=kb
    )
    game.registration_msg_id = sent_msg.message_id
    game.metadata["registration_msg_id"] = sent_msg.message_id

    if chat_settings.pin_message:
        try:
            await bot.pin_chat_message(
                message.chat.id, sent_msg.message_id, disable_notification=True
            )
            try:
                await bot.delete_message(message.chat.id, sent_msg.message_id + 1)
            except Exception:
                pass
        except Exception:
            pass

    manager.save_game(game.chat_id)

    # Notify next-game subscribers
    async def notify_subscribers(chat_id, chat_title, lang):
        subs = await db_service.get_system_setting("next_game_subscribers")
        chat_key = str(chat_id)
        if chat_key in subs and subs[chat_key]:
            user_ids = subs[chat_key]
            subs[chat_key] = []
            await db_service.update_system_setting("next_game_subscribers", subs)
            
            chat_id_str = str(chat_id)
            board_id = sent_msg.message_id
            if chat_id_str.startswith("-100"):
                chat_link = f"https://t.me/c/{chat_id_str[4:]}/{board_id}"
            else:
                chat_link = f"https://t.me/{bot.username}"
                
            btn_text = b(lang, "Повернутися до гри 🎮", "Back to Game 🎮")
            pm_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=btn_text, url=chat_link)]
            ])
            
            for uid in user_ids:
                try:
                    await bot.send_message(
                        chat_id=uid,
                        text=b(lang,
                               f"🎮 У чаті <b>{chat_title}</b> розпочалася нова гра Codenames! Заходьте грати!",
                               f"🎮 A new Codenames game has started in the chat <b>{chat_title}</b>! Join the game!"),
                        reply_markup=pm_kb,
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    asyncio.create_task(notify_subscribers(message.chat.id, message.chat.title, chat_settings.language))
    asyncio.create_task(game.start_reg_timer(bot))


@router.message(Command("cn_next"))
async def cmd_cn_next(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        return await message.answer(b("uk", "🎮 Будь ласка, використовуйте цю команду в групі!", "🎮 Please use this command in the group!"))

    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    
    user_mention = message.from_user.mention_html()
    chat_title = message.chat.title
    
    # Save subscription
    subs = await db_service.get_system_setting("next_game_subscribers")
    chat_key = str(message.chat.id)
    if chat_key not in subs:
        subs[chat_key] = []
    if message.from_user.id not in subs[chat_key]:
        subs[chat_key].append(message.from_user.id)
    await db_service.update_system_setting("next_game_subscribers", subs)
    
    group_text = b(chat_settings.language,
                   f"🎮 {user_mention} зареєструвався на наступну гру! Бот сповістить у ПП при її початку.",
                   f"🎮 {user_mention} registered for the next game! The bot will notify you in PM when it starts.")
    
    pm_text = b(chat_settings.language,
                f"🎮 Ви успішно зареєструвалися на наступну гру в чаті <b>{chat_title}</b>! Я сповіщу вас, коли вона розпочнеться.",
                f"🎮 You have successfully registered for the next game in <b>{chat_title}</b>! I will notify you when it starts.")

    # Send message to the group
    await message.answer(group_text, parse_mode="HTML")

    # Send message to the user in PM
    try:
        await bot.send_message(chat_id=message.from_user.id, text=pm_text, parse_mode="HTML")
    except Exception:
        # If bot failed to message in PM (e.g., user blocked bot or hasn't started it)
        warning_text = b(chat_settings.language,
                        f"⚠️ {user_mention}, будь ласка, почніть діалог з ботом в особистих повідомленнях (ПП), щоб бот міг сповістити вас!",
                        f"⚠️ {user_mention}, please start a chat with the bot in PM so the bot can notify you!")
        await message.answer(warning_text, parse_mode="HTML")