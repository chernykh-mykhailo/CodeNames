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

    # Auto Bot Settings (available for both private and group)
    status_auto_bot = "✅" if settings.auto_bot_enabled else "❌"
    kb_list.append([types.InlineKeyboardButton(
        text=t.SETTING_AUTO_BOT.format(status=status_auto_bot),
        callback_data="set_toggle_auto_bot"
    )])
    
    if settings.auto_bot_enabled:
        difficulty_display = {
            "easy": "🟢 Easy",
            "medium": "🟡 Medium", 
            "hard": "🔴 Hard"
        }.get(settings.auto_bot_difficulty, "🟡 Medium")
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_AUTO_BOT_DIFFICULTY.format(level=difficulty_display),
            callback_data="set_auto_bot_difficulty"
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
            text=t.SETTING_PIN_MESSAGE.format(status=status_pin),
            callback_data="set_toggle_pin"
        )])

        status_sheet = "✅" if settings.spymaster_sheet else "❌"
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_CAPTAIN_SHEET.format(status=status_sheet),
            callback_data="set_toggle_sheet"
        )])

        status_past_clues = "✅" if settings.show_past_clues else "❌"
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_PAST_CLUES.format(status=status_past_clues),
            callback_data="set_toggle_past_clues"
        )])

        status_strict = "✅" if settings.strict_clues else "❌"
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_STRICT_CLUES.format(status=status_strict),
            callback_data="set_toggle_strict"
        )])

        status_pass = "✅" if settings.allow_pass else "❌"
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_ALLOW_PASS.format(status=status_pass),
            callback_data="set_toggle_pass"
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


@router.callback_query(lambda c: c.data == "set_toggle_sheet")
async def toggle_sheet(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.spymaster_sheet = not chat_settings.spymaster_sheet
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["spymaster_sheet"] = chat_settings.spymaster_sheet
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "set_toggle_past_clues")
async def toggle_past_clues(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.show_past_clues = not chat_settings.show_past_clues
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["show_past_clues"] = chat_settings.show_past_clues
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()



@router.callback_query(lambda c: c.data == "set_toggle_strict")
async def toggle_strict(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.strict_clues = not chat_settings.strict_clues
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["strict_clues"] = chat_settings.strict_clues

    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "set_toggle_pass")
async def toggle_pass(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.allow_pass = not chat_settings.allow_pass
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["allow_pass"] = chat_settings.allow_pass

    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "set_toggle_buttons")
async def toggle_buttons(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id != settings.admin_id:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
        
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    if chat_settings.board_size > 8:
        return await callback.answer(t.TOO_MANY_WORDS_BUTTON_BOARD, show_alert=True)

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
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    if not game:
        return await callback.answer(t.NO_ACTIVE_GAME_SESSION)

    current_mode = game.metadata.get("mode", "Classic")
    if current_mode == "Classic":
        new_mode = "Duet"
    elif current_mode == "Duet":
        new_mode = "Hardcore"
    else:
        new_mode = "Classic"
    game.metadata["mode"] = new_mode

    await show_chat_settings(callback, chat_settings)
    await callback.answer(t.MODE_CHANGED.format(mode=new_mode))

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
    t = get_text(chat_settings.language)
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
    await callback.answer(t.SETUP_SIZE_SET_MSG.format(size=size))

@router.callback_query(lambda c: c.data == "set_board_size_back")
async def set_board_size_back(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    await show_chat_settings(callback, chat_settings)

@router.callback_query(lambda c: c.data == "set_toggle_auto_bot")
async def toggle_auto_bot(callback: types.CallbackQuery, bot: Bot, settings):
    # Only allow admin to toggle auto-bot (not just any group admin)
    if callback.from_user.id != settings.admin_id:
        return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.auto_bot_enabled = not chat_settings.auto_bot_enabled
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["auto_bot_enabled"] = chat_settings.auto_bot_enabled
        game.metadata["auto_bot_difficulty"] = chat_settings.auto_bot_difficulty

    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_auto_bot_difficulty")
async def change_auto_bot_difficulty(callback: types.CallbackQuery, bot: Bot, settings):
    # Only allow admin to change auto-bot difficulty (not just any group admin)
    if callback.from_user.id != settings.admin_id:
        return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)

    # Cycle through difficulties
    difficulties = ["easy", "medium", "hard"]
    current_index = difficulties.index(chat_settings.auto_bot_difficulty) if chat_settings.auto_bot_difficulty in difficulties else 1
    next_difficulty = difficulties[(current_index + 1) % len(difficulties)]

    chat_settings.auto_bot_difficulty = next_difficulty
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["auto_bot_difficulty"] = chat_settings.auto_bot_difficulty

    await show_chat_settings(callback, chat_settings)

    difficulty_names = {
        "easy": t.DIFFICULTY_EASY if hasattr(t, "DIFFICULTY_EASY") else "Easy",
        "medium": t.DIFFICULTY_MEDIUM if hasattr(t, "DIFFICULTY_MEDIUM") else "Medium",
        "hard": t.DIFFICULTY_HARD if hasattr(t, "DIFFICULTY_HARD") else "Hard"
    }
    await callback.answer(t.AUTO_BOT_DIFFICULTY_CHANGED.format(level=difficulty_names[next_difficulty]))

@router.callback_query(lambda c: c.data == "chat_settings_close")
async def close_settings(callback: types.CallbackQuery):
    await callback.message.delete()
