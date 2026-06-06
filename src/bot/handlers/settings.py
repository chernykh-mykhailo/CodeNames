from aiogram import Router, types, Bot
from aiogram.filters import Command
from src.core.database.service import db_service
from src.core.database.schemas import ChatSettings
from src.assets.texts import get_text
from src.core.platform.game_manager import manager

router = Router()

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, bot: Bot, settings):
    chat_id = message.chat.id
    is_private = message.chat.type == "private"
    
    chat_settings = await db_service.get_chat_settings(chat_id)
    t = get_text(chat_settings.language)
    
    if not is_private and message.from_user.id != settings.admin_id:
        # Check if user is admin in groups
        member = await bot.get_chat_member(chat_id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ADMIN_ONLY_ERROR)
        
    await show_chat_settings(message, chat_settings)

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
        status_buttons = "✅" if settings.button_board else "❌"
        
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_ALLOW_EVERYONE_START.format(status=status_everyone),
            callback_data="set_toggle_everyone"
        )])
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_BUFFS.format(status=status_buffs),
            callback_data="set_toggle_buffs"
        )])
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_BUTTON_BOARD.format(status=status_buttons),
            callback_data="set_toggle_buttons"
        )])
        
        status_pin = "✅" if settings.pin_message else "❌"
        kb_list.append([types.InlineKeyboardButton(
            text=f"📌 Закріпити повідомлення: {status_pin}" if settings.language == "uk" else f"📌 Pin message: {status_pin}",
            callback_data="set_toggle_pin"
        )])
        
        # 4. Board Size Toggle
        kb_list.append([types.InlineKeyboardButton(
            text=t.SET_BOARD_SIZE.format(size=settings.board_size),
            callback_data="set_toggle_board_size"
        )])
        
        # 3. Game Mode (for active games)
        game = manager.get_game(chat_id)
        if game:
            mode = game.metadata.get("mode", "Classic")
            kb_list.append([types.InlineKeyboardButton(
                text=t.SET_MODE.format(mode=mode),
                callback_data="set_toggle_mode"
            )])

    kb_list.append([types.InlineKeyboardButton(text="❌ " + (t.CLOSE_BTN if hasattr(t, "CLOSE_BTN") else "CLOSE"), callback_data="chat_settings_close")])
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=kb_list)
    
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(lambda c: c.data == "set_toggle_lang")
async def toggle_lang(callback: types.CallbackQuery, bot: Bot, settings):
    # Admin check only for groups
    if callback.message.chat.type != "private" and callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.language = "en" if chat_settings.language == "uk" else "uk"
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    # Update active game if exists
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.language = chat_settings.language
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_dark")
async def toggle_dark(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id != settings.admin_id:
       member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
       if member.status not in ["administrator", "creator"]:
           return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
           
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.dark_mode = not chat_settings.dark_mode
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.dark_mode = chat_settings.dark_mode
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_everyone")
async def toggle_everyone(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.allow_everyone_start = not chat_settings.allow_everyone_start
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_buffs")
async def toggle_buffs(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.allow_buffs = not chat_settings.allow_buffs
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_pin")
async def toggle_pin(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.pin_message = not chat_settings.pin_message
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    await show_chat_settings(callback, chat_settings)
    await callback.answer()



@router.callback_query(lambda c: c.data == "set_toggle_buttons")
async def toggle_buttons(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    if chat_settings.board_size > 8:
        return await callback.answer("❌ Слів занадто багато для кнопкового відображення!", show_alert=True)
        
    chat_settings.button_board = not chat_settings.button_board
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.button_board = chat_settings.button_board
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_mode")
async def toggle_mode(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    game = manager.get_game(callback.message.chat.id)
    if not game:
        return await callback.answer("❌ No active game session")
        
    current_mode = game.metadata.get("mode", "Classic")
    new_mode = "Duet" if current_mode == "Classic" else "Classic"
    game.metadata["mode"] = new_mode
    
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    await show_chat_settings(callback, chat_settings)
    await callback.answer(f"Mode: {new_mode}")

@router.callback_query(lambda c: c.data == "set_toggle_board_size")
async def choose_board_size_menu(callback: types.CallbackQuery):
    if not callback.message:
        return
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    
    buttons = []
    row1 = [types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"set_size_{i}") for i in range(4, 8)]
    buttons.append(row1)
    row2 = [types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"set_size_{i}") for i in range(8, 12)]
    buttons.append(row2)
    row3 = [types.InlineKeyboardButton(text=f"{i}x{i}", callback_data=f"set_size_{i}") for i in range(12, 14)]
    buttons.append(row3)
    
    buttons.append([types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="set_board_size_back")])
    
    await callback.message.edit_text(t.SET_BOARD_SIZE_TITLE, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data.startswith("set_size_"))
async def set_board_size_confirm(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    size = int(callback.data.replace("set_size_", ""))
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.board_size = size
    
    if size > 8:
        chat_settings.button_board = False
        
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.board_size = size
        if size > 8:
            game.button_board = False
            
    await show_chat_settings(callback, chat_settings)
    await callback.answer(f"Size set to {size}x{size}")

@router.callback_query(lambda c: c.data == "set_board_size_back")
async def set_board_size_back(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    await show_chat_settings(callback, chat_settings)

@router.callback_query(lambda c: c.data == "chat_settings_close")
async def close_settings(callback: types.CallbackQuery):
    await callback.message.delete()
