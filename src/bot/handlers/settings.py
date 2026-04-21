from aiogram import Router, types, Bot
from aiogram.filters import Command
from src.core.database.service import db_service
from src.core.database.schemas import ChatSettings
from src.assets.texts import get_text
from src.core.platform.game_manager import manager

router = Router()

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    is_private = message.chat.type == "private"
    
    settings = await db_service.get_chat_settings(chat_id)
    t = get_text(settings.language)
    
    if not is_private:
        # Check if user is admin in groups
        member = await bot.get_chat_member(chat_id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ADMIN_ONLY_ERROR)
        
    await show_chat_settings(message, settings)

async def show_chat_settings(message: types.Message, settings: ChatSettings):
    t = get_text(settings.language)
    chat_id = message.chat.id if hasattr(message, "chat") else message.message.chat.id
    is_private = (message.chat.type == "private") if hasattr(message, "chat") else (message.message.chat.type == "private")
    
    text = t.CHAT_SETTINGS_TITLE
    kb_list = []
    
    # 1. Language Toggle
    lang_display = "🇺🇦 UK" if settings.language == "uk" else "🇺🇸 EN"
    kb_list.append([types.InlineKeyboardButton(
        text=t.SET_LANG.format(lang=lang_display),
        callback_data="set_toggle_lang"
    )])

    # 2. Dark Mode Toggle
    status_dark = "✅" if settings.dark_mode else "❌"
    kb_list.append([types.InlineKeyboardButton(
        text=t.SETTING_DARK_MODE.format(status=status_dark),
        callback_data="set_toggle_dark"
    )])

    if not is_private:
        # Group-specific settings
        status_everyone = "✅" if settings.allow_everyone_start else "❌"
        status_buffs = "✅" if settings.allow_buffs else "❌"
        
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_ALLOW_EVERYONE_START.format(status=status_everyone),
            callback_data="set_toggle_everyone"
        )])
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_BUFFS.format(status=status_buffs),
            callback_data="set_toggle_buffs"
        )])
        
        # 3. Game Mode (for active games)
        game = manager.get_game(chat_id)
        if game:
            mode = game.metadata.get("mode", "Classic")
            kb_list.append([types.InlineKeyboardButton(
                text=t.SET_MODE.format(mode=mode),
                callback_data="set_toggle_mode"
            )])

    kb_list.append([types.InlineKeyboardButton(text="❌ " + t.CLOSE_BTN if hasattr(t, "CLOSE_BTN") else "❌ CLOSE", callback_data="chat_settings_close")])
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=kb_list)
    
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(lambda c: c.data == "set_toggle_lang")
async def toggle_lang(callback: types.CallbackQuery, bot: Bot):
    # Admin check only for groups
    if callback.message.chat.type != "private":
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    settings.language = "en" if settings.language == "uk" else "uk"
    await db_service.update_chat_settings(callback.message.chat.id, settings)
    
    # Update active game if exists
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.language = settings.language
        
    await show_chat_settings(callback, settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_dark")
async def toggle_dark(callback: types.CallbackQuery, bot: Bot):
    if callback.message.chat.type != "private":
       member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
       if member.status not in ["administrator", "creator"]:
           return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
           
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    settings.dark_mode = not settings.dark_mode
    await db_service.update_chat_settings(callback.message.chat.id, settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.dark_mode = settings.dark_mode
        
    await show_chat_settings(callback, settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_everyone")
async def toggle_everyone(callback: types.CallbackQuery, bot: Bot):
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
    
    await show_chat_settings(callback, settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_mode")
async def toggle_mode(callback: types.CallbackQuery, bot: Bot):
    member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return await callback.answer("❌ No active game session")
        
    current_mode = game.metadata.get("mode", "Classic")
    new_mode = "Duet" if current_mode == "Classic" else "Classic"
    game.metadata["mode"] = new_mode
    
    settings = await db_service.get_chat_settings(callback.message.chat.id)
    await show_chat_settings(callback, settings)
    await callback.answer(f"Mode: {new_mode}")

@router.callback_query(lambda c: c.data == "chat_settings_close")
async def close_settings(callback: types.CallbackQuery):
    await callback.message.delete()
