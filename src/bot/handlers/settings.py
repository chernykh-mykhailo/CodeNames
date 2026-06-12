from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, PhotoSize, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import os
from src.core.database.service import db_service
from src.core.database.schemas import ChatSettings

# FSM state for skin upload and opacity setting
class SkinState(StatesGroup):
    waiting_for_photo = State()
    waiting_for_opacity = State()

class ChatColorState(StatesGroup):
    waiting_for_hex = State()

from src.core.database.schemas import ChatSettings
from src.assets.texts import get_text
from src.core.platform.game_manager import manager

router = Router()

# Set of chat IDs where chat settings were opened from the game lobby.
# Used to show a "Back to lobby" button instead of just "Close".
game_lobby_chats: set[int] = set()

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, bot: Bot, settings):
    chat_id = message.chat.id
    is_private = message.chat.type == "private"
    
    chat_settings = await db_service.get_chat_settings(chat_id)
    t = get_text(chat_settings.language)
    
    if not is_private and message.from_user.id not in settings.admin_ids:
        # Check if user is admin in groups
        member = await bot.get_chat_member(chat_id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.answer(t.ADMIN_ONLY_ERROR)
        
    await show_chat_settings(message, chat_settings)


# ---------- Skin upload handler ----------

@router.callback_query(lambda c: c.data == "set_skin")
async def set_skin(callback: types.CallbackQuery, state: FSMContext, bot: Bot, settings):
    """Initiate skin upload by setting the FSM state and prompting the user.

    The user will be asked to send a photo, which will be handled by the
    ``handle_skin_photo`` message handler defined below. The state is set to
    ``SkinState.waiting_for_photo`` so that the next photo message is routed
    correctly.
    """
    # Save the message ID of the settings message
    await state.update_data(settings_msg_id=callback.message.message_id)
    # Prompt the user to send a photo
    await callback.message.edit_text("Please send a photo for the skin.")
    # Set the FSM state for the current chat
    await state.set_state(SkinState.waiting_for_photo)
    await callback.answer()

async def show_chat_settings(message: types.Message, settings: ChatSettings, edit_message_id: int = None):
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
        status_buffs = {
            "off": "❌" if settings.language != "uk" else "❌ Вимкнено",
            "on": "✅" if settings.language != "uk" else "✅ Увімкнено",
            "interesting": "✨ Interesting" if settings.language != "uk" else "✨ Цікавий",
        }.get(settings.allow_buffs, "✅")
        
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_ALLOW_EVERYONE_START.format(status=status_everyone),
            callback_data="set_toggle_everyone"
        )])
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_BUFFS.format(status=status_buffs),
            callback_data="set_toggle_buffs"
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

        status_admin_only_settings = "✅" if settings.admin_only_settings else "❌"
        kb_list.append([types.InlineKeyboardButton(
            text=t.SETTING_ADMIN_ONLY_SETTINGS.format(status=status_admin_only_settings),
            callback_data="set_toggle_admin_only_settings"
        )])

        kb_list.append([types.InlineKeyboardButton(
            text=t.SET_TIMER_REG.format(time=settings.last_reg_timer // 60),
            callback_data="set_timer_reg"
        )])
        kb_list.append([types.InlineKeyboardButton(
            text=t.SET_TIMER_TURN.format(time=settings.last_turn_timer // 60),
            callback_data="set_timer_turn"
        )])
        # Appearance submenu (skin + opacity)
        kb_list.append([types.InlineKeyboardButton(
            text="🎨 Appearance", callback_data="set_appearance"
        )])

    # If opened from game lobby, show "Back to lobby" button instead of just Close
    if chat_id in game_lobby_chats:
        kb_list.append([
            types.InlineKeyboardButton(
                text=t.BACK_BTN, callback_data="chat_settings_back_to_lobby"
            )
        ])
    else:
        kb_list.append([types.InlineKeyboardButton(text="❌ " + (t.CLOSE_BTN if hasattr(t, "CLOSE_BTN") else "CLOSE"), callback_data="chat_settings_close")])

    kb = types.InlineKeyboardMarkup(inline_keyboard=kb_list)
    
    if edit_message_id:
        try:
            bot = message.bot if hasattr(message, "bot") else None
            if bot:
                await bot.edit_message_text(text, chat_id=chat_id, message_id=edit_message_id, reply_markup=kb, parse_mode="HTML")
                return
        except Exception:
            pass

    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(lambda c: c.data == "set_toggle_lang")
async def toggle_lang(callback: types.CallbackQuery, bot: Bot, settings):
    # Admin check only for groups
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
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
        manager.save_game(callback.message.chat.id)
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_dark")
async def toggle_dark(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
       member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
       if member.status not in ["administrator", "creator"]:
           return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
           
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.dark_mode = not chat_settings.dark_mode
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.dark_mode = chat_settings.dark_mode
        manager.save_game(callback.message.chat.id)
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_everyone")
async def toggle_everyone(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id not in settings.admin_ids:
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
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    # Cycle: "off" -> "on" -> "interesting" -> "off"
    current = chat_settings.allow_buffs
    if current == "on":
        next_mode = "interesting"
    elif current == "interesting":
        next_mode = "off"
    else:
        next_mode = "on"
        
    chat_settings.allow_buffs = next_mode
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["allow_buffs"] = next_mode
        manager.save_game(callback.message.chat.id)
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_toggle_pin")
async def toggle_pin(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.pin_message = not chat_settings.pin_message
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    # Sync the change to the active game/lobby so the two views stay in sync.
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.pin_message = chat_settings.pin_message
        manager.save_game(callback.message.chat.id)

    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "set_toggle_sheet")
async def toggle_sheet(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.spymaster_sheet = not chat_settings.spymaster_sheet
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["spymaster_sheet"] = chat_settings.spymaster_sheet
        manager.save_game(callback.message.chat.id)
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "set_toggle_past_clues")
async def toggle_past_clues(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.show_past_clues = not chat_settings.show_past_clues
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["show_past_clues"] = chat_settings.show_past_clues
        manager.save_game(callback.message.chat.id)
        
    await show_chat_settings(callback, chat_settings)
    await callback.answer()



@router.callback_query(lambda c: c.data == "set_toggle_strict")
async def toggle_strict(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.strict_clues = not chat_settings.strict_clues
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["strict_clues"] = chat_settings.strict_clues
        manager.save_game(callback.message.chat.id)

    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "set_toggle_pass")
async def toggle_pass(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.allow_pass = not chat_settings.allow_pass
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    game = manager.get_game(callback.message.chat.id)
    if game:
        game.metadata["allow_pass"] = chat_settings.allow_pass
        manager.save_game(callback.message.chat.id)

    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "chat_settings_close")
async def close_settings(callback: types.CallbackQuery):
    await callback.message.delete()

@router.callback_query(lambda c: c.data == "chat_settings_back_to_lobby")
async def chat_settings_back_to_lobby(callback: types.CallbackQuery):
    """Return to the game lobby settings from chat settings."""
    if not callback.message:
        return
    chat_id = callback.message.chat.id
    game_lobby_chats.discard(chat_id)
    game = manager.get_game(chat_id)
    if not game:
        await callback.message.delete()
        return
    from src.bot.handlers.game_setup import show_settings
    await show_settings(callback)
    await callback.answer()

@router.callback_query(lambda c: c.data == "set_timer_reg")
async def set_timer_reg_menu(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.TIME_2M, callback_data="set_conf_tmreg_120")],
        [types.InlineKeyboardButton(text=t.TIME_5M, callback_data="set_conf_tmreg_300")],
        [types.InlineKeyboardButton(text=t.TIME_10M, callback_data="set_conf_tmreg_600")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="set_timer_back")],
    ])
    await callback.message.edit_text(t.SET_TMR_REG_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("set_conf_tmreg_"))
async def set_confirm_tmreg(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.last_reg_timer = int(callback.data.replace("set_conf_tmreg_", ""))
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.reg_timer = chat_settings.last_reg_timer
        manager.save_game(callback.message.chat.id)
    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "set_timer_turn")
async def set_timer_turn_menu(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.TIME_1M, callback_data="set_conf_tmturn_60")],
        [types.InlineKeyboardButton(text=t.TIME_2M, callback_data="set_conf_tmturn_120")],
        [types.InlineKeyboardButton(text=t.TIME_3M, callback_data="set_conf_tmturn_180")],
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="set_timer_back")],
    ])
    await callback.message.edit_text(t.SET_TMR_TURN_TITLE, reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("set_conf_tmturn_"))
async def set_confirm_tmturn(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.last_turn_timer = int(callback.data.replace("set_conf_tmturn_", ""))
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    game = manager.get_game(callback.message.chat.id)
    if game:
        game.turn_timer = chat_settings.last_turn_timer
        manager.save_game(callback.message.chat.id)
    await show_chat_settings(callback, chat_settings)
    await callback.answer()


@router.callback_query(lambda c: c.data == "set_timer_back")
async def set_timer_back(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    await show_chat_settings(callback, chat_settings)


@router.callback_query(lambda c: c.data == "set_toggle_admin_only_settings")
async def toggle_admin_only_settings(callback: types.CallbackQuery, bot: Bot, settings):
    """Chat-level toggle for `admin_only_settings`.

    Only the lobby creator, bot admin or a chat admin is allowed to change
    this option, mirroring the lobby-side restriction in
    `setup_admin_only_settings_toggle`.
    """
    if not callback.message:
        return
    user_id = callback.from_user.id
    game = manager.get_game(callback.message.chat.id)

    # Bot admin and lobby creator are always allowed
    allowed = user_id in settings.admin_ids
    if not allowed and game and user_id == game.metadata.get("creator_id"):
        allowed = True
    if not allowed and callback.message.chat.type != "private":
        member = await bot.get_chat_member(callback.message.chat.id, user_id)
        if member.status in ["administrator", "creator"]:
            allowed = True
    if not allowed:
        t = get_text().ADMIN_ONLY_ERROR
        return await callback.answer(t, show_alert=True)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.admin_only_settings = not chat_settings.admin_only_settings
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)

    # Sync to active game/lobby so the two views stay in sync.
    if game:
        game.metadata["admin_only_settings"] = chat_settings.admin_only_settings
        manager.save_game(callback.message.chat.id)

    await show_chat_settings(callback, chat_settings)
    await callback.answer()


# ---------- Appearance / Skin / Opacity handlers ----------


@router.callback_query(lambda c: c.data == "set_appearance")
async def set_appearance_menu(callback: types.CallbackQuery):
    """Show the appearance sub-menu with skin + opacity options."""
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    has_skin = chat_settings.background_image is not None
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="🖼️ Set Skin", callback_data="set_skin"
        )],
        [types.InlineKeyboardButton(
            text="🗑️ Reset Skin" if has_skin else "✅ No Skin Set", callback_data="reset_skin"
        )],
        [types.InlineKeyboardButton(
            text="⚪ BG Opacity", callback_data="set_opacity"
        )],
        [types.InlineKeyboardButton(
            text="📋 Card Opacity", callback_data="set_card_opacity"
        )],
        [types.InlineKeyboardButton(
            text="🎨 Customize Colors", callback_data="set_chat_colors"
        )],
        [types.InlineKeyboardButton(
            text="◀ Back", callback_data="appearance_back"
        )],
    ])
    await callback.message.edit_text("🎨 <b>Appearance Settings</b>\n\nCustomize the board background.", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(lambda c: c.data == "reset_skin")
async def reset_skin(callback: types.CallbackQuery, bot: Bot, settings):
    """Reset skin — remove background image, restore default opacities."""
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    # Delete the old file if it exists
    old_path = chat_settings.background_image
    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception:
            pass
    chat_settings.background_image = None
    chat_settings.background_opacity = 1.0
    chat_settings.card_background_opacity = 1.0
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    # Clear renderer cache
    game = manager.get_game(callback.message.chat.id)
    if game and hasattr(game, 'renderer'):
        game.renderer.clear_cache()
    await callback.answer("Skin reset to default.", show_alert=True)
    # Show appearance menu again
    await set_appearance_menu(callback)

@router.callback_query(lambda c: c.data == "appearance_back")
async def appearance_back(callback: types.CallbackQuery):
    """Back to main settings from appearance menu."""
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    await show_chat_settings(callback, chat_settings)
    await callback.answer()

@router.message(SkinState.waiting_for_photo, F.photo)
async def handle_skin_photo(message: types.Message, state: FSMContext, bot: Bot):
    try:
        await message.delete()
    except Exception:
        pass

    state_data = await state.get_data()
    settings_msg_id = state_data.get("settings_msg_id")

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    # Ensure directory exists
    skin_dir = os.path.join("src", "assets", "skins")
    os.makedirs(skin_dir, exist_ok=True)
    file_path = os.path.join(skin_dir, f"{message.chat.id}.jpg")
    await bot.download_file(file.file_path, file_path)
    # Update settings
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    chat_settings.background_image = file_path
    chat_settings.background_opacity = 1.0  # Set background opacity to maximum
    chat_settings.card_background_opacity = 0.5  # Set card background opacity to 0.5
    await db_service.update_chat_settings(message.chat.id, chat_settings)
    # Clear renderer cache
    game = manager.get_game(message.chat.id)
    if game and hasattr(game, 'renderer'):
        game.renderer.clear_cache()

    # In some aiogram versions the FSMContext may not expose a ``finish``
    # method.  To keep compatibility we check for its existence and fall
    # back to resetting the state manually.
    if hasattr(state, "finish"):
        await state.finish()
    else:
        # ``set_state`` with ``None`` clears the current state.
        await state.set_state(None)
    await show_chat_settings(message, chat_settings, edit_message_id=settings_msg_id)

@router.callback_query(lambda c: c.data == "set_opacity")
async def set_opacity(callback: types.CallbackQuery, bot: Bot, settings):
    """Show opacity options."""
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="0.1", callback_data="set_opacity_0.1"),
         types.InlineKeyboardButton(text="0.3", callback_data="set_opacity_0.3"),
         types.InlineKeyboardButton(text="0.5", callback_data="set_opacity_0.5"),
         types.InlineKeyboardButton(text="0.7", callback_data="set_opacity_0.7"),
         types.InlineKeyboardButton(text="1.0", callback_data="set_opacity_1.0")],
    ])
    await callback.message.edit_text("Select opacity for the skin (0.1‑1.0)", reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("set_opacity_"))
async def set_opacity_value(callback: types.CallbackQuery, bot: Bot, settings):
    value = float(callback.data.split("_")[-1])
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.background_opacity = value
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    await callback.answer(f"Background opacity set to {value}")
    await show_chat_settings(callback, chat_settings)

@router.callback_query(lambda c: c.data == "set_card_opacity")
async def set_card_opacity(callback: types.CallbackQuery, bot: Bot, settings):
    """Show card background opacity options."""
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="0.1", callback_data="set_card_opacity_0.1"),
         types.InlineKeyboardButton(text="0.3", callback_data="set_card_opacity_0.3"),
         types.InlineKeyboardButton(text="0.5", callback_data="set_card_opacity_0.5"),
         types.InlineKeyboardButton(text="0.7", callback_data="set_card_opacity_0.7"),
         types.InlineKeyboardButton(text="1.0", callback_data="set_card_opacity_1.0")],
    ])
    await callback.message.edit_text("Select card background opacity (0.1‑1.0)", reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("set_card_opacity_"))
async def set_card_opacity_value(callback: types.CallbackQuery, bot: Bot, settings):
    value = float(callback.data.split("_")[-1])
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    chat_settings.card_background_opacity = value
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    await callback.answer(f"Card background opacity set to {value}")
    await show_chat_settings(callback, chat_settings)

@router.callback_query(lambda c: c.data == "set_chat_colors")
async def cb_chat_colors_menu(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
    await send_chat_color_menu(callback, "light")
    await callback.answer()

async def send_chat_color_menu(callback: types.CallbackQuery, mode="light"):
    chat_id = callback.message.chat.id
    chat_settings = await db_service.get_chat_settings(chat_id)
    t = get_text(chat_settings.language)
    
    kb_list = []
    
    # Mode selector
    light_text = "🔘 Light" if mode == "light" else "Light"
    dark_text = "🔘 Dark" if mode == "dark" else "Dark"
    kb_list.append([
        types.InlineKeyboardButton(text=f"☀️ {light_text}", callback_data=f"chat_color_mode_light"),
        types.InlineKeyboardButton(text=f"🌙 {dark_text}", callback_data=f"chat_color_mode_dark")
    ])
    
    # Base color elements
    elements = [
        ("Green", "green"), ("Red", "red"), ("Assassin", "assassin"), 
        ("Neutral", "bystander"), ("Hidden", "hidden"), ("Background", "bg"),
        ("Outline", "outline")
    ]
    
    if mode == "light":
        elements.extend([
            ("Text (Neutral Cards)", "text_dark"),
            ("Text (Colored Cards)", "text_light")
        ])
    else:
        elements.extend([
            ("Text (All Cards)", "text")
        ])
        
    for name, key in elements:
        kb_list.append([types.InlineKeyboardButton(text=f"🎨 {name}", callback_data=f"chat_color_edit_{mode}_{key}")])
        
    kb_list.append([types.InlineKeyboardButton(text="🗑️ Reset to Defaults", callback_data=f"chat_color_reset_{mode}")])
    kb_list.append([types.InlineKeyboardButton(text=t.BACK_BTN, callback_data="set_appearance")])

    kb = types.InlineKeyboardMarkup(inline_keyboard=kb_list)
    text = t.GAME_SETTINGS_COLOR_TITLE.format(mode=mode.upper()) + "\n\n" + t.GAME_SETTINGS_COLOR_PROMPT
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(lambda c: c.data.startswith("chat_color_mode_"))
async def cb_chat_color_mode(callback: types.CallbackQuery, bot: Bot, settings, state: FSMContext):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    await state.clear()
    mode = callback.data.split("_")[-1]
    await send_chat_color_menu(callback, mode)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("chat_color_edit_"))
async def cb_chat_color_edit(callback: types.CallbackQuery, bot: Bot, settings, state: FSMContext):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    parts = callback.data.split("_")
    mode = parts[3]
    key = "_".join(parts[4:])
    
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    await state.set_state(ChatColorState.waiting_for_hex)
    await state.update_data(edit_mode=mode, edit_key=key, menu_msg_id=callback.message.message_id)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t.BACK_BTN, callback_data=f"chat_color_mode_{mode}")]
    ])
    
    await callback.message.edit_text(
        t.ADMIN_COLOR_EDIT_TITLE.format(key=key, mode=mode) + "\n\n" + t.ADMIN_COLOR_EDIT_PROMPT,
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("chat_color_reset_"))
async def cb_chat_color_reset(callback: types.CallbackQuery, bot: Bot, settings):
    if callback.message.chat.type != "private" and callback.from_user.id not in settings.admin_ids:
        member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await callback.answer(get_text().ADMIN_ONLY_ERROR, show_alert=True)
            
    mode = callback.data.split("_")[-1]
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    
    if mode == "light":
        chat_settings.theme_colors_light = {}
    else:
        chat_settings.theme_colors_dark = {}
        
    await db_service.update_chat_settings(callback.message.chat.id, chat_settings)
    
    game = manager.get_game(callback.message.chat.id)
    if game:
        if hasattr(game, '_board_img_cache'):
            game._board_img_cache.clear()
        if hasattr(game, 'renderer'):
            game.renderer.clear_cache()
            
    await callback.answer(t.ADMIN_COLOR_RESET_CONFIRM, show_alert=True)
    await send_chat_color_menu(callback, mode)

@router.message(ChatColorState.waiting_for_hex)
async def process_chat_color_hex(message: types.Message, state: FSMContext, bot: Bot):
    try:
        await message.delete()
    except Exception:
        pass
        
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    text = message.text.strip()
    
    data = await state.get_data()
    mode = data.get("edit_mode", "light")
    key = data.get("edit_key")
    menu_msg_id = data.get("menu_msg_id")
    
    import re
    if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", text):
        err = await message.answer(t.ADMIN_COLOR_FORMAT_ERROR)
        await asyncio.sleep(3)
        try:
            await err.delete()
        except:
            pass
        return

    if mode == "light":
        colors = dict(chat_settings.theme_colors_light)
        colors[key] = text
        chat_settings.theme_colors_light = colors
    else:
        colors = dict(chat_settings.theme_colors_dark)
        colors[key] = text
        chat_settings.theme_colors_dark = colors
        
    await db_service.update_chat_settings(message.chat.id, chat_settings)
    
    game = manager.get_game(message.chat.id)
    if game:
        if hasattr(game, '_board_img_cache'):
            game._board_img_cache.clear()
        if hasattr(game, 'renderer'):
            game.renderer.clear_cache()
            
    await state.clear()
    
    class MockCallbackQuery:
        def __init__(self, msg):
            self.message = msg
    
    if menu_msg_id:
        try:
            mock_msg = await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=t.ADMIN_COLOR_UPDATE_SUCCESS.format(key=key, text=text),
                parse_mode="HTML"
            )
            await asyncio.sleep(1.5)
            await send_chat_color_menu(MockCallbackQuery(mock_msg), mode)
        except Exception:
            pass
