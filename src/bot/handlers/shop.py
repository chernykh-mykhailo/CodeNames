import httpx
from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.database.service import db_service
from src.assets.texts import get_text
import logging

router = Router()
logger = logging.getLogger(__name__)

PACKS = {
    "1000": {"amount": 1000, "price_uah": 100, "price_stars": 200},
    "5000": {"amount": 5000, "price_uah": 450, "price_stars": 900},
    "10000": {"amount": 10000, "price_uah": 800, "price_stars": 1600},
}

@router.message(Command("diamonds"))
async def cmd_shop(message: types.Message):
    t = get_text(message.from_user.language_code)
    balance = await db_service.get_user_diamonds(message.from_user.id)
    
    kb = InlineKeyboardBuilder()
    for key, pack in PACKS.items():
        kb.row(types.InlineKeyboardButton(
            text=f"💎 {pack['amount']} — {pack['price_uah']} UAH / {pack['price_stars']} 🌟",
            callback_data=f"shop_pack_{key}"
        ))
    
    text = (
        f"{t.SHOP_DIAMONDS_TITLE}\n"
        f"{t.SHOP_BALANCE.format(balance=balance)}\n\n"
        f"{t.SHOP_DIAMONDS_DESC}"
    )
    await message.answer(text, reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("shop_pack_"))
async def select_pack(callback: types.CallbackQuery, settings):
    t = get_text(callback.from_user.language_code)
    pack_id = callback.data.replace("shop_pack_", "")
    
    kb = InlineKeyboardBuilder()
    
    # Show Mono only if token or jar is configured
    # (Checking if jar_url is not just the default base domain)
    has_mono = bool(settings.monobank_token) or (bool(settings.mono_jar_url) and len(settings.mono_jar_url) > 25)
    
    if has_mono:
        kb.row(types.InlineKeyboardButton(text=t.BUY_VIA_MONO, callback_data=f"buy_mono_{pack_id}"))
    
    kb.row(types.InlineKeyboardButton(text=t.BUY_VIA_STARS, callback_data=f"buy_stars_{pack_id}"))
    kb.row(types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="shop_back"))
    
    await callback.message.edit_text(t.SHOP_DIAMONDS_TITLE, reply_markup=kb.as_markup())

@router.callback_query(F.data == "shop_back")
async def shop_back(callback: types.CallbackQuery):
    t = get_text(callback.from_user.language_code)
    balance = await db_service.get_user_diamonds(callback.from_user.id)
    kb = InlineKeyboardBuilder()
    for key, pack in PACKS.items():
        kb.row(types.InlineKeyboardButton(text=f"💎 {pack['amount']} — {pack['price_uah']} UAH / {pack['price_stars']} 🌟", callback_data=f"shop_pack_{key}"))
    
    text = (
        f"{t.SHOP_DIAMONDS_TITLE}\n"
        f"{t.SHOP_BALANCE.format(balance=balance)}\n\n"
        f"{t.SHOP_DIAMONDS_DESC}"
    )
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

# --- TELEGRAM STARS ---
@router.callback_query(F.data.startswith("buy_stars_"))
async def buy_stars(callback: types.CallbackQuery, bot: Bot):
    t = get_text(callback.from_user.language_code)
    pack_id = callback.data.replace("buy_stars_", "")
    pack = PACKS.get(pack_id)
    if not pack: return

    try:
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=t.INVOICE_TITLE.format(amount=pack['amount']),
            description=t.INVOICE_DESC,
            payload=f"stars_{pack_id}",
            currency="XTR",
            prices=[types.LabeledPrice(
                label=t.ITEM_1000_NAME if pack_id=="1000" else t.ITEM_5000_NAME if pack_id=="5000" else t.ITEM_10000_NAME, 
                amount=pack['price_stars']
            )],
            provider_token="" # Empty for Stars
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Stars error: {e}")
        await callback.answer(t.PAYMENT_ERROR, show_alert=True)

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: types.Message):
    t = get_text(message.from_user.language_code)
    payload = message.successful_payment.invoice_payload
    if payload.startswith("stars_"):
        pack_id = payload.replace("stars_", "")
        pack = PACKS.get(pack_id)
        if pack:
            await db_service.update_user_diamonds(message.from_user.id, pack['amount'])
            await message.answer(t.PAYMENT_SUCCESS.format(amount=pack['amount']))

# --- MONOBANK ---
@router.callback_query(F.data.startswith("buy_mono_"))
async def buy_mono(callback: types.CallbackQuery, settings):
    t = get_text(callback.from_user.language_code)
    pack_id = callback.data.replace("buy_mono_", "")
    pack = PACKS.get(pack_id)
    if not pack: return

    # If token is provided, use automated acquiring
    if settings.monobank_token:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "https://api.monobank.ua/api/merchant/invoice/create",
                    headers={"X-Token": settings.monobank_token},
                    json={
                        "amount": pack['price_uah'] * 100,
                        "ccy": 980,
                        "merchantPaymInfo": {
                            "reference": f"{callback.from_user.id}_{pack_id}",
                            "destination": t.INVOICE_TITLE.format(amount=pack['amount'])
                        },
                        "redirectUrl": f"https://t.me/{(await callback.bot.get_me()).username}"
                    }
                )
                data = resp.json()
                if "pageUrl" in data:
                    kb = InlineKeyboardBuilder()
                    kb.row(types.InlineKeyboardButton(text="💳 Оплатити", url=data['pageUrl']))
                    kb.row(types.InlineKeyboardButton(text=t.PAYMENT_CHECK_BTN, callback_data=f"check_mono_auto_{data['invoiceId']}_{pack_id}"))
                    await callback.message.edit_text(f"🔗 Посилання на оплату {pack['price_uah']} грн створено!", reply_markup=kb.as_markup())
                    return
                else:
                    logger.error(f"Mono API error: {data}")
            except Exception as e:
                logger.error(f"Mono request error: {e}")

    # Fallback to manual Jar if no token or API failed
    import random
    salt = random.randint(100, 999)
    code = f"ID_{callback.from_user.id}_{pack_id}_{salt}"
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text=t.OPEN_JAR_BTN, url=settings.mono_jar_url))
    kb.row(types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="shop_back"))
    
    text = (
        f"{t.MONO_MANUAL_INSTRUCTIONS.format(price=pack['price_uah'])}\n\n"
        f"{t.MONO_MANUAL_CODE.format(code=code)}\n\n"
        f"{t.MANUAL_PAYMENT_NOTICE}"
    )
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("check_mono_"))
async def check_mono(callback: types.CallbackQuery, settings):
    t = get_text(callback.from_user.language_code)
    parts = callback.data.split("_")
    
    # Check if it was an auto-payment
    if "auto" in parts:
        invoice_id = parts[3]
        pack_id = parts[4]
        pack = PACKS.get(pack_id)
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"https://api.monobank.ua/api/merchant/invoice/status?invoiceId={invoice_id}",
                    headers={"X-Token": settings.monobank_token}
                )
                data = resp.json()
                status = data.get("status")
                if status == "success":
                    await db_service.update_user_diamonds(callback.from_user.id, pack['amount'])
                    await callback.message.edit_text(t.PAYMENT_SUCCESS.format(amount=pack['amount']))
                elif status == "expired":
                    await callback.message.edit_text(t.PAYMENT_EXPIRED)
                else:
                    await callback.answer(t.PAYMENT_PENDING, show_alert=True)
                return
            except Exception as e:
                logger.error(f"Check Mono error: {e}")
    
    # Manual mode fallback
    await callback.answer(t.MANUAL_PAYMENT_NOTICE, show_alert=True)
