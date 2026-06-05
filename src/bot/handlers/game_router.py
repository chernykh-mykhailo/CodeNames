import logging
from typing import Optional
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
from src.assets.texts import get_text
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
                    switch_inline_query_current_chat=f"hint_{game.chat_id} ",
                )
            ]
        )
    else:
        if not game.button_board:
            buttons.append(
                [
                    types.InlineKeyboardButton(
                        text=t.CHOOSE_WORD_BTN,
                        switch_inline_query_current_chat=f"reveal_{game.chat_id}",
                    )
                ]
            )

    buttons.append(
        [
            types.InlineKeyboardButton(
                text="🤖 Перейти в бота (Карта)", url=f"https://t.me/{bot.username}"
            )
        ]
    )
    buttons.append(
        [types.InlineKeyboardButton(text=t.PASS_BTN, callback_data="board_pass")]
    )



    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def update_main_board(message: types.Message, game: CodeNamesGame, bot: Bot):
    caption = game.get_status_message()

    kb = await get_game_keyboard(game, bot)
    board_img = await game.get_board_image(spymaster_view=False)

    try:
        await bot.edit_message_media(
            chat_id=game.chat_id,
            message_id=game.board_msg_id,
            media=types.InputMediaPhoto(
                media=BufferedInputFile(board_img.read(), filename="board.png"),
                caption=caption,
                parse_mode="HTML",
            ),
            reply_markup=kb,
        )
    except Exception as e:
        logger.error(f"Board update failed: {e}")

    # Update spymasters' views in PM
    t = get_text(game.language)
    updated_sms = set()
    for team, sm_id in game.spymasters.items():
        if sm_id and sm_id not in updated_sms:
            updated_sms.add(sm_id)
            msg_id = game.metadata.get(f"sm_msg_id_{sm_id}")
            if msg_id:
                try:
                    side = (
                        "a"
                        if team == Team.GREEN
                        else "b"
                        if game.engine.mode == "duet"
                        else None
                    )
                    sm_img = await game.get_board_image(spymaster_view=True, side=side)
                    
                    chat_id_str = str(game.chat_id)
                    if chat_id_str.startswith("-100"):
                        link = f"https://t.me/c/{chat_id_str[4:]}/{game.board_msg_id}"
                    else:
                        link = ""
                    btn = types.InlineKeyboardButton(text="🗺 До карти в групі", url=link)
                    kb_sm = InlineKeyboardBuilder().row(btn).as_markup() if link else None

                    if game.engine.mode == "duet":
                        role_msg = "🤝 <b>Кооперативний режим </b>\nВаша мета — відгадати всі зелені картки агентів разом з напарником!"
                    else:
                        role_msg = t.SPYMASTER_ROLE.format(
                            team=t.TEAM_GREEN if team == Team.GREEN else t.TEAM_RED
                        )

                    await bot.edit_message_media(
                        chat_id=sm_id,
                        message_id=msg_id,
                        media=types.InputMediaPhoto(
                            media=BufferedInputFile(sm_img.read(), filename="board.png"),
                            caption=f"{role_msg}\n\n{t.SPYMASTER_INSTRUCTIONS}",
                            parse_mode="HTML"
                        ),
                        reply_markup=kb_sm
                    )
                except Exception as e:
                    logger.error(f"Failed to update PM board for spymaster {sm_id}: {e}")


@router.callback_query(lambda c: c.data == "game_start")
async def start_game(callback: types.CallbackQuery, bot: Bot):
    game = get_cn_game(callback.message.chat.id)
    if not game:
        return await callback.answer("❌ Гра не знайдена")

    t = get_text(game.language)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    game.dark_mode = chat_settings.dark_mode
    game.button_board = chat_settings.button_board
    game.board_size = chat_settings.board_size

    # Save finalized settings to DB for future games
    chat_settings.language = game.language
    chat_settings.last_word_set = game.word_set
    chat_settings.last_reg_timer = game.reg_timer
    chat_settings.last_turn_timer = game.turn_timer
    chat_settings.last_mode = game.metadata.get("mode", "classic")
    chat_settings.board_size = game.board_size
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    if not chat_settings.allow_everyone_start:
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(t.ADMIN_ONLY_ERROR, show_alert=True)

    if len(game.players) < 2:
        return await callback.answer(t.MIN_PLAYERS, show_alert=True)

    start_msg = await game.start()
    board_img = await game.get_board_image(spymaster_view=False)
    kb = await get_game_keyboard(game, bot)

    # Delete redundant join messages for all players
    for player in game.players.values():
        if getattr(player, 'join_msg_id', None):
            try:
                await bot.delete_message(player.user_id, player.join_msg_id)
            except:
                pass

    sent_board = await bot.send_photo(
        callback.message.chat.id,
        photo=BufferedInputFile(board_img.read(), filename="board.png"),
        caption=start_msg,
        reply_markup=kb,
        message_thread_id=game.thread_id,
    )
    game.board_msg_id = sent_board.message_id

    if game.engine.mode == "3p":
        # In 3P mode, there is one shared spymaster
        sm_id = game.spymasters[Team.GREEN]
        sm_img = await game.get_board_image(spymaster_view=True)
        role_msg = t.SPYMASTER_DUAL_ROLE
        
        try:
            chat_id_str = str(game.chat_id)
            if chat_id_str.startswith("-100"):
                link = f"https://t.me/c/{chat_id_str[4:]}/{game.board_msg_id}"
            else:
                link = ""
            btn = types.InlineKeyboardButton(text="🗺 До карти в групі", url=link)
            kb_sm = InlineKeyboardBuilder().row(btn).as_markup() if link else None
            
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
                    role_msg = "🤝 <b>Кооперативний режим </b>\nВаша мета — відгадати всі зелені картки агентів разом з напарником!"
                else:
                    role_msg = t.SPYMASTER_ROLE.format(
                        team=t.TEAM_GREEN if team == Team.GREEN else t.TEAM_RED
                    )
                try:
                    # Create a link back to the group if possible
                    chat_id_str = str(game.chat_id)
                    if chat_id_str.startswith("-100"):
                        link = f"https://t.me/c/{chat_id_str[4:]}/{game.board_msg_id}"
                    else:
                        link = ""
                    btn = types.InlineKeyboardButton(
                        text="🗺 До карти в групі", url=link
                    )
                    kb_sm = (
                        InlineKeyboardBuilder().row(btn).as_markup() if link else None
                    )
    
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

    await callback.message.delete()
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("reveal_"))
async def handle_reveal(callback: types.CallbackQuery, bot: Bot):
    game = get_cn_game(callback.message.chat.id)
    if not game or game.status != "in_progress":
        return await callback.answer()

    t = get_text(game.language)
    idx = int(callback.data.replace("reveal_", ""))

    # Permission logic
    player = game.players.get(callback.from_user.id)
    if not player:
        return await callback.answer(t.NOT_A_PLAYER, show_alert=True)

    current_team = game.engine.current_turn

    if game.engine.mode == "duet":
        giver_id = game.spymasters.get(current_team)
        if not game.engine.clue:
            if callback.from_user.id == giver_id:
                return await callback.answer(
                    "Зараз ваша черга написати підказку!", show_alert=True
                )
            else:
                return await callback.answer(
                    "Зачекайте, поки ваш напарник напише підказку!", show_alert=True
                )
        else:
            if callback.from_user.id == giver_id:
                return await callback.answer(
                    "Зараз черга відгадувати вашого напарника!", show_alert=True
                )
    else:
        if player.role == "spymaster" or player.role == "dual_spymaster":
            return await callback.answer(t.SPYMASTER_GUESS_ERROR, show_alert=True)
        if player.team != current_team.value:
            return await callback.answer(t.NOT_YOUR_TURN, show_alert=True)

    if not game.engine.clue:
        return await callback.answer(t.SPYMASTER_WAIT, show_alert=True)

    turn_before = game.engine.current_turn
    card_word = game.engine.get_board_state(revealed_only=False)[idx]["word"]

    if game.engine.reveal_card(idx):
        await update_main_board(callback.message, game, bot)

        # Send guess result notification
        color_val = game.engine.board[idx].revealed_color
        if game.engine.mode == "duet":
            if color_val == CardColor.GREEN:
                color_name = "🟢 Агент (Зелене)"
            elif color_val == CardColor.ASSASSIN:
                color_name = "💀 Вбивця"
            else:
                color_name = "⚪ Нейтральне"
        else:
            if color_val == CardColor.GREEN:
                color_name = "🟢 Зелена команда"
            elif color_val == CardColor.RED:
                color_name = "🔴 Червона команда"
            elif color_val == CardColor.ASSASSIN:
                color_name = "💀 Вбивця"
            else:
                color_name = "⚪ Нейтральне"

        msg_text = f"👉 <b>{player.full_name}</b>: <b>{card_word.upper()}</b> — <b>{color_name}</b>"
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
            manager.end_game(game.chat_id)
        else:
            turn_after = game.engine.current_turn
            if turn_before != turn_after:
                btn = types.InlineKeyboardButton(
                    text="💡 Дати підказку",
                    switch_inline_query_current_chat=f"hint_{game.chat_id} "
                )
                kb = types.InlineKeyboardMarkup(inline_keyboard=[[btn]])
                
                if game.engine.mode == "duet":
                    giver_id = game.spymasters.get(turn_after)
                    giver_mention = game.players[giver_id].mention if giver_id in game.players else "Напарник"
                    msg_text += f"\n🛑 Хід переходить до: {giver_mention} (дає підказку)!"
                else:
                    team_name = "🔴 Червоних" if turn_after == Team.RED else "🟢 Зелених"
                    if game.language == "en":
                        team_name = "🔴 Red" if turn_after == Team.RED else "🟢 Green"
                    msg_text += f"\n🛑 Хід переходить до команди: <b>{team_name}</b>!"
            else:
                if not game.button_board:
                    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
                        types.InlineKeyboardButton(text="🔍 Обрати слово", switch_inline_query_current_chat=f"reveal_{game.chat_id}")
                    ]])

            await bot.send_message(
                game.chat_id,
                msg_text,
                message_thread_id=game.thread_id,
                reply_markup=kb,
                parse_mode="HTML"
            )

    await callback.answer()


@router.callback_query(lambda c: c.data == "board_pass")
async def handle_pass(callback: types.CallbackQuery, bot: Bot):
    game = get_cn_game(callback.message.chat.id)
    if not game:
        return await callback.answer()

    player = game.players.get(callback.from_user.id)
    is_admin = False
    
    # Check if user is admin in the group
    if callback.message.chat.type in ["group", "supergroup"]:
        try:
            member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
            if member.status in ["administrator", "creator"]:
                is_admin = True
        except Exception:
            pass

    # Allow if it's their turn OR if they are an admin
    is_their_turn = player and player.team == game.engine.current_turn.value
    
    if not is_admin and not is_their_turn:
        return await callback.answer(
            get_text(game.language).NOT_YOUR_TURN, show_alert=True
        )

    # Require double-click confirmation for admin force-skip
    if is_admin and not is_their_turn:
        import time
        now = time.time()
        confirm_data = game.metadata.get("admin_pass_confirm", {})
        
        if confirm_data.get("user_id") != callback.from_user.id or (now - confirm_data.get("time", 0) > 10):
            game.metadata["admin_pass_confirm"] = {"user_id": callback.from_user.id, "time": now}
            return await callback.answer(
                "⚠️ Натисніть «Пас» ще раз протягом 10 секунд, щоб ПРИМУСОВО скіпнути чужий хід (AFK).", 
                show_alert=True
            )
        else:
            # Confirmed within 10 seconds, clear the state
            game.metadata["admin_pass_confirm"] = None

    game.engine.end_turn()
    await update_main_board(callback.message, game, bot)
    
    # Send a notification if an admin force-skipped someone else's turn
    if is_admin and not is_their_turn:
        await bot.send_message(
            game.chat_id,
            f"⚡ Адмін <b>{callback.from_user.full_name}</b> примусово пропустив хід (AFK скіп)!",
            message_thread_id=game.thread_id,
            parse_mode="HTML"
        )
    await callback.answer()


@router.inline_query(lambda q: q.query.startswith("hint_"))
async def inline_hint(query: InlineQuery):
    try:
        chat_id = int(query.query.split("_")[1].split(" ")[0])
    except (IndexError, ValueError):
        return

    game = get_cn_game(chat_id)
    if not game:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"hint_no_game",
                    title="Гра не знайдена або вже завершена",
                    description="Створіть нову гру за допомогою /codenames",
                    input_message_content=InputTextMessageContent(
                        message_text="Гра вже завершена. Створіть нову гру за допомогою /codenames"
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
                        message_text=f"/cn_join {chat_id}"
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
                        message_text="Я чекаю своєї черги."
                    ),
                )
            ],
            cache_time=1,
        )

    parts = query.query.strip().split(" ")

    if len(parts) >= 3:
        word = parts[1]
        count = parts[2]
        if count.isdigit():
            if game.button_board:
                chat_id_str = str(chat_id)
                if chat_id_str.startswith("-100") and game.board_msg_id:
                    link = f"https://t.me/c/{chat_id_str[4:]}/{game.board_msg_id}"
                else:
                    link = f"https://t.me/{query.bot.username}" if query.bot else ""
                
                kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🗺️ До карти", url=link)]
                ]) if link else None
            else:
                kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔍 Обрати слово", switch_inline_query_current_chat=f"reveal_{chat_id}")]
                ])


            await query.answer(
                [
                    InlineQueryResultArticle(
                        id=f"hint_{chat_id}",
                        title=t.INLINE_VALID_HINT_TITLE.format(word=word, count=count),
                        input_message_content=InputTextMessageContent(
                            message_text=f"📢 Підказка: <b>{word.upper()}</b> {count}",
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
                        message_text=f"Введіть число після слова {word}"
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
                        message_text=f"Введіть слово та число через пробіл"
                    ),
                )
            ],
            cache_time=1,
        )


@router.inline_query(lambda q: q.query.startswith("reveal_"))
async def inline_reveal(query: InlineQuery):
    try:
        chat_id = int(query.query.split("_")[1].split(" ")[0])
    except (IndexError, ValueError):
        return

    game = get_cn_game(chat_id)
    if not game:
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"reveal_no_game",
                    title="Гра не знайдена або вже завершена",
                    description="Створіть нову гру за допомогою /codenames",
                    input_message_content=InputTextMessageContent(
                        message_text="Гра вже завершена. Створіть нову гру за допомогою /codenames"
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
                        message_text=f"/cn_join {chat_id}"
                    ),
                )
            ],
            cache_time=1,
        )

    current_team = game.engine.current_turn
    if game.engine.mode != "duet" and (
        player.role == "spymaster" or player.role == "dual_spymaster"
    ):
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"reveal_spymaster_{chat_id}",
                    title=t.SPYMASTER_GUESS_ERROR,
                    description="Капітани не можуть обирати слова.",
                    input_message_content=InputTextMessageContent(
                        message_text="Я лише капітан."
                    ),
                )
            ],
            cache_time=1,
        )

    if player.team != current_team.value and game.engine.mode != "duet":
        return await query.answer(
            [
                InlineQueryResultArticle(
                    id=f"reveal_not_turn_{chat_id}",
                    title=t.NOT_YOUR_TURN,
                    description=t.NOT_YOUR_TURN_DESC,
                    input_message_content=InputTextMessageContent(
                        message_text="Я чекаю своєї черги."
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
                    title="Зачекайте",
                    description=t.SPYMASTER_WAIT,
                    input_message_content=InputTextMessageContent(
                        message_text="Чекаю на підказку."
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
                        message_text=f"🔎 Обрано слово: <b>{card.word.upper()}</b>",
                        parse_mode="HTML"
                    ),
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔍 Обрати слово", switch_inline_query_current_chat=f"reveal_{chat_id}")]
                    ])
                )
            )

    if not results:
        results.append(
            InlineQueryResultArticle(
                id=f"reveal_not_found_{chat_id}",
                title="Не знайдено",
                description="Слово не знайдено на дошці",
                input_message_content=InputTextMessageContent(message_text="..."),
            )
        )

    # Telegram inline queries are limited to 50 results, we have at most 25
    await query.answer(results, cache_time=1)


@router.message(lambda m: m.text and (m.text.startswith("🔎 Обрано слово: ") or m.text.startswith("REVEAL: ")))
async def process_reveal_text(message: types.Message, bot: Bot):
    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
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
    if game.engine.mode != "duet" and (
        player.role == "spymaster" or player.role == "dual_spymaster"
    ):
        return

    if player.team != current_team.value and game.engine.mode != "duet":
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
                color_name = "🟢 Агент (Зелене)"
            elif color_val == CardColor.ASSASSIN:
                color_name = "💀 Вбивця"
            else:
                color_name = "⚪ Нейтральне"
        else:
            if color_val == CardColor.GREEN:
                color_name = "🟢 Зелена команда"
            elif color_val == CardColor.RED:
                color_name = "🔴 Червона команда"
            elif color_val == CardColor.ASSASSIN:
                color_name = "💀 Вбивця"
            else:
                color_name = "⚪ Нейтральне"

        msg_text = f"👉 <b>{player.full_name}</b>: <b>{card_word.upper()}</b> — <b>{color_name}</b>"
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
            manager.end_game(game.chat_id)
        else:
            turn_after = game.engine.current_turn
            if turn_before != turn_after:
                btn = types.InlineKeyboardButton(
                    text="💡 Дати підказку",
                    switch_inline_query_current_chat=f"hint_{game.chat_id} "
                )
                kb = types.InlineKeyboardMarkup(inline_keyboard=[[btn]])
                
                if game.engine.mode == "duet":
                    giver_id = game.spymasters.get(turn_after)
                    giver_mention = game.players[giver_id].mention if giver_id in game.players else "Напарник"
                    msg_text += f"\n🛑 Хід переходить до: {giver_mention} (дає підказку)!"
                else:
                    team_name = "🔴 Червоних" if turn_after == Team.RED else "🟢 Зелених"
                    if game.language == "en":
                        team_name = "🔴 Red" if turn_after == Team.RED else "🟢 Green"
                    msg_text += f"\n🛑 Хід переходить до команди: <b>{team_name}</b>!"
            else:
                if not game.button_board:
                    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
                        types.InlineKeyboardButton(text="🔍 Обрати слово", switch_inline_query_current_chat=f"reveal_{game.chat_id}")
                    ]])

            await bot.send_message(
                game.chat_id,
                msg_text,
                message_thread_id=game.thread_id,
                reply_markup=kb,
                parse_mode="HTML"
            )

    try:
        await message.delete()
    except Exception:
        pass


@router.message(lambda m: m.text and (m.text.startswith("📢 Підказка: ") or m.text.startswith("HINT: ")))
async def process_hint_text(message: types.Message, bot: Bot):
    # This captures the spymaster's hint sent via inline
    game = get_cn_game(message.chat.id)
    if not game:
        return

    user_id = message.from_user.id
    player = game.players.get(user_id)
    if not player:
        return

    is_turn = game.spymasters.get(game.engine.current_turn) == user_id
    if not is_turn:
        return

    clean_text = message.text
    if clean_text.startswith("📢 Підказка: "):
        clean_text = clean_text.replace("📢 Підказка: ", "")
    else:
        clean_text = clean_text.replace("HINT: ", "")

    parts = clean_text.strip().split(" ")
    if len(parts) == 2:
        word, count = parts[0], int(parts[1])
        game.engine.set_clue(word, count)
        await update_main_board(message, game, bot)



@router.callback_query(F.data == "none")
async def cb_none(callback: types.CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "game_shop")
async def cb_game_shop(callback: types.CallbackQuery, bot: Bot):
    game = get_cn_game(callback.message.chat.id)
    if not game:
        return await callback.answer("❌ Гра не знайдена або вже завершена! Створіть нову.", show_alert=True)

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

    kb.row(types.InlineKeyboardButton(text="❌ Закрити", callback_data="none"))

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
        await callback.answer(
            "Відправив меню бафів вам в особисті повідомлення!", show_alert=True
        )
    except Exception:
        await callback.answer(
            "❌ Спочатку почніть діалог з ботом в особистих повідомленнях!", show_alert=True
        )

@router.message(Command("buffs"))
async def cmd_game_buffs(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        return await message.answer("🎮 Будь ласка, використовуйте команду /buffs у групі, де йде гра!")

    game = get_cn_game(message.chat.id)
    if not game or game.status != "in_progress":
        return await message.answer("❌ Зараз немає активної гри у цьому чаті!")

    t = get_text(game.language)
    player = game.players.get(message.from_user.id)
    if not player:
        return await message.answer(t.NOT_A_PLAYER)

    balance = await db_service.get_user_diamonds(message.from_user.id)

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

    kb.row(types.InlineKeyboardButton(text="❌ Закрити", callback_data="none"))

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
            message.from_user.id, text, reply_markup=kb.as_markup(), parse_mode="HTML"
        )
        await message.answer("📨 Надіслав вам меню бафів в особисті повідомлення!")
    except Exception:
        await message.answer(t.SPYMASTER_DM_ERROR.format(mention=player.mention))


@router.callback_query(F.data.startswith("buy_buff_"))
async def process_buy_buff(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    chat_id = int(parts[2])
    buff_type = parts[3]

    game = get_cn_game(chat_id)
    if not game or game.status != "in_progress":
        return await callback.answer("Гра не знайдена або завершена", show_alert=True)

    t = get_text(game.language)
    player = game.players.get(callback.from_user.id)
    if not player:
        return await callback.answer(t.NOT_A_PLAYER, show_alert=True)

    team = Team(player.team)
    if game.engine.current_turn != team and game.engine.mode != "duet":
        return await callback.answer(t.NOT_YOUR_TURN, show_alert=True)

    balance = await db_service.get_user_diamonds(callback.from_user.id)
    prices = {
        "armor": t.BUFF_ARMOR_PRICE,
        "intercept": t.BUFF_INTERCEPT_PRICE,
        "detector": t.BUFF_DETECTOR_PRICE,
        "remap": t.BUFF_REMAP_PRICE,
        "reveal": 200,
    }

    price = prices.get(buff_type, 9999)
    if balance < price:
        return await callback.answer(t.BUY_FAIL, show_alert=True)

    # Apply buff logic
    success = False
    result_msg = ""
    team_name = "🟢 Зелених" if team == Team.GREEN else "🔴 Червоних"
    if game.language == "en":
        team_name = "🟢 Green" if team == Team.GREEN else "🔴 Red"

    if buff_type == "armor":
        if team in game.engine.team_armor:
            return await callback.answer(t.BUFF_USED_ERROR, show_alert=True)
        game.engine.team_armor.append(team)
        success = True
        result_msg = f"🛡 Команда <b>{team_name}</b> застосувала {t.BUFF_ARMOR_NAME}!"

    elif buff_type == "intercept":
        if team in game.engine.team_interception:
            return await callback.answer(t.BUFF_USED_ERROR, show_alert=True)
        game.engine.team_interception.append(team)
        success = True
        result_msg = (
            f"⚡ Команда <b>{team_name}</b> застосувала {t.BUFF_INTERCEPT_NAME}!"
        )

    elif buff_type == "detector":
        word = game.engine.use_buff_detector()
        if word:
            success = True
            result_msg = (
                f"📡 {t.BUFF_DETECTOR_NAME} виявив нейтральне слово: <b>{word}</b>!"
            )
        else:
            return await callback.answer(t.BUFF_NOT_AVAILABLE, show_alert=True)

    elif buff_type == "reveal":
        word = game.engine.use_buff_reveal()
        if word:
            success = True
            result_msg = t.REVEAL_BUFF_RESULT.format(word=word)
        else:
            return await callback.answer(t.BUFF_NOT_AVAILABLE, show_alert=True)

    elif buff_type == "remap":
        if game.engine.use_buff_replace_all():
            success = True
            result_msg = f"🗺 <b>{player.full_name}</b> використав баф {t.BUFF_REMAP_NAME} і змінив всі слова на полі!"
        else:
            return await callback.answer(
                "Цей баф можна використати ТІЛЬКИ до відкриття першого слова!",
                show_alert=True,
            )

    if success:
        # Deduct diamonds
        await db_service.update_user_diamonds(callback.from_user.id, -price)
        await callback.answer(t.BUY_SUCCESS, show_alert=True)

        # Send group notification
        await bot.send_message(
            chat_id, result_msg, message_thread_id=game.thread_id, parse_mode="HTML"
        )

        # Update board if it was a reveal or remap action
        if buff_type in ["detector", "reveal", "remap"]:
            await update_main_board(callback.message, game, bot)
        # Delete PM menu message
        try:
            await callback.message.delete()
        except:
            pass
