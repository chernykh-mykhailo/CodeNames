import random
from typing import Any
from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.platform.game_manager import manager
from src.core.database.service import db_service
from src.assets.texts import get_text
import logging

logger = logging.getLogger(__name__)

router = Router()

SPY_QUOTES_UK = [
    "\u00abШпигун \u2014 це не профес\u0129я, це спос\u0156б життя.\u00bb",
    "\u00abУ шпигунств\u0129 нема\u0454 випадкових людей, є лише непом\u0129тних.\u00bb",
    "\u00abНайкраща збр\u0457я агента \u2014 це \u0456нформац\u0129я.\u00bb",
    "\u00abТочн\u0156сть \u2014 це наша вв\u0456члив\u0156сть, скритн\u0156сть \u2014 наш дев\u0456з.\u00bb",
    "\u00abМи д\u0456\u0454мо в т\u0156н\u0129, щоб служити св\u0156тлу.\u00bb",
    "\u00abСправжн\u0156й майстер кодових \u0456мен бачить зв'\u0454зки там, де \u0456нш\u0156 бачать хаос.\u00bb",
    "\u00abТиша \u2014 найкращий союзник шпигуна.\u00bb",
]

SPY_QUOTES_EN = [
    '"A spy is not a profession, it is a way of life."',
    '"In espionage, there are no accidental people, only invisible ones."',
    '"The agent\'s best weapon is information."',
    '"Accuracy is our politeness, stealth is our motto."',
    '"We work in the dark to serve the light."',
    '"A true master of codenames sees connections where others see chaos."',
    '"Silence is a spy\'s best ally."',
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

            import asyncio

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

    kb = InlineKeyboardBuilder()

    if avoid_count > 0:
        if avoid_ready:
            avoid_label = f"✅ {t.BUFF_AVOID_CAPTAIN_NAME}: {avoid_count} шт."
        else:
            avoid_label = f"⬜ {t.BUFF_AVOID_CAPTAIN_NAME}: {avoid_count} шт."
        kb.row(types.InlineKeyboardButton(text=avoid_label, callback_data="captain_toggle_avoid"))

    if become_count > 0:
        if become_ready:
            become_label = f"✅ {t.BUFF_BECOME_CAPTAIN_NAME}: {become_count} шт."
        else:
            become_label = f"⬜ {t.BUFF_BECOME_CAPTAIN_NAME}: {become_count} шт."
        kb.row(types.InlineKeyboardButton(text=become_label, callback_data="captain_toggle_become"))

    if avoid_ready and become_ready:
        kb.row(types.InlineKeyboardButton(text="⚠️ Можна активувати лише один баф одночасно!" if lang == "uk" else "⚠️ Only one buff can be active at a time!", callback_data="none"))

    if lang == "uk":
        kb.row(types.InlineKeyboardButton(text="🔙 Назад до профілю", callback_data="profile_back"))
    else:
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

    buff_type = callback.data.replace("captain_toggle_", "")
    if buff_type not in ("avoid", "become"):
        return

    full_buff_type = f"{buff_type}_captain"
    other_type = "become_captain" if buff_type == "avoid" else "avoid_captain"

    flags = await db_service.get_user_captain_buff_flags(user_id)
    is_ready = flags.get(f"{full_buff_type}_ready", False)

    if is_ready:
        await db_service.toggle_captain_buff_ready(user_id, full_buff_type, False)
        msg = t.AVOID_CAPTAIN_DEACTIVATED if buff_type == "avoid" else t.BECOME_CAPTAIN_DEACTIVATED
        await callback.answer(msg)
    else:
        other_ready = flags.get(f"{other_type}_ready", False)
        if other_ready:
            await db_service.toggle_captain_buff_ready(user_id, other_type, False)

        success = await db_service.toggle_captain_buff_ready(user_id, full_buff_type, True)
        if not success:
            return await callback.answer(t.CAPTAIN_BUFF_NO_INVENTORY, show_alert=True)
        msg = t.AVOID_CAPTAIN_ACTIVATED if buff_type == "avoid" else t.BECOME_CAPTAIN_ACTIVATED
        await callback.answer(msg)

    await profile_captain_buffs(callback)