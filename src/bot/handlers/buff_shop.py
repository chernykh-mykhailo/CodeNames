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
                text=f"{bname}: {bcount} \u2014 {pcoin}\U0001fa99",
                callback_data=left_cb,
            ),
            types.InlineKeyboardButton(
                text=f"{pdia}\U0001f48e",
                callback_data=right_cb,
            ),
        )

    if lang == "uk":
        kb.row(
            types.InlineKeyboardButton(
                text="\U0001f519 \u041d\u0430\u0437\u0430\u0434 \u0434\u043e \u043f\u0440\u043e\u0444\u0456\u043b\u044e", callback_data="profile_back"
            )
        )
        text = (
            f"\U0001f6d2 <b>\u041c\u0410\u0413\u0410\u0417\u0418\u041d \u0411\u0410\u0424\u0406\u0412</b>\n\n"
            f"\U0001f48e \u0414\u0456\u0430\u043c\u0430\u043d\u0442\u0438: <b>{balance}</b>\n"
            f"\U0001fa99 \u041c\u043e\u043d\u0435\u0442\u0438: <b>{coins}</b>\n\n"
            f"<b>{t.BUFF_ARMOR_NAME}</b> \u2014 {t.BUFF_ARMOR_PRICE}\U0001f48e / 175\U0001fa99\n"
            f"<blockquote>{t.BUFF_ARMOR_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_INTERCEPT_NAME}</b> \u2014 {t.BUFF_INTERCEPT_PRICE}\U0001f48e / 125\U0001fa99\n"
            f"<blockquote>{t.BUFF_INTERCEPT_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_DETECTOR_NAME}</b> \u2014 {t.BUFF_DETECTOR_PRICE}\U0001f48e / 75\U0001fa99\n"
            f"<blockquote>{t.BUFF_DETECTOR_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_REVEAL_SHORT}</b> \u2014 20\U0001f48e / 100\U0001fa99\n"
            f"<blockquote>{t.REVEAL_BUFF_NAME}</blockquote>\n\n"
            f"<b>{t.BUFF_REMAP_NAME}</b> \u2014 {t.BUFF_REMAP_PRICE}\U0001f48e / 50\U0001fa99\n"
            f"<blockquote>{t.BUFF_REMAP_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_BECOME_CAPTAIN_SHORT}</b> \u2014 {t.BUFF_BECOME_CAPTAIN_PRICE}\U0001f48e / {t.BUFF_BECOME_CAPTAIN_PRICE_COINS}\U0001fa99\n"
            f"<blockquote>{t.BUFF_BECOME_CAPTAIN_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_AVOID_CAPTAIN_SHORT}</b> \u2014 {t.BUFF_AVOID_CAPTAIN_PRICE}\U0001f48e / {t.BUFF_AVOID_CAPTAIN_PRICE_COINS}\U0001fa99\n"
            f"<blockquote>{t.BUFF_AVOID_CAPTAIN_DESC}</blockquote>"
        )
    else:
        kb.row(
            types.InlineKeyboardButton(
                text="\U0001f519 Back to Profile", callback_data="profile_back"
            )
        )
        text = (
            f"\U0001f6d2 <b>BUFF SHOP</b>\n\n"
            f"\U0001f48e Diamonds: <b>{balance}</b>\n"
            f"\U0001fa99 Coins: <b>{coins}</b>\n\n"
            f"<b>{t.BUFF_ARMOR_NAME}</b> \u2014 {t.BUFF_ARMOR_PRICE}\U0001f48e / 175\U0001fa99\n"
            f"<blockquote>{t.BUFF_ARMOR_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_INTERCEPT_NAME}</b> \u2014 {t.BUFF_INTERCEPT_PRICE}\U0001f48e / 125\U0001fa99\n"
            f"<blockquote>{t.BUFF_INTERCEPT_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_DETECTOR_NAME}</b> \u2014 {t.BUFF_DETECTOR_PRICE}\U0001f48e / 75\U0001fa99\n"
            f"<blockquote>{t.BUFF_DETECTOR_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_REVEAL_SHORT}</b> \u2014 20\U0001f48e / 100\U0001fa99\n"
            f"<blockquote>{t.REVEAL_BUFF_NAME}</blockquote>\n\n"
            f"<b>{t.BUFF_REMAP_NAME}</b> \u2014 {t.BUFF_REMAP_PRICE}\U0001f48e / 50\U0001fa99\n"
            f"<blockquote>{t.BUFF_REMAP_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_BECOME_CAPTAIN_NAME}</b> \u2014 {t.BUFF_BECOME_CAPTAIN_PRICE}\U0001f48e / {t.BUFF_BECOME_CAPTAIN_PRICE_COINS}\U0001fa99\n"
            f"<blockquote>{t.BUFF_BECOME_CAPTAIN_DESC}</blockquote>\n\n"
            f"<b>{t.BUFF_AVOID_CAPTAIN_NAME}</b> \u2014 {t.BUFF_AVOID_CAPTAIN_PRICE}\U0001f48e / {t.BUFF_AVOID_CAPTAIN_PRICE_COINS}\U0001fa99\n"
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