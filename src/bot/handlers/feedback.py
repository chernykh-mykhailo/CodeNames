from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.core.database.service import db_service
from src.assets.texts import get_text
import logging
import asyncio

logger = logging.getLogger(__name__)
router = Router()

class FeedbackState(StatesGroup):
    waiting_for_feedback = State()

@router.message(Command("feedback"))
async def cmd_feedback(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        settings = await db_service.get_chat_settings(message.chat.id)
        t = get_text(settings.language)
        bot_info = await message.bot.get_me()
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="💬 Перейти в ПП" if settings.language == "uk" else "💬 Go to PM",
                        url=f"https://t.me/{bot_info.username}?start=feedback"
                    )
                ]
            ]
        )
        await message.reply(
            "📝 Написати фідбек можна тільки в особистих повідомленнях з ботом." if settings.language == "uk" else "📝 You can only send feedback in private messages with the bot.",
            reply_markup=kb
        )
        return

    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)

    # Check admin log configuration
    log_cfg = await db_service.get_system_setting("log_settings")
    dest = log_cfg.get("destination")
    if not dest or "feedback" not in log_cfg.get("enabled_types", []):
        return await message.answer(t.FEEDBACK_UNAVAILABLE)

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
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(settings.language)
    await state.clear()
    await callback.message.edit_text(t.FEEDBACK_FINISHED)
    await callback.answer()

@router.message(Command("done"), FeedbackState.waiting_for_feedback)
async def cmd_done_feedback(message: types.Message, state: FSMContext):
    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)
    await state.clear()
    await message.answer(t.FEEDBACK_FINISHED)

@router.message(FeedbackState.waiting_for_feedback)
async def process_feedback_ticket(message: types.Message, state: FSMContext, bot: Bot):
    import time
    settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(settings.language)

    # Anti‑spam checks
    data = await state.get_data()
    last_msg_time = data.get("last_msg_time", 0)
    msg_count = data.get("msg_count", 0)
    now = time.time()
    if msg_count >= 10 and now - last_msg_time < 1.5:
        return await message.answer(t.FEEDBACK_TOO_FAST)
    if msg_count >= 50:
        return await message.answer(t.FEEDBACK_LIMIT_REACHED)

    # Admin log configuration
    log_cfg = await db_service.get_system_setting("log_settings")
    dest = log_cfg.get("destination")
    if not dest or "feedback" not in log_cfg.get("enabled_types", []):
        return await message.answer(t.FEEDBACK_UNAVAILABLE)

    chat_id = dest.get("chat_id")
    thread_id = dest.get("thread_id")
    try:
        chat_id = int(chat_id) if chat_id is not None else None
        thread_id = int(thread_id) if thread_id is not None else None
    except (ValueError, TypeError):
        logger.error("Invalid chat_id or thread_id in log settings for feedback")
        return await message.answer(t.FEEDBACK_UNAVAILABLE)
    if chat_id is None:
        logger.error("Feedback log destination missing chat_id")
        return await message.answer(t.FEEDBACK_UNAVAILABLE)

    header = t.FEEDBACK_HEADER.format(name=message.from_user.full_name, id=message.from_user.id)
    try:
        caption = header
        if message.caption:
            caption += f"\n\n{message.caption}"

        send_kwargs = {"chat_id": chat_id, "parse_mode": "HTML"}
        if thread_id is not None:
            send_kwargs["message_thread_id"] = thread_id

        success = False
        last_error = None
        for attempt in range(3):
            try:
                if message.text:
                    send_kwargs["text"] = f"{header}\n\n{message.text}"
                    await bot.send_message(**send_kwargs)
                else:
                    send_kwargs.update({
                        "from_chat_id": message.chat.id,
                        "message_id": message.message_id,
                        "caption": caption,
                    })
                    await bot.copy_message(**send_kwargs)
                success = True
                break
            except Exception as e:
                last_error = e
                logger.error(f"Feedback send attempt {attempt+1}/3 failed: {e}")
                await asyncio.sleep(0.5)
        if not success:
            raise last_error or Exception("Unknown send error")

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
        logger.error(f"Feedback send error: {e}")
        await message.answer(t.FEEDBACK_SEND_ERROR.format(error=e))
