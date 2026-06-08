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
        and message.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ADMIN_ONLY_ERROR)

    existing_game = manager.get_game(message.chat.id)
    if existing_game:
        return await message.answer(
            t.GAME_ALREADY_STARTED or "Гра вже триває або лоббі вже створене!"
        )

    game = manager.create_game(
        message.chat.id, CodeNamesGame, message.message_thread_id
    )
    game.language = chat_settings.language
    game.word_set = chat_settings.last_word_set
    game.reg_timer = chat_settings.last_reg_timer
    game.turn_timer = chat_settings.last_turn_timer
    game.metadata["mode"] = chat_settings.last_mode
    game.dark_mode = chat_settings.dark_mode
    game.button_board = chat_settings.button_board
    game.board_size = chat_settings.board_size
    game.pin_message = chat_settings.pin_message
    game.metadata["spymaster_sheet"] = chat_settings.spymaster_sheet
    game.metadata["show_past_clues"] = chat_settings.show_past_clues
    game.metadata["strict_clues"] = chat_settings.strict_clues
    game.metadata["allow_pass"] = chat_settings.allow_pass

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
        except Exception:
            pass

    asyncio.create_task(game.start_reg_timer(bot))