from typing import Any
import asyncio
from aiogram import Router, types, Bot, F
from aiogram.filters import Command, CommandObject
from src.core.platform.game_manager import manager
from src.games.codenames.game import CodeNamesGame
from src.core.platform.base_game import GamePlayer
from src.core.database.service import db_service
from src.assets.texts import get_text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from src.core.utils.logging import send_log

logger = logging.getLogger(__name__)


class FeedbackState(StatesGroup):
    waiting_for_feedback = State()


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
        # Assign team if joining mid-game
        if game.status == "in_progress":
            if game.metadata.get("mode", "Classic").lower() != "duet":
                # Count agents and spymasters per team, assign to the team with fewer players
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
                # Duet mode mid-game join: balance between Side A (green) and Side B (red)
                green_count = sum(1 for p in game.players.values() if p.team == "green")
                red_count = sum(1 for p in game.players.values() if p.team == "red")
                if green_count <= red_count:
                    player.team = "green"
                else:
                    player.team = "red"
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

        # Customize JOIN_SUCCESS message
        if game.status == "in_progress":
            if game.metadata.get("mode", "Classic").lower() == "duet":
                join_msg = (
                    "✅ Ви приєдналися до гри у кооперативному режимі (Duet)!"
                    if settings.language == "uk"
                    else "✅ You joined the game in cooperative mode (Duet)!"
                )
            else:
                team_display = "Зеленої 🟢" if player.team == "green" else "Червоної 🔴"
                if settings.language != "uk":
                    team_display = "Green 🟢" if player.team == "green" else "Red 🔴"
                join_msg = (
                    f"✅ Ви приєдналися до {team_display} команди!"
                    if settings.language == "uk"
                    else f"✅ You joined the {team_display} team!"
                )
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
                    f"➕ 🤝 {player.full_name} приєднався до кооперативної гри!"
                    if settings.language == "uk"
                    else f"➕ 🤝 {player.full_name} joined the cooperative game!",
                    message_thread_id=game.thread_id,
                )
            else:
                team_emoji = "🟢" if player.team == "green" else "🔴"
                team_name = "Зеленої" if player.team == "green" else "Червоної"
                if settings.language != "uk":
                    team_name = "Green" if player.team == "green" else "Red"
                await bot.send_message(
                    chat_id,
                    f"➕ {team_emoji} {player.full_name} приєднався до {team_name} команди!"
                    if settings.language == "uk"
                    else f"➕ {team_emoji} {player.full_name} joined the {team_name} team!",
                    message_thread_id=game.thread_id,
                )
        else:
            await update_registration_view(bot, chat_id, game)
    else:
        await message.answer(t.ALREADY_JOINED)


from aiogram.utils.keyboard import InlineKeyboardBuilder
import random

SPY_QUOTES_UK = [
    "«Шпигун — це не професія, це спосіб життя.»",
    "«У шпигунстві немає випадкових людей, є лише непомітні.»",
    "«Найкраща зброя агента — це інформація.»",
    "«Точність — це наша ввічливість, скритність — наш девіз.»",
    "«Ми діємо в тіні, щоб служити світлу.»",
    "«Справжній майстер кодових імен бачить зв'язки там, де інші бачать хаос.»",
    "«Тиша — найкращий союзник шпигуна.»",
]

SPY_QUOTES_EN = [
    "“A spy is not a profession, it is a way of life.”",
    "“In espionage, there are no accidental people, only invisible ones.”",
    "“The agent's best weapon is information.”",
    "“Accuracy is our politeness, stealth is our motto.”",
    "“We work in the dark to serve the light.”",
    "“A true master of codenames sees connections where others see chaos.”",
    "“Silence is a spy's best ally.”",
]


async def show_profile_message(
    user_id: int, full_name: str, username: str, lang: str = "uk"
):
    stats = await db_service.get_user_stats(user_id)
    c_stats = await db_service.get_user_combat_stats(user_id)
    balance = await db_service.get_user_diamonds(user_id)
    coins = await db_service.get_user_coins(user_id)
    inv = await db_service.get_user_inventory(user_id)

    wins = stats.wins or 0 if stats else 0
    losses = stats.losses or 0 if stats else 0
    total = stats.total if stats else 0
    winrate = (wins / total * 100) if total > 0 else 0

    guessed_words = c_stats["guessed_words"]
    assassins_hit = c_stats["assassins_hit"]
    opponent_words_hit = c_stats["opponent_words_hit"]

    xp = wins * 100 + losses * 40
    level = int(xp / 300) + 1
    next_level_xp = level * 300
    prev_level_xp = (level - 1) * 300
    level_progress_xp = xp - prev_level_xp
    xp_needed = 300
    percentage = int(level_progress_xp / xp_needed * 100)

    filled = int(percentage / 10)
    progress_bar = "║" + "█" * filled + "░" * (10 - filled) + f"║ {percentage}%"

    t = get_text(lang)

    codename = f"@{username}" if username else full_name
    quote = random.choice(SPY_QUOTES_UK if lang == "uk" else SPY_QUOTES_EN)

    if lang == "uk":
        text = (
            f"👤 <b>ОСОБОВА СПРАВА АГЕНТА:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote>🔓 <b>Кодовий позивний:</b> {codename}\n"
            f"💎 <b>Баланс (Діаманти):</b> <code>{balance}</code> 💎\n"
            f"🪙 <b>Баланс (Монети):</b> <code>{coins}</code> 🪙\n"
            f"🎖 <b>Рівень:</b> {level}\n"
            f"{progress_bar}\n"
            f"✨ <i>До наступного рівня: {level_progress_xp}/{xp_needed} XP</i></blockquote>\n\n"
            f"📊 <b>БОЙОВА СТАТИСТИКА:</b>\n"
            f"<blockquote>├─ 🎮 Всього ігор: <b>{total}</b>\n"
            f"├─ 🏆 Перемоги: <b>{wins}</b>\n"
            f"├─ 💀 Поразки: <b>{losses}</b>\n"
            f"├─ 💯 Вінрейт: <b>{winrate:.1f}%</b>\n"
            f"├─ 🎯 Вгадано слів: <b>{guessed_words}</b>\n"
            f"├─ 💀 Обрано вбивць: <b>{assassins_hit}</b>\n"
            f"└─ 💥 Слів чужої команди: <b>{opponent_words_hit}</b></blockquote>\n\n"
            f"🎒 <b>СПЕЦ-ІНВЕНТАР (БАФИ):</b>\n"
            f"<blockquote>├─ {t.BUFF_ARMOR_NAME}: <b>{inv.get('armor', 0)}</b>\n"
            f"├─ {t.BUFF_INTERCEPT_NAME}: <b>{inv.get('intercept', 0)}</b>\n"
            f"├─ {t.BUFF_DETECTOR_NAME}: <b>{inv.get('detector', 0)}</b>\n"
            f"├─ {t.REVEAL_BUFF_NAME.split('(')[0].strip()}: <b>{inv.get('reveal', 0)}</b>\n"
            f"├─ {t.BUFF_REMAP_NAME}: <b>{inv.get('remap', 0)}</b>\n"
            f"├─ {t.BUFF_AVOID_CAPTAIN_NAME}: <b>{inv.get('avoid_captain', 0)}</b>\n"
            f"└─ {t.BUFF_BECOME_CAPTAIN_NAME}: <b>{inv.get('become_captain', 0)}</b></blockquote>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💬 <i>{quote}</i>"
        )
    else:
        text = (
            f"👤 <b>AGENT DOSSIER:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote>🔓 <b>Code Name:</b> {codename}\n"
            f"💎 <b>Diamonds:</b> <code>{balance}</code> 💎\n"
            f"🪙 <b>Coins:</b> <code>{coins}</code> 🪙\n"
            f"🎖 <b>Level:</b> {level}\n"
            f"{progress_bar}\n"
            f"✨ <i>Next Level in: {level_progress_xp}/{xp_needed} XP</i></blockquote>\n\n"
            f"📊 <b>COMBAT STATS:</b>\n"
            f"<blockquote>├─ 🎮 Total Games: <b>{total}</b>\n"
            f"├─ 🏆 Wins: <b>{wins}</b>\n"
            f"├─ 💀 Losses: <b>{losses}</b>\n"
            f"├─ 💯 Win Rate: <b>{winrate:.1f}%</b>\n"
            f"├─ 🎯 Guessed Words: <b>{guessed_words}</b>\n"
            f"├─ 💀 Hit Assassins: <b>{assassins_hit}</b>\n"
            f"└─ 💥 Opponent Words: <b>{opponent_words_hit}</b></blockquote>\n\n"
            f"🎒 <b>SPECIAL INVENTORY (BUFFS):</b>\n"
            f"<blockquote>├─ {t.BUFF_ARMOR_NAME}: <b>{inv.get('armor', 0)}</b> pcs.\n"
            f"├─ {t.BUFF_INTERCEPT_NAME}: <b>{inv.get('intercept', 0)}</b> pcs.\n"
            f"├─ {t.BUFF_DETECTOR_NAME}: <b>{inv.get('detector', 0)}</b> pcs.\n"
            f"├─ {t.REVEAL_BUFF_NAME.split('(')[0].strip()}: <b>{inv.get('reveal', 0)}</b> pcs.\n"
            f"├─ {t.BUFF_REMAP_NAME}: <b>{inv.get('remap', 0)}</b> pcs.\n"
            f"├─ {t.BUFF_AVOID_CAPTAIN_NAME}: <b>{inv.get('avoid_captain', 0)}</b> pcs.\n"
            f"└─ {t.BUFF_BECOME_CAPTAIN_NAME}: <b>{inv.get('become_captain', 0)}</b> pcs.</blockquote>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💬 <i>{quote}</i>"
        )

    kb = InlineKeyboardBuilder()
    if lang == "uk":
        kb.row(
            types.InlineKeyboardButton(
                text="👑 Бафи капітана", callback_data="profile_captain_buffs"
            ),
        )
        kb.row(
            types.InlineKeyboardButton(
                text="🛒 Купити Бафи", callback_data="profile_shop_buffs"
            ),
            types.InlineKeyboardButton(
                text="💎 Купити Алмази", callback_data="profile_shop_diamonds"
            ),
        )
        kb.row(
            types.InlineKeyboardButton(text="❌ Закрити", callback_data="profile_close")
        )
    else:
        kb.row(
            types.InlineKeyboardButton(
                text="👑 Captain Buffs", callback_data="profile_captain_buffs"
            ),
        )
        kb.row(
            types.InlineKeyboardButton(
                text="🛒 Buy Buffs", callback_data="profile_shop_buffs"
            ),
            types.InlineKeyboardButton(
                text="💎 Buy Diamonds", callback_data="profile_shop_diamonds"
            ),
        )
        kb.row(
            types.InlineKeyboardButton(text="❌ Close", callback_data="profile_close")
        )

    return text, kb.as_markup()


@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, bot: Bot):
    if command.args and command.args.startswith("join_"):
        chat_id = int(command.args.replace("join_", ""))
        return await process_join_game(message, chat_id, bot)

    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)

    kb = InlineKeyboardBuilder()
    if settings.language == "uk":
        kb.row(
            types.InlineKeyboardButton(
                text="👤 Мій Профіль", callback_data="profile_back"
            ),
            types.InlineKeyboardButton(
                text="💎 Магазин Алмазів", callback_data="profile_shop_diamonds"
            ),
        )
    else:
        kb.row(
            types.InlineKeyboardButton(
                text="👤 My Profile", callback_data="profile_back"
            ),
            types.InlineKeyboardButton(
                text="💎 Diamond Shop", callback_data="profile_shop_diamonds"
            ),
        )

    await message.answer(t.WELCOME, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.message(Command("cn_join"))
async def cmd_cn_join(message: types.Message, command: CommandObject, bot: Bot):
    if not command.args:
        return
    try:
        chat_id = int(command.args)
    except ValueError:
        return

    await process_join_game(message, chat_id, bot)
    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("profile", "stats"))
async def cmd_profile(message: types.Message, bot: Bot):
    settings = await db_service.get_chat_settings(message.chat.id)
    lang = settings.language
    t = get_text(lang)

    if message.chat.type != "private":
        try:
            text, markup = await show_profile_message(
                message.from_user.id,
                message.from_user.full_name,
                message.from_user.username,
                lang,
            )
            await bot.send_message(
                message.from_user.id, text, reply_markup=markup, parse_mode="HTML"
            )
            sent = await message.answer(
                "📨 Надіслав вам профіль в особисті повідомлення!"
            )

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

            asyncio.create_task(delete_after(7))
        except Exception:
            await message.answer(
                t.SPYMASTER_DM_ERROR.format(mention=message.from_user.mention)
            )
    else:
        text, markup = await show_profile_message(
            message.from_user.id,
            message.from_user.full_name,
            message.from_user.username,
            lang,
        )
        await message.answer(text, reply_markup=markup, parse_mode="HTML")


@router.callback_query(F.data == "profile_back")
async def profile_back(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    text, markup = await show_profile_message(
        callback.from_user.id,
        callback.from_user.full_name,
        callback.from_user.username,
        lang,
    )
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")


@router.callback_query(F.data == "profile_close")
async def profile_close(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass


@router.callback_query(F.data == "profile_shop_buffs")
async def profile_shop_buffs(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    t = get_text(lang)
    balance = await db_service.get_user_diamonds(callback.from_user.id)
    coins = await db_service.get_user_coins(callback.from_user.id)
    inv = await db_service.get_user_inventory(callback.from_user.id)

    kb = InlineKeyboardBuilder()

    # Buff shop: left button = name + count (buy with coins), right button = price (buy with diamonds)
    buffs_config = [
        ("armor", t.BUFF_ARMOR_NAME, t.BUFF_ARMOR_DESC, inv.get('armor', 0), t.BUFF_ARMOR_PRICE, 175),
        ("intercept", t.BUFF_INTERCEPT_NAME, t.BUFF_INTERCEPT_DESC, inv.get('intercept', 0), t.BUFF_INTERCEPT_PRICE, 125),
        ("detector", t.BUFF_DETECTOR_NAME, t.BUFF_DETECTOR_DESC, inv.get('detector', 0), t.BUFF_DETECTOR_PRICE, 75),
        ("reveal", t.BUFF_REVEAL_SHORT, t.REVEAL_BUFF_NAME, inv.get('reveal', 0), 20, 100),
        ("remap", t.BUFF_REMAP_NAME, t.BUFF_REMAP_DESC, inv.get('remap', 0), t.BUFF_REMAP_PRICE, 50),
        ("become_captain", t.BUFF_BECOME_CAPTAIN_SHORT, t.BUFF_BECOME_CAPTAIN_DESC, inv.get('become_captain', 0), t.BUFF_BECOME_CAPTAIN_PRICE, t.BUFF_BECOME_CAPTAIN_PRICE_COINS),
        ("avoid_captain", t.BUFF_AVOID_CAPTAIN_SHORT, t.BUFF_AVOID_CAPTAIN_DESC, inv.get('avoid_captain', 0), t.BUFF_AVOID_CAPTAIN_PRICE, t.BUFF_AVOID_CAPTAIN_PRICE_COINS),
    
    ]

    for btype, bname, bdesc, bcount, pdia, pcoin in buffs_config:
        left_cb = f"buy_inv_buff_{btype}_coin"
        right_cb = f"buy_inv_buff_{btype}_dia"
        kb.row(
            types.InlineKeyboardButton(
                text=f"{bname}: {bcount} — {pcoin}🪙",
                callback_data=left_cb,
            ),
            types.InlineKeyboardButton(
                text=f"{pdia}💎",
                callback_data=right_cb,
            ),
        )

    if lang == "uk":
        kb.row(
            types.InlineKeyboardButton(
                text="🔙 Назад до профілю", callback_data="profile_back"
            )
        )
        text = (
            f"🛒 <b>МАГАЗИН БАФІВ</b>\n\n"
            f"💎 Діаманти: <b>{balance}</b>\n"
            f"🪙 Монети: <b>{coins}</b>\n\n"
            f"<b>{t.BUFF_ARMOR_NAME}</b> — {t.BUFF_ARMOR_PRICE}💎 / 175🪙\n"
            f"<blockquote>{t.BUFF_ARMOR_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_INTERCEPT_NAME}</b> — {t.BUFF_INTERCEPT_PRICE}💎 / 125🪙\n"
            f"<blockquote>{t.BUFF_INTERCEPT_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_DETECTOR_NAME}</b> — {t.BUFF_DETECTOR_PRICE}💎 / 75🪙\n"
            f"<blockquote>{t.BUFF_DETECTOR_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_REVEAL_SHORT}</b> — 20💎 / 100🪙\n"
            f"<blockquote>{t.REVEAL_BUFF_NAME}</blockquote>\n\n"
            f"<b>{t.BUFF_REMAP_NAME}</b> — {t.BUFF_REMAP_PRICE}💎 / 50🪙\n"
            f"<blockquote>{t.BUFF_REMAP_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_BECOME_CAPTAIN_SHORT}</b> — {t.BUFF_BECOME_CAPTAIN_PRICE}💎 / {t.BUFF_BECOME_CAPTAIN_PRICE_COINS}🪙\n"
            f"<blockquote>{t.BUFF_BECOME_CAPTAIN_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_AVOID_CAPTAIN_SHORT}</b> — {t.BUFF_AVOID_CAPTAIN_PRICE}💎 / {t.BUFF_AVOID_CAPTAIN_PRICE_COINS}🪙\n"
            f"<blockquote>{t.BUFF_AVOID_CAPTAIN_DESC}</blockquote>"
        )
    else:
        kb.row(
            types.InlineKeyboardButton(
                text="🔙 Back to Profile", callback_data="profile_back"
            )
        )
        text = (
            f"🛒 <b>BUFF SHOP</b>\n\n"
            f"💎 Diamonds: <b>{balance}</b>\n"
            f"🪙 Coins: <b>{coins}</b>\n\n"
            f"<b>{t.BUFF_ARMOR_NAME}</b> — {t.BUFF_ARMOR_PRICE}💎 / 175🪙\n"
            f"<blockquote>{t.BUFF_ARMOR_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_INTERCEPT_NAME}</b> — {t.BUFF_INTERCEPT_PRICE}💎 / 125🪙\n"
            f"<blockquote>{t.BUFF_INTERCEPT_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_DETECTOR_NAME}</b> — {t.BUFF_DETECTOR_PRICE}💎 / 75🪙\n"
            f"<blockquote>{t.BUFF_DETECTOR_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_REVEAL_SHORT}</b> — 20💎 / 100🪙\n"
            f"<blockquote>{t.REVEAL_BUFF_NAME}</blockquote>\n\n"
            f"<b>{t.BUFF_REMAP_NAME}</b> — {t.BUFF_REMAP_PRICE}💎 / 50🪙\n"
            f"<blockquote>{t.BUFF_REMAP_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_BECOME_CAPTAIN_SHORT}</b> — {t.BUFF_BECOME_CAPTAIN_PRICE}💎 / {t.BUFF_BECOME_CAPTAIN_PRICE_COINS}🪙\n"
            f"<blockquote>{t.BUFF_BECOME_CAPTAIN_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_AVOID_CAPTAIN_SHORT}</b> — {t.BUFF_AVOID_CAPTAIN_PRICE}💎 / {t.BUFF_AVOID_CAPTAIN_PRICE_COINS}🪙\n"
            f"<blockquote>{t.BUFF_AVOID_CAPTAIN_DESC}</blockquote>"
        )

    await callback.message.edit_text(
        text, reply_markup=kb.as_markup(), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("buy_inv_buff_"))
async def buy_inv_buff(callback: types.CallbackQuery):
    data = callback.data.replace("buy_inv_buff_", "")
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    t = get_text(lang)

    # Format: bufftype_currency (e.g. armor_coin, avoid_captain_dia)
    # Use rsplit to handle buff types with underscores
    parts = data.rsplit("_", 1)
    if len(parts) < 2:
        return
    buff_type = parts[0]
    currency = parts[1]  # "dia" or "coin"

    prices_dia = {
        "armor": t.BUFF_ARMOR_PRICE,
        "intercept": t.BUFF_INTERCEPT_PRICE,
        "detector": t.BUFF_DETECTOR_PRICE,
        "reveal": 20,
        "remap": t.BUFF_REMAP_PRICE,
        "avoid": t.BUFF_AVOID_CAPTAIN_PRICE,
        "become": t.BUFF_BECOME_CAPTAIN_PRICE,
    }

    prices_coin = {
        "armor": 175,
        "intercept": 125,
        "detector": 75,
        "reveal": 100,
        "remap": 50,
        "avoid": t.BUFF_AVOID_CAPTAIN_PRICE_COINS,
        "become": t.BUFF_BECOME_CAPTAIN_PRICE_COINS,
    }

    # Map short buff_type to full column name for avoid/become
    buff_column = buff_type
    if buff_type == "avoid":
        buff_column = "avoid_captain"
    elif buff_type == "become":
        buff_column = "become_captain"

    if currency == "dia":
        price = prices_dia.get(buff_type, 9999)
        balance = await db_service.get_user_diamonds(callback.from_user.id)
        if balance < price:
            return await callback.answer(t.BUY_FAIL, show_alert=True)
        await db_service.update_user_diamonds(callback.from_user.id, -price)
    else:
        price = prices_coin.get(buff_type, 9999)
        balance = await db_service.get_user_coins(callback.from_user.id)
        if balance < price:
            return await callback.answer(t.BUY_FAIL, show_alert=True)
        await db_service.update_user_coins(callback.from_user.id, -price)

    await db_service.update_user_buff(callback.from_user.id, buff_column, 1)

    await callback.answer(t.BUY_SUCCESS)
    await profile_shop_buffs(callback)


@router.callback_query(F.data == "profile_shop_diamonds")
async def profile_shop_diamonds(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    t = get_text(lang)
    balance = await db_service.get_user_diamonds(callback.from_user.id)

    from src.bot.handlers.shop import PACKS

    kb = InlineKeyboardBuilder()
    for key, pack in PACKS.items():
        kb.row(
            types.InlineKeyboardButton(
                text=f"💎 {pack['amount']} — {pack['price_uah']} UAH / {pack['price_stars']} 🌟",
                callback_data=f"shop_pack_{key}",
            )
        )

    if lang == "uk":
        kb.row(
            types.InlineKeyboardButton(
                text="🔙 Назад до профілю", callback_data="profile_back"
            )
        )
        text = (
            f"💎 <b>МАГАЗИН АЛМАЗІВ:</b>\n"
            f"🛒 Баланс: <b>{balance}</b> алмазів\n\n"
            f"Оберіть пакет алмазів для придбання:"
        )
    else:
        kb.row(
            types.InlineKeyboardButton(
                text="🔙 Back to Profile", callback_data="profile_back"
            )
        )
        text = (
            f"💎 <b>DIAMOND SHOP:</b>\n"
            f"🛒 Balance: <b>{balance}</b> diamonds\n\n"
            f"Select a package to buy:"
        )
    await callback.message.edit_text(
        text, reply_markup=kb.as_markup(), parse_mode="HTML"
    )


@router.message(Command("feedback"))
async def cmd_feedback(message: types.Message, state: FSMContext):
    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t.FINISH_FEEDBACK_BTN, callback_data="finish_feedback"
                )
            ]
        ]
    )

    await message.answer(t.FEEDBACK_SESSION_STARTED, reply_markup=kb)
    await state.set_state(FeedbackState.waiting_for_feedback)


@router.callback_query(lambda c: c.data == "finish_feedback")
async def cb_finish_feedback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("✅ Режим фідбеку завершено. Дякуємо!")
    await callback.answer()


@router.message(Command("done"), FeedbackState.waiting_for_feedback)
async def cmd_done_feedback(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Режим фідбеку завершено. Дякуємо!")


@router.message(FeedbackState.waiting_for_feedback)
async def process_feedback_ticket(message: types.Message, state: FSMContext, bot: Bot):
    import time

    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)

    # Smart anti-spam check
    data = await state.get_data()
    last_msg_time = data.get("last_msg_time", 0)
    msg_count = data.get("msg_count", 0)

    now = time.time()
    if msg_count >= 10 and now - last_msg_time < 1.5:
        # Only apply cooldown after first 10 messages to allow media groups/forwards
        return await message.answer(t.FEEDBACK_TOO_FAST)

    if msg_count >= 50:  # Increased total cap to 50
        return await message.answer(t.FEEDBACK_LIMIT_REACHED)

    # Check admin log configuration
    log_cfg = await db_service.get_system_setting("log_settings")
    dest = log_cfg.get("destination")
    if not dest or "feedback" not in log_cfg.get("enabled_types", []):
        return await message.answer("⚠️ Функція фідбеку тимчасово недоступна.")

    chat_id = dest.get("chat_id")
    thread_id = dest.get("thread_id")

    header = t.FEEDBACK_HEADER.format(
        name=message.from_user.full_name, id=message.from_user.id
    )

    try:
        caption = header
        if message.caption:
            caption += f"\n\n{message.caption}"

        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=thread_id,
            caption=caption if message.caption or not message.text else None,
            parse_mode="HTML",
        )

        if message.text:
            await bot.send_message(
                chat_id=chat_id,
                text=f"{header}\n\n{message.text}",
                message_thread_id=thread_id,
                parse_mode="HTML",
            )

        # Update anti-spam data
        await state.update_data(last_msg_time=now, msg_count=msg_count + 1)

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=t.FINISH_FEEDBACK_BTN, callback_data="finish_feedback"
                    )
                ]
            ]
        )
        await message.answer(t.FEEDBACK_SENT, reply_markup=kb)
    except Exception as e:
        await message.answer(f"❌ Помилка надсилання: {e}")


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

    # Permission check
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
    # Deep link for joining
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
    # Store message_id for later updates
    game.registration_msg_id = sent_msg.message_id
    game.metadata["registration_msg_id"] = sent_msg.message_id

    if chat_settings.pin_message:
        try:
            await bot.pin_chat_message(
                message.chat.id, sent_msg.message_id, disable_notification=True
            )
        except Exception:
            pass

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

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t.JOIN_BTN,
                    url=f"https://t.me/{bot.username}?start=join_{chat_id}",
                )
            ],
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

    try:
        await bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id, text=text, reply_markup=kb
        )
    except Exception:
        pass  # Message might not be modified or deleted


@router.callback_query(lambda c: c.data == "game_settings")
async def show_settings(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    t = get_text(game.language)
    status_dark = "✅" if game.dark_mode else "❌"
    status_buttons = "✅" if game.button_board else "❌"
    status_pin = "✅" if getattr(game, "pin_message", True) else "❌"
    status_sheet = "✅" if game.metadata.get("spymaster_sheet", False) else "❌"
    status_past_clues = "✅" if game.metadata.get("show_past_clues", True) else "❌"
    status_strict = "✅" if game.metadata.get("strict_clues", False) else "❌"

    kb_list = [
        [
            types.InlineKeyboardButton(
                text=t.SET_MODE.format(mode=game.metadata.get("mode", "Classic")),
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
                text=t.SETTING_DARK_MODE.format(status=status_dark),
                callback_data="setup_dark",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SET_BOARD_SIZE.format(size=game.board_size),
                callback_data="setup_board_size",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SETTING_BUTTON_BOARD.format(status=status_buttons),
                callback_data="setup_buttons",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=f"📌 Закріпити повідомлення: {status_pin}"
                if game.language == "uk"
                else f"📌 Pin message: {status_pin}",
                callback_data="setup_pin_msg",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=f"📋 Шпаргалка капітана: {status_sheet}"
                if game.language == "uk"
                else f"📋 Captain's Sheet: {status_sheet}",
                callback_data="setup_toggle_sheet",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=f"📜 Минулі загадки: {status_past_clues}"
                if game.language == "uk"
                else f"📜 Past Clues: {status_past_clues}",
                callback_data="setup_toggle_past_clues",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=f"🔍 Строгі підказки: {status_strict}"
                if game.language == "uk"
                else f"🔍 Strict Clues: {status_strict}",
                callback_data="setup_toggle_strict",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SET_WORDS.format(words=game.word_set),
                callback_data="setup_words",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SET_TIMER_REG.format(time=game.reg_timer // 60),
                callback_data="setup_timer_reg",
            )
        ],
        [
            types.InlineKeyboardButton(
                text=t.SET_TIMER_TURN.format(time=game.turn_timer // 60),
                callback_data="setup_timer_turn",
            )
        ],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="setup_back")],
    ]

    kb = types.InlineKeyboardMarkup(inline_keyboard=kb_list)
    await callback.message.edit_text(t.SETTINGS_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data == "setup_pin_msg")
async def setup_pin_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Permission check for groups
    if (
        callback.message.chat.type != "private"
        and callback.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(
                get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True
            )

    # Update game and DB
    game.pin_message = not getattr(game, "pin_message", True)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.pin_message = game.pin_message
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_toggle_sheet")
async def setup_sheet_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Permission check for groups
    if (
        callback.message.chat.type != "private"
        and callback.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(
                get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True
            )

    # Update game and DB
    game.metadata["spymaster_sheet"] = not game.metadata.get("spymaster_sheet", False)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.spymaster_sheet = game.metadata["spymaster_sheet"]
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_toggle_past_clues")
async def setup_past_clues_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Permission check for groups
    if (
        callback.message.chat.type != "private"
        and callback.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(
                get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True
            )

    # Update game and DB
    game.metadata["show_past_clues"] = not game.metadata.get("show_past_clues", True)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.show_past_clues = game.metadata["show_past_clues"]
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_toggle_strict")
async def setup_strict_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Permission check for groups
    if (
        callback.message.chat.type != "private"
        and callback.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(
                get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True
            )

    # Update game and DB
    game.metadata["strict_clues"] = not game.metadata.get("strict_clues", False)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.strict_clues = game.metadata["strict_clues"]
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_dark")
async def setup_dark_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Permission check for groups
    if (
        callback.message.chat.type != "private"
        and callback.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(
                get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True
            )

    # Update game and DB
    game.dark_mode = not game.dark_mode
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.dark_mode = game.dark_mode
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_board_size")
async def setup_board_size_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)

    buttons = []
    row1 = [
        types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}")
        for i in range(4, 8)
    ]
    buttons.append(row1)
    row2 = [
        types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}")
        for i in range(8, 12)
    ]
    buttons.append(row2)
    row3 = [
        types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"setup_size_{i}")
        for i in range(12, 14)
    ]
    buttons.append(row3)

    buttons.append(
        [
            types.InlineKeyboardButton(
                text=t.BACK_BTN, callback_data="setup_board_size_back"
            )
        ]
    )

    await callback.message.edit_text(
        t.SET_BOARD_SIZE_TITLE,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(lambda c: c.data.startswith("setup_size_"))
async def setup_board_size_confirm(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Permission check for groups
    if (
        callback.message.chat.type != "private"
        and callback.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(
                get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True
            )

    size = int(callback.data.replace("setup_size_", ""))
    game.board_size = size

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.board_size = size

    if size > 8:
        game.button_board = False
        chat_settings.button_board = False

    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer(f"Size set to {size}x{size}")


@router.callback_query(lambda c: c.data == "setup_board_size_back")
async def setup_board_size_back(callback: types.CallbackQuery):
    await show_settings(callback)


@router.callback_query(lambda c: c.data == "setup_buttons")
async def setup_buttons_toggle(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    # Permission check for groups
    if (
        callback.message.chat.type != "private"
        and callback.from_user.id != settings.admin_id
    ):
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(
                get_text(game.language).ADMIN_ONLY_ERROR, show_alert=True
            )

    if game.board_size > 8:
        return await callback.answer(
            "❌ Слів занадто багато для кнопкового відображення!", show_alert=True
        )

    # Update game and DB
    game.button_board = not game.button_board
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.button_board = game.button_board
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    await show_settings(callback)
    await callback.answer()


@router.callback_query(lambda c: c.data == "setup_timer_reg")
async def setup_timer_reg_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t.TIME_2M, callback_data="conf_tmreg_120"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.TIME_5M, callback_data="conf_tmreg_300"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.TIME_10M, callback_data="conf_tmreg_600"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.BACK_BTN, callback_data="game_settings"
                )
            ],
        ]
    )
    await callback.message.edit_text(t.SET_TMR_REG_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("conf_tmreg_"))
async def confirm_tmreg(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.reg_timer = int(callback.data.replace("conf_tmreg_", ""))
    await show_settings(callback)


@router.callback_query(lambda c: c.data == "setup_timer_turn")
async def setup_timer_turn_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t.TIME_1M, callback_data="conf_tmturn_60"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.TIME_2M, callback_data="conf_tmturn_120"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.TIME_3M, callback_data="conf_tmturn_180"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.BACK_BTN, callback_data="game_settings"
                )
            ],
        ]
    )
    await callback.message.edit_text(t.SET_TMR_TURN_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("conf_tmturn_"))
async def confirm_tmturn(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.turn_timer = int(callback.data.replace("conf_tmturn_", ""))
    await show_settings(callback)


@router.callback_query(lambda c: c.data == "setup_mode")
async def setup_mode_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t.MODE_CLASSIC_BTN, callback_data="conf_mode_Classic"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.MODE_DUET_BTN, callback_data="conf_mode_Duet"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="💀 Hardcore (Хардкор)" if game.language == "uk" else "💀 Hardcore",
                    callback_data="conf_mode_Hardcore"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.BACK_BTN, callback_data="game_settings"
                )
            ],
        ]
    )
    await callback.message.edit_text(t.SET_MODE_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("conf_mode_"))
async def confirm_mode(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.metadata["mode"] = callback.data.replace("conf_mode_", "")
    await show_settings(callback)


@router.callback_query(lambda c: c.data == "setup_back")
async def settings_back(callback: types.CallbackQuery, bot: Bot):
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    await update_registration_view(bot, callback.message.chat.id, game)


@router.callback_query(lambda c: c.data == "setup_lang")
async def setup_lang_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    t = get_text(game.language)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t.LANG_UK_BTN, callback_data="conf_lang_uk"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.LANG_EN_BTN, callback_data="conf_lang_en"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t.BACK_BTN, callback_data="game_settings"
                )
            ],
        ]
    )
    await callback.message.edit_text(t.SET_LANG_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("conf_lang_"))
async def confirm_lang(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.language = callback.data.replace("conf_lang_", "")
    await show_settings(callback)


@router.callback_query(lambda c: c.data == "setup_words")
async def setup_words_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return

    from src.games.codenames.words import WordRepository

    repo = WordRepository()
    sets = repo.list_available_sets(game.language)

    # Get custom dictionaries
    custom_dicts = await db_service.get_custom_dictionaries(callback.message.chat.id)

    t = get_text(game.language)
    buttons = []
    for s in sets:
        buttons.append(
            [
                types.InlineKeyboardButton(
                    text=t.WORD_SET_FORMAT.format(name=s),
                    callback_data=f"conf_words_{s}",
                )
            ]
        )

    for d in custom_dicts:
        buttons.append(
            [
                types.InlineKeyboardButton(
                    text=f"✨ {d.name}", callback_data=f"conf_words_custom_{d.name}"
                )
            ]
        )

    await callback.message.edit_text(
        t.SET_WORDS_TITLE,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=buttons
            + [
                [
                    types.InlineKeyboardButton(
                        text=t.BACK_BTN, callback_data="game_settings"
                    )
                ]
            ]
        ),
    )


@router.callback_query(lambda c: c.data.startswith("conf_words_"))
async def confirm_word_set(callback: types.CallbackQuery):
    if not callback.message:
        return
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return
    game.word_set = callback.data.replace("conf_words_", "")
    await show_settings(callback)


@router.callback_query(lambda c: c.data == "game_cancel")
async def cancel_registration(callback: types.CallbackQuery, bot: Bot, settings):
    if not callback.message:
        return

    game = manager.get_game(callback.message.chat.id)
    if not game:
        return await callback.answer()

    t = get_text(game.language)

    # Permission check: Only admin can cancel registration phase
    if callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(
            callback.message.chat.id, callback.from_user.id
        )
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(t.ONLY_ADMIN_STOP, show_alert=True)

    manager.end_game(callback.message.chat.id)
    # Unpin if pinned
    try:
        await bot.unpin_chat_message(
            callback.message.chat.id, callback.message.message_id
        )
    except Exception:
        pass

    await callback.message.edit_text(t.GAME_STOPPED)
    await callback.answer()


@router.message(Command("cnstop"))
async def cmd_stop(message: types.Message, bot: Bot, settings):
    game = manager.get_game(message.chat.id)
    if not game:
        return

    t = get_text(game.language)

    # Permission check: Only admin can stop the game
    if message.chat.type != "private" and message.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ONLY_ADMIN_STOP)

    manager.end_game(message.chat.id)

    # Unpin if pinned
    try:
        if game.board_msg_id:
            await bot.unpin_chat_message(message.chat.id, game.board_msg_id)
        elif game.metadata.get("registration_msg_id"):
            await bot.unpin_chat_message(
                message.chat.id, game.metadata["registration_msg_id"]
            )
    except Exception:
        pass

    await message.answer(t.GAME_STOPPED)


@router.callback_query(F.data == "profile_captain_buffs")
async def profile_captain_buffs(callback: types.CallbackQuery):
    """Show captain buffs management menu."""
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    t = get_text(lang)
    user_id = callback.from_user.id

    inv = await db_service.get_user_inventory(user_id)
    flags = await db_service.get_user_captain_buff_flags(user_id)

    avoid_count = inv.get("avoid_captain", 0)
    become_count = inv.get("become_captain", 0)
    avoid_ready = flags.get("avoid_captain_ready", False)
    become_ready = flags.get("become_captain_ready", False)

    # Format status labels
    avoid_status = t.BUFFS_ACTIVE_STATUS if avoid_ready else t.BUFFS_INACTIVE_STATUS
    become_status = t.BUFFS_ACTIVE_STATUS if become_ready else t.BUFFS_INACTIVE_STATUS

    kb = InlineKeyboardBuilder()

    # Avoid Captain row
    avoid_label = f"{t.BUFF_AVOID_CAPTAIN_NAME}: {avoid_count} шт. [{avoid_status}]"
    if avoid_ready:
        kb.row(types.InlineKeyboardButton(text=avoid_label, callback_data="none"))
        kb.row(types.InlineKeyboardButton(text=t.CAPTAIN_BUFF_DEACTIVATE_BTN, callback_data="captain_toggle_avoid_off"))
    elif avoid_count > 0 and not become_ready:  # can't have both active
        kb.row(types.InlineKeyboardButton(text=avoid_label, callback_data="none"))
        kb.row(types.InlineKeyboardButton(text=t.CAPTAIN_BUFF_ACTIVATE_BTN, callback_data="captain_toggle_avoid_on"))
    else:
        kb.row(types.InlineKeyboardButton(text=avoid_label, callback_data="none"))

    # Become Captain row
    become_label = f"{t.BUFF_BECOME_CAPTAIN_NAME}: {become_count} шт. [{become_status}]"
    if become_ready:
        kb.row(types.InlineKeyboardButton(text=become_label, callback_data="none"))
        kb.row(types.InlineKeyboardButton(text=t.CAPTAIN_BUFF_DEACTIVATE_BTN, callback_data="captain_toggle_become_off"))
    elif become_count > 0 and not avoid_ready:  # can't have both active
        kb.row(types.InlineKeyboardButton(text=become_label, callback_data="none"))
        kb.row(types.InlineKeyboardButton(text=t.CAPTAIN_BUFF_ACTIVATE_BTN, callback_data="captain_toggle_become_on"))
    else:
        kb.row(types.InlineKeyboardButton(text=become_label, callback_data="none"))

    if avoid_ready and become_ready:
        kb.row(types.InlineKeyboardButton(text="⚠️ Можна активувати лише один баф одночасно!" if lang == "uk" else "⚠️ Only one buff can be active at a time!", callback_data="none"))

    # Buy more buttons (quick buy)
    if lang == "uk":
        kb.row(
            types.InlineKeyboardButton(text="🚫 Купити Уникнути капітанства 50💎", callback_data="buy_inv_buff_avoid_captain_dia"),
            types.InlineKeyboardButton(text="250🪙", callback_data="buy_inv_buff_avoid_captain_coin"),
        )
        kb.row(
            types.InlineKeyboardButton(text="👑 Купити Стати капітаном 75💎", callback_data="buy_inv_buff_become_captain_dia"),
            types.InlineKeyboardButton(text="375🪙", callback_data="buy_inv_buff_become_captain_coin"),
        )
        kb.row(types.InlineKeyboardButton(text="🔙 Назад до профілю", callback_data="profile_back"))
    else:
        kb.row(
            types.InlineKeyboardButton(text="🚫 Buy Avoid Captain 50💎", callback_data="buy_inv_buff_avoid_captain_dia"),
            types.InlineKeyboardButton(text="250🪙", callback_data="buy_inv_buff_avoid_captain_coin"),
        )
        kb.row(
            types.InlineKeyboardButton(text="👑 Buy Become Captain 75💎", callback_data="buy_inv_buff_become_captain_dia"),
            types.InlineKeyboardButton(text="375🪙", callback_data="buy_inv_buff_become_captain_coin"),
        )
        kb.row(types.InlineKeyboardButton(text="🔙 Back to Profile", callback_data="profile_back"))

    text = t.BUFFS_MENU_TITLE
    if lang == "uk":
        text += f"\n\n{t.CAPTAIN_BUFFS_SECTION}\n"
        text += f"\n{t.BUFF_AVOID_CAPTAIN_NAME}: {avoid_count} шт."
        text += f"\n{t.BUFF_AVOID_CAPTAIN_DESC}"
        text += f"\n\n{t.BUFF_BECOME_CAPTAIN_NAME}: {become_count} шт."
        text += f"\n{t.BUFF_BECOME_CAPTAIN_DESC}"
    else:
        text += f"\n\n{t.CAPTAIN_BUFFS_SECTION}\n"
        text += f"\n{t.BUFF_AVOID_CAPTAIN_NAME}: {avoid_count} pcs."
        text += f"\n{t.BUFF_AVOID_CAPTAIN_DESC}"
        text += f"\n\n{t.BUFF_BECOME_CAPTAIN_NAME}: {become_count} pcs."
        text += f"\n{t.BUFF_BECOME_CAPTAIN_DESC}"

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("captain_toggle_"))
async def captain_toggle_handler(callback: types.CallbackQuery):
    """Toggle captain buff on/off."""
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    t = get_text(lang)
    user_id = callback.from_user.id

    # data format: captain_toggle_{buff_type}_{on|off}
    data = callback.data.replace("captain_toggle_", "")
    parts = data.split("_")
    if len(parts) < 2:
        return

    buff_type = parts[0]  # "avoid" or "become"
    action = parts[1]  # "on" or "off"

    # Map to full DB column name
    full_buff_type = f"{buff_type}_captain"

    if action == "on":
        # Can't activate if other captain buff is already active
        other_type = "become_captain" if buff_type == "avoid" else "avoid_captain"
        other_flags = await db_service.get_user_captain_buff_flags(user_id)
        if other_flags.get(f"{other_type}_ready", False):
            return await callback.answer(
                "⚠️ Спочатку деактивуйте інший баф капітана!" if lang == "uk" else "⚠️ Deactivate the other captain buff first!",
                show_alert=True
            )
        success = await db_service.toggle_captain_buff_ready(user_id, full_buff_type, True)
        if not success:
            return await callback.answer(t.CAPTAIN_BUFF_NO_INVENTORY, show_alert=True)
        msg = t.AVOID_CAPTAIN_ACTIVATED if buff_type == "avoid" else t.BECOME_CAPTAIN_ACTIVATED
        await callback.answer(msg)
    else:
        await db_service.toggle_captain_buff_ready(user_id, full_buff_type, False)
        msg = t.AVOID_CAPTAIN_DEACTIVATED if buff_type == "avoid" else t.BECOME_CAPTAIN_DEACTIVATED
        await callback.answer(msg)

    # Refresh menu
    await profile_captain_buffs(callback)
