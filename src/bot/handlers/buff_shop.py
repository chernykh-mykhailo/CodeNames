from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.database.service import db_service
from src.assets.texts import get_text
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "profile_shop_buffs")
async def profile_shop_buffs(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    t = get_text(lang)
    balance = await db_service.get_user_diamonds(callback.from_user.id)
    coins = await db_service.get_user_coins(callback.from_user.id)
    inv = await db_service.get_user_inventory(callback.from_user.id)

    kb = InlineKeyboardBuilder()

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
            f"<b>{t.BUFF_BECOME_CAPTAIN_NAME}</b> — {t.BUFF_BECOME_CAPTAIN_PRICE}💎 / {t.BUFF_BECOME_CAPTAIN_PRICE_COINS}🪙\n"
            f"<blockquote>{t.BUFF_BECOME_CAPTAIN_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_AVOID_CAPTAIN_NAME}</b> — {t.BUFF_AVOID_CAPTAIN_PRICE}💎 / {t.BUFF_AVOID_CAPTAIN_PRICE_COINS}🪙\n"
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

    parts = data.rsplit("_", 1)
    if len(parts) < 2:
        return
    buff_type = parts[0]
    currency = parts[1]

    prices_dia = {
        "armor": t.BUFF_ARMOR_PRICE,
        "intercept": t.BUFF_INTERCEPT_PRICE,
        "detector": t.BUFF_DETECTOR_PRICE,
        "reveal": 20,
        "remap": t.BUFF_REMAP_PRICE,
        "avoid_captain": t.BUFF_AVOID_CAPTAIN_PRICE,
        "become_captain": t.BUFF_BECOME_CAPTAIN_PRICE,
    }

    prices_coin = {
        "armor": 175,
        "intercept": 125,
        "detector": 75,
        "reveal": 100,
        "remap": 50,
        "avoid_captain": t.BUFF_AVOID_CAPTAIN_PRICE_COINS,
        "become_captain": t.BUFF_BECOME_CAPTAIN_PRICE_COINS,
    }

    buff_column = buff_type

    if currency == "dia":
        price = prices_dia.get(buff_type, 9999)
        balance = await db_service.get_user_diamonds(callback.from_user.id)
        logger.info(f"BUY_DIA: user={callback.from_user.id}, buff={buff_type}, price={price}, balance={balance}")
        if balance < price:
            logger.warning(f"BUY_DIA_FAILED: user={callback.from_user.id}, balance={balance} < price={price}")
            return await callback.answer(t.BUY_FAIL, show_alert=True)
        await db_service.update_user_diamonds(callback.from_user.id, -price)
    else:
        price = prices_coin.get(buff_type, 9999)
        balance = await db_service.get_user_coins(callback.from_user.id)
        logger.info(f"BUY_COIN: user={callback.from_user.id}, buff={buff_type}, price={price}, balance={balance}")
        if balance < price:
            logger.warning(f"BUY_COIN_FAILED: user={callback.from_user.id}, balance={balance} < price={price}")
            return await callback.answer(t.BUY_FAIL, show_alert=True)
        await db_service.update_user_coins(callback.from_user.id, -price)

    await db_service.update_user_buff(callback.from_user.id, buff_column, 1)

    await callback.answer(t.BUY_SUCCESS)
    await profile_shop_buffs(callback)