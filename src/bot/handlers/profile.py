import random
from typing import Any
from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.platform.game_manager import manager
from src.core.database.service import db_service
from src.assets.texts import get_text, b
import logging

logger = logging.getLogger(__name__)

router = Router()

SPY_QUOTES_UK = [
    "«Шпигун — це не професія, це спосіб життя.»",
    "«У шпигунстві немає випадкових людей, є лише непомітних.»",
    "«Найкраща зброя агента — це інформація.»",
    "«Точність — це наша ввічливість, скритність — наш девіз.»",
    "«Ми діємо в тіні, щоб служити світлу.»",
    "«Справжній майстер кодових імен бачить зв'язки там, де інші бачать хаос.»",
    "«Тиша — найкращий союзник шпигуна.»",
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

    text = (
        f"{t.PROFILE_TITLE}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<blockquote>{t.PROFILE_CODE_NAME.format(name=codename)}\n"
        f"{t.PROFILE_DIAMONDS.format(balance=balance)}\n"
        f"{t.PROFILE_COINS.format(balance=coins)}\n"
        f"{t.PROFILE_LEVEL.format(level=level)}\n"
        f"{progress_bar}\n"
        f"{t.PROFILE_NEXT_LEVEL.format(xp=level_progress_xp, needed=xp_needed)}</blockquote>\n\n"
        f"{t.PROFILE_COMBAT_STATS}\n"
        f"<blockquote>{t.PROFILE_TOTAL_GAMES.format(count=total)}\n"
        f"{t.PROFILE_WINS.format(count=wins)}\n"
        f"{t.PROFILE_LOSSES.format(count=losses)}\n"
        f"{t.PROFILE_WINRATE.format(rate=winrate)}\n"
        f"{t.PROFILE_GUESSED_WORDS.format(count=guessed_words)}\n"
        f"{t.PROFILE_ASSASSINS_HIT.format(count=assassins_hit)}\n"
        f"{t.PROFILE_OPPONENT_WORDS_HIT.format(count=opponent_words_hit)}</blockquote>\n\n"
        f"{t.PROFILE_INVENTORY}\n"
        f"<blockquote>├─ {t.BUFF_ARMOR_NAME}: <b>{inv.get('armor', 0)}</b>{t.PROFILE_INVENTORY_PCS}\n"
        f"├─ {t.BUFF_INTERCEPT_NAME}: <b>{inv.get('intercept', 0)}</b>{t.PROFILE_INVENTORY_PCS}\n"
        f"├─ {t.BUFF_DETECTOR_NAME}: <b>{inv.get('detector', 0)}</b>{t.PROFILE_INVENTORY_PCS}\n"
        f"├─ {t.REVEAL_BUFF_NAME.split('(')[0].strip()}: <b>{inv.get('reveal', 0)}</b>{t.PROFILE_INVENTORY_PCS}\n"
        f"├─ {t.BUFF_REMAP_NAME}: <b>{inv.get('remap', 0)}</b>{t.PROFILE_INVENTORY_PCS}\n"
        f"├─ {t.BUFF_AVOID_CAPTAIN_NAME}: <b>{inv.get('avoid_captain', 0)}</b>{t.PROFILE_INVENTORY_PCS}\n"
        f"└─ {t.BUFF_BECOME_CAPTAIN_NAME}: <b>{inv.get('become_captain', 0)}</b>{t.PROFILE_INVENTORY_PCS}</blockquote>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💬 <i>{quote}</i>"
    )

    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(
            text=t.PROFILE_CAPTAIN_BUFFS_BTN, callback_data="profile_captain_buffs"
        ),
    )
    kb.row(
        types.InlineKeyboardButton(
            text=t.PROFILE_BUY_BUFFS_BTN, callback_data="profile_shop_buffs"
        ),
        types.InlineKeyboardButton(
            text=t.PROFILE_BUY_DIAMONDS_BTN, callback_data="profile_shop_diamonds"
        ),
    )
    kb.row(
        types.InlineKeyboardButton(
            text="⚙️ Налаштування" if lang == "uk" else "⚙️ Settings", callback_data="profile_settings"
        ),
    )
    kb.row(
        types.InlineKeyboardButton(text=t.CLOSE_BTN, callback_data="profile_close")
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
            sent = await message.answer(t.PROFILE_SENT_TO_DM)

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

    kb.row(
        types.InlineKeyboardButton(
            text=t.PROFILE_BACK_BTN, callback_data="profile_back"
        )
    )
    text = (
        f"{t.PROFILE_SHOP_DIAMONDS_TITLE}\n"
        f"{t.PROFILE_SHOP_DIAMONDS_BALANCE.format(balance=balance)}\n\n"
        f"{t.PROFILE_SHOP_DIAMONDS_SELECT}"
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
            avoid_label = f"✅ {t.BUFF_AVOID_CAPTAIN_NAME}: {avoid_count}{t.PROFILE_INVENTORY_PCS}"
        else:
            avoid_label = f"⬜ {t.BUFF_AVOID_CAPTAIN_NAME}: {avoid_count}{t.PROFILE_INVENTORY_PCS}"
        kb.row(types.InlineKeyboardButton(text=avoid_label, callback_data="captain_toggle_avoid"))

    if become_count > 0:
        if become_ready:
            become_label = f"✅ {t.BUFF_BECOME_CAPTAIN_NAME}: {become_count}{t.PROFILE_INVENTORY_PCS}"
        else:
            become_label = f"⬜ {t.BUFF_BECOME_CAPTAIN_NAME}: {become_count}{t.PROFILE_INVENTORY_PCS}"
        kb.row(types.InlineKeyboardButton(text=become_label, callback_data="captain_toggle_become"))

    if avoid_ready and become_ready:
        kb.row(types.InlineKeyboardButton(text=t.PROFILE_CAPTAIN_BUFFS_ONLY_ONE, callback_data="none"))

    kb.row(types.InlineKeyboardButton(text=t.PROFILE_BACK_BTN, callback_data="profile_back"))

    text = (
        f"{t.BUFFS_MENU_TITLE}\n\n"
        f"{t.CAPTAIN_BUFFS_SECTION}\n\n"
        f"{t.BUFF_AVOID_CAPTAIN_NAME}: {avoid_count}{t.PROFILE_INVENTORY_PCS}\n"
        f"{t.BUFF_AVOID_CAPTAIN_DESC}\n\n"
        f"{t.BUFF_BECOME_CAPTAIN_NAME}: {become_count}{t.PROFILE_INVENTORY_PCS}\n"
        f"{t.BUFF_BECOME_CAPTAIN_DESC}"
    )

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


@router.callback_query(F.data == "profile_settings")
async def profile_settings_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    
    # Fetch all_games_subscribers
    subs_all = await db_service.get_system_setting("all_games_subscribers")
    
    # Find chats where user is subscribed
    subscribed_chats = []
    for cid_str, uids in subs_all.items():
        if user_id in uids:
            try:
                cid = int(cid_str)
                chat_info = await callback.bot.get_chat(cid)
                subscribed_chats.append((cid, chat_info.title))
            except Exception:
                subscribed_chats.append((int(cid_str), f"Chat {cid_str}"))
                
    kb = InlineKeyboardBuilder()
    
    if not subscribed_chats:
        text = b(lang,
                 "⚙️ <b>Налаштування сповіщень</b>\n\nВи не підписані на сповіщення про нові ігри в жодному чаті.",
                 "⚙️ <b>Notification Settings</b>\n\nYou are not subscribed to game notifications in any chats.")
    else:
        text = b(lang,
                 "⚙️ <b>Налаштування сповіщень</b>\n\nНижче наведено чати, з яких ви отримуєте сповіщення про всі нові ігри. Натисніть на назву чату, щоб вимкнути сповіщення:",
                 "⚙️ <b>Notification Settings</b>\n\nBelow are the chats you receive notifications for. Click on a chat to unsubscribe:")
                 
        for cid, title in subscribed_chats:
            kb.row(types.InlineKeyboardButton(
                text=f"🔕 {title}" if lang == "uk" else f"🔕 {title}",
                callback_data=f"unsub_{cid}"
            ))
            
    kb.row(types.InlineKeyboardButton(text=get_text(lang).PROFILE_BACK_BTN, callback_data="profile_back"))
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("unsub_"))
async def handle_unsubscribe(callback: types.CallbackQuery):
    chat_id = int(callback.data.replace("unsub_", ""))
    user_id = callback.from_user.id
    
    subs_all = await db_service.get_system_setting("all_games_subscribers")
    chat_key = str(chat_id)
    
    if chat_key in subs_all and user_id in subs_all[chat_key]:
        subs_all[chat_key].remove(user_id)
        await db_service.update_system_setting("all_games_subscribers", subs_all)
        
    chat_settings = await db_service.get_chat_settings(chat_id)
    await callback.answer(b(chat_settings.language, "Сповіщення вимкнено! 🔕", "Notifications turned off! 🔕"))
    # Refresh menu
    await profile_settings_menu(callback)