from aiogram import Router, types, Bot
from aiogram.filters import Command
from src.core.database.service import db_service
from src.core.database.schemas import ChatSettings
from src.assets.texts import get_text

router = Router()

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        return # PM settings might be different later
        
    t = get_text()
    
    # Check if user is admin
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return await message.answer(t.ADMIN_ONLY_ERROR)
        
    settings = await db_service.get_chat_settings(message.chat.id)
    await show_chat_settings(message, settings)

async def show_chat_settings(message: types.Message, settings: ChatSettings):
    t = get_text()
    
    status_everyone = "✅" if settings.allow_everyone_start else "❌"
    status_buffs = "✅" if settings.allow_buffs else "❌"
    status_dark = "✅" if settings.dark_mode else "❌"
    text = t.CHAT_SETTINGS_TITLE
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text=t.SETTING_ALLOW_EVERYONE_START.format(status=status_everyone),
            callback_data="set_toggle_everyone"
        )],
        [types.InlineKeyboardButton(
            text=t.SETTING_BUFFS.format(status=status_buffs),
            callback_data="set_toggle_buffs"
        )],
        [types.InlineKeyboardButton(
            text=t.SETTING_DARK_MODE.format(status=status_dark),
            callback_data="set_toggle_dark"
        )],
        [types.InlineKeyboardButton(text=t.BACK_BTN if hasattr(t, "BACK_BTN") else "❌ CLOSE", callback_data="chat_settings_close")]
    ])
    
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(lambda c: c.data == "set_toggle_everyone")
async def toggle_everyone(callback: types.CallbackQuery, bot: Bot):
    # Check if user is admin again for safety
    member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    settings.allow_everyone_start = not settings.allow_everyone_start
    await db_service.update_chat_settings(callback.message.chat.id, settings)
    
    await show_chat_settings(callback, settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_buffs")
async def toggle_buffs(callback: types.CallbackQuery, bot: Bot):
    member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    settings.allow_buffs = not settings.allow_buffs
    await db_service.update_chat_settings(callback.message.chat.id, settings)
    
    t = get_text()
    status_text = "ON" if settings.allow_buffs else "OFF"
    await callback.answer(t.BUFFS_ENABLED_MSG.format(status=status_text))
    await show_chat_settings(callback, settings)

@router.callback_query(lambda c: c.data == "set_toggle_dark")
async def toggle_dark_mode(callback: types.CallbackQuery, bot: Bot):
    member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    settings.dark_mode = not settings.dark_mode
    await db_service.update_chat_settings(callback.message.chat.id, settings)
    
    await callback.answer(get_text().ADMIN_UPDATED)
    await show_chat_settings(callback, settings)

@router.callback_query(lambda c: c.data == "chat_settings_close")
async def close_settings(callback: types.CallbackQuery):
    await callback.message.delete()
