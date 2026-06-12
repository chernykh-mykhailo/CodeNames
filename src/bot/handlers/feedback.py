from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.core.database.service import db_service
from src.assets.texts import get_text
import logging

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
            "📝 Написати фідбек можна тільки в особистих повідомленнях з ботом."
            if settings.language == "uk"
            else "📝 You can only send feedback in private messages with the bot.",
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

    # Smart anti-spam check
    data = await state.get_data()
    last_msg_time = data.get("last_msg_time", 0)
    msg_count = data.get("msg_count", 0)

    now = time.time()
    if msg_count >= 10 and now - last_msg_time < 1.5:
        return await message.answer(t.FEEDBACK_TOO_FAST)

    if msg_count >= 50:
        return await message.answer(t.FEEDBACK_LIMIT_REACHED)

    # Check admin log configuration
    log_cfg = await db_service.get_system_setting("log_settings")
    dest = log_cfg.get("destination")
    if not dest or "feedback" not in log_cfg.get("enabled_types", []):
        return await message.answer(t.FEEDBACK_UNAVAILABLE)

    chat_id = dest.get("chat_id")
    thread_id = dest.get("thread_id")

    header = t.FEEDBACK_HEADER.format(
        name=message.from_user.full_name, id=message.from_user.id
    )

    try:
        caption = header
        if message.caption:
            caption += f"\n\n{message.caption}"

        if message.text:
            await bot.send_message(
                chat_id=chat_id,
                text=f"{header}\n\n{message.text}",
                message_thread_id=thread_id,
                parse_mode="HTML",
            )
        else:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                message_thread_id=thread_id,
                caption=caption,
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
        await message.answer(t.FEEDBACK_SEND_ERROR.format(error=e))
