from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.database.service import db_service
from src.assets.texts import get_text
import logging

router = Router()
logger = logging.getLogger(__name__)

async def is_admin(user_id: int, settings) -> bool:
    return user_id == settings.admin_id

@router.message(Command("set_log"))
async def cmd_set_log(message: types.Message, bot: Bot, settings):
    if not await is_admin(message.from_user.id, settings):
        return

    t = get_text()
    
    # Get current settings
    log_cfg = await db_service.get_system_setting("log_settings")
    dest = log_cfg.get("destination", {})
    enabled = log_cfg.get("enabled_types", ["errors", "feedback"])
    
    chat_title = dest.get("title", "---")
    thread_id = dest.get("thread_id")
    dest_str = f"{chat_title}" + (f" (Thread: {thread_id})" if thread_id else "")

    text = (
        f"{t.ADMIN_LOG_TITLE}\n\n"
        f"{t.ADMIN_LOG_DEST.format(dest=dest_str)}\n"
        f"{t.ADMIN_LOG_TYPES.format(types=', '.join(enabled))}\n\n"
        f"{t.ADMIN_CHOOSE_ACTION}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=f"{t.ADMIN_LOG_HERE_BTN}", callback_data="admin_log_here"))
    
    # Toggle errors
    err_icon = "🟢" if "errors" in enabled else "🔴"
    builder.row(types.InlineKeyboardButton(text=f"{err_icon} {t.ADMIN_LOG_ERRORS_BTN}", callback_data="admin_log_toggle_errors"))
    
    # Toggle feedback
    fb_icon = "🟢" if "feedback" in enabled else "🔴"
    builder.row(types.InlineKeyboardButton(text=f"{fb_icon} {t.ADMIN_LOG_FEEDBACK_BTN}", callback_data="admin_log_toggle_feedback"))
    
    builder.row(types.InlineKeyboardButton(text=f"{t.ADMIN_CLOSE_BTN}", callback_data="admin_log_close"))

    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("admin_log_"))
async def callback_admin_log(callback: types.CallbackQuery, settings):
    t = get_text(callback.from_user.language_code)
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer(t.ADMIN_NO_RIGHTS, show_alert=True)

    log_cfg = await db_service.get_system_setting("log_settings")
    enabled = log_cfg.get("enabled_types", ["errors", "feedback"])
    action = callback.data.replace("admin_log_", "")

    if action == "here":
        # Set current chat as destination
        title = callback.message.chat.title or (t.WELCOME.split()[1] if callback.message.chat.type == "private" else "Private")
        log_cfg["destination"] = {
            "chat_id": callback.message.chat.id,
            "thread_id": callback.message.message_thread_id,
            "title": title
        }
        await callback.answer(t.ADMIN_LOG_SET_SUCCESS)
    
    elif action == "toggle_errors":
        if "errors" in enabled:
            enabled.remove("errors")
        else:
            enabled.append("errors")
        log_cfg["enabled_types"] = enabled
        await callback.answer(t.ADMIN_UPDATED)

    elif action == "toggle_feedback":
        if "feedback" in enabled:
            enabled.remove("feedback")
        else:
            enabled.append("feedback")
        log_cfg["enabled_types"] = enabled
        await callback.answer(t.ADMIN_UPDATED)

    elif action == "close":
        return await callback.message.delete()

    await db_service.update_system_setting("log_settings", log_cfg)
    
    # Refresh message
    dest = log_cfg.get("destination", {})
    chat_title = dest.get("title", "---")
    thread_id = dest.get("thread_id")
    dest_str = f"{chat_title}" + (f" (Thread: {thread_id})" if thread_id else "")
    
    text = (
        f"{t.ADMIN_LOG_TITLE}\n\n"
        f"{t.ADMIN_LOG_DEST.format(dest=dest_str)}\n"
        f"{t.ADMIN_LOG_TYPES.format(types=', '.join(enabled))}\n\n"
        f"{t.ADMIN_CHOOSE_ACTION}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=f"{t.ADMIN_LOG_HERE_BTN}", callback_data="admin_log_here"))
    
    # Toggle errors
    err_icon = "🟢" if "errors" in enabled else "🔴"
    builder.row(types.InlineKeyboardButton(text=f"{err_icon} {t.ADMIN_LOG_ERRORS_BTN}", callback_data="admin_log_toggle_errors"))
    
    # Toggle feedback
    fb_icon = "🟢" if "feedback" in enabled else "🔴"
    builder.row(types.InlineKeyboardButton(text=f"{fb_icon} {t.ADMIN_LOG_FEEDBACK_BTN}", callback_data="admin_log_toggle_feedback"))
    
    builder.row(types.InlineKeyboardButton(text=f"{t.ADMIN_CLOSE_BTN}", callback_data="admin_log_close"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
