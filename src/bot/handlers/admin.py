from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.core.database.service import db_service
from src.assets.texts import get_text, b
from src.games.codenames.renderer import BoardRenderer
from src.games.codenames.engine import CardColor
from aiogram.types import BufferedInputFile
import logging
import re
import io

router = Router()
logger = logging.getLogger(__name__)

async def is_admin(user_id: int, settings) -> bool:
    return user_id == settings.admin_id

@router.message(Command("admin"))
async def cmd_admin_panel(message: types.Message, settings):
    if not await is_admin(message.from_user.id, settings):
        return

    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)

    text = t.ADMIN_PANEL_TITLE + t.ADMIN_DEBUG_INFO

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=t.ADMIN_LOG_SETTINGS_BTN, callback_data="admin_panel_logs"))
    builder.row(types.InlineKeyboardButton(text=t.ADMIN_COLOR_SETTINGS_BTN, callback_data="admin_panel_colors"))
    builder.row(
        types.InlineKeyboardButton(text=t.ADMIN_TEST_RENDER_UA_BTN, callback_data="admin_panel_tr"),
        types.InlineKeyboardButton(text=t.ADMIN_TEST_RENDER_EN_BTN, callback_data="admin_panel_tren")
    )
    builder.row(types.InlineKeyboardButton(text=t.CLOSE_BTN, callback_data="admin_log_close"))

    # Send with HTML parse_mode to properly handle HTML tags in the text
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "admin_panel_logs")
async def cb_admin_panel_logs(callback: types.CallbackQuery, bot: Bot, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
    await callback.message.delete()
    await cmd_set_log(callback.message, bot, settings)
    await callback.answer()


@router.callback_query(F.data == "admin_panel_colors")
async def cb_admin_panel_colors(callback: types.CallbackQuery, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
    await callback.message.delete()
    await send_color_menu(callback.message, "light")
    await callback.answer()


@router.callback_query(F.data == "admin_panel_tr")
async def cb_admin_panel_tr(callback: types.CallbackQuery, bot: Bot, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
    await cmd_test_render(callback.message, settings)
    await callback.answer()


@router.callback_query(F.data == "admin_panel_tren")
async def cb_admin_panel_tren(callback: types.CallbackQuery, bot: Bot, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
    await cmd_test_render_en(callback.message, settings)
    await callback.answer()

@router.callback_query(F.data == "admin_panel_debug_autobot")
async def cb_admin_panel_debug_autobot(callback: types.CallbackQuery, bot: Bot, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()

    # Get the game from the chat where admin panel was opened
    game = None
    try:
        from src.core.platform.game_manager import manager
        from src.games.codenames.game import CodeNamesGame
        game = manager.get_game(callback.message.chat.id)
        if not isinstance(game, CodeNamesGame) or game.status != "in_progress":
            game = None
    except:
        game = None

    if not game:
        chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
        t = get_text(chat_settings.language)
        return await callback.answer(t.ADMIN_NO_ACTIVE_GAME, show_alert=True)

    # Check if auto-bot is enabled
    if not game.metadata.get("auto_bot_enabled", False):
        chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
        t = get_text(chat_settings.language)
        return await callback.answer("Auto-bot is not enabled in the current game", show_alert=True)

    # Generate debug info
    from src.games.codenames.ai_bot import AIBot

    # Create AI bot instance
    ai_bot = AIBot(language=game.language, difficulty=game.metadata.get("auto_bot_difficulty", "medium"))

    # Generate clue with debug info
    clue_result = ai_bot.generate_clue(game.engine, game.engine.current_turn)

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)

    if not clue_result:
        return await callback.answer("Auto-bot could not generate a clue for the current board state", show_alert=True)

    clue_word, count, explanation = clue_result

    # Send debug info to admin in private message
    debug_msg = f"🔍 <b>Auto-Bot Debug Info</b>\n"
    display_count = "∞" if count == 0 else count
    debug_msg += f"📢 Clue: <b>{clue_word.upper()} {display_count}</b>\n"
    debug_msg += f"💡 Explanation: <i>{explanation}</i>\n"
    debug_msg += f"\n🎯 Current Team: {'🟢 Green' if game.engine.current_turn == Team.GREEN else '🔴 Red'}\n"

    # Add board state info
    team_words = []
    other_words = []
    assassin_words = []
    bystander_words = []

    for card in game.engine.board:
        if not card.is_revealed:
            if game.engine.mode == "duet":
                color_a = game.engine.get_duet_color(card.index, "a")
                color_b = game.engine.get_duet_color(card.index, "b")
                if color_a == CardColor.GREEN or color_b == CardColor.GREEN:
                    team_words.append(card.word)
                elif color_a == CardColor.ASSASSIN or color_b == CardColor.ASSASSIN:
                    assassin_words.append(card.word)
                else:
                    bystander_words.append(card.word)
            else:
                if card.color.value == game.engine.current_turn.value:
                    team_words.append(card.word)
                elif card.color == CardColor.ASSASSIN:
                    assassin_words.append(card.word)
                elif card.color in [CardColor.GREEN, CardColor.RED]:
                    other_words.append(card.word)
                else:
                    bystander_words.append(card.word)

    debug_msg += f"\n🟢 Target Words: {', '.join(team_words) if team_words else 'None'}\n"
    debug_msg += f"🔴 Other Team Words: {', '.join(other_words) if other_words else 'None'}\n"
    debug_msg += f"💀 Assassin Words: {', '.join(assassin_words) if assassin_words else 'None'}\n"
    debug_msg += f"⚪ Bystander Words: {', '.join(bystander_words) if bystander_words else 'None'}"

    try:
        await bot.send_message(callback.from_user.id, debug_msg, parse_mode="HTML")
        await callback.answer("📊 Auto-bot debug info sent to your private messages", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Error sending debug info: {e}", show_alert=True)


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
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
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

@router.message(Command("give"))
async def cmd_give_diamonds(message: types.Message, bot: Bot, settings):
    if not await is_admin(message.from_user.id, settings):
        return

    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)

    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer(t.ADMIN_GIVE_FORMAT_ERROR)

    try:
        amount = int(parts[1])
    except ValueError:
        return await message.answer(t.ADMIN_GIVE_AMOUNT_ERROR)

    target_user_id = None
    target_name = t.ROLE_USER
    target_name = t.ROLE_USER

    # 1. Check reply
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.full_name
        await db_service.ensure_user(
            target_user_id, 
            target_name, 
            message.reply_to_message.from_user.username
        )
    # 2. Check username/id in args
    elif len(parts) >= 3:
        input_val = parts[2]
        if input_val.startswith("@") or not input_val.isdigit():
            user = await db_service.get_user_by_username(input_val)
            if user:
                target_user_id = user.id
                target_name = user.full_name
            else:
                # If not in DB, maybe it's just a username string, but we need ID
                return await message.answer(t.ADMIN_USER_NOT_FOUND.format(user=input_val))
        else:
            target_user_id = int(input_val)
            await db_service.ensure_user(target_user_id)

    if not target_user_id:
        return await message.answer(t.ADMIN_GIVE_USER_REQUIRED)

    success = await db_service.update_user_diamonds(target_user_id, amount)
    if success:
        # Escape HTML special characters to prevent parsing errors
        from html import escape
        safe_name = escape(target_name)
        await message.answer(t.ADMIN_GIVE_SUCCESS.format(amount=amount, name=safe_name, id=target_user_id))
        # Notify user if possible
        try:
            await bot.send_message(target_user_id, t.ADMIN_GIVE_NOTIFY.format(amount=amount))
        except:
            pass
    else:
        await message.answer(t.ADMIN_GIVE_ERROR)

@router.message(F.reply_to_message)
async def handle_admin_reply(message: types.Message, bot: Bot, settings):
    # Only process if it's a private chat with admin OR it's the designated log chat
    is_private_admin = (message.chat.type == "private" and await is_admin(message.from_user.id, settings))
    
    log_cfg = await db_service.get_system_setting("log_settings")
    dest = log_cfg.get("destination", {})
    is_log_chat = (message.chat.id == dest.get("chat_id"))

    if not (is_private_admin or is_log_chat):
        # NOT an admin context - let the event bubble up (or down the routers)
        # However, since this handler MATCHES the filter F.reply_to_message,
        # we must EXPLICITLY REJECT it in the filter if we want other routers to see it.
        return

    reply = message.reply_to_message
    if not (reply.text or reply.caption):
        return

    # Check if this is a feedback message
    # Format: 👤 [ID] Name:
    text_to_search = reply.text or reply.caption
    
    # Improved regex for ticket-style header
    match = re.search(r"\[(\d+)\]", text_to_search)
    if not match:
        return

    user_id = int(match.group(1))
    
    try:
        # If admin just sends text, we wrap it in template
        if message.text:
             user_settings = await db_service.get_chat_settings(user_id)
             t = get_text(user_settings.language)
             await bot.send_message(
                 chat_id=user_id,
                 text=t.FEEDBACK_REPLY_TEMPLATE.format(text=message.text)
             )
        else:
             # If admin sends media, copy it
             await bot.copy_message(
                 chat_id=user_id,
                 from_chat_id=message.chat.id,
                 message_id=message.message_id
             )
        chat_settings = await db_service.get_chat_settings(message.chat.id)
        t = get_text(chat_settings.language)
        await message.reply(t.ADMIN_REPLY_SENT)
    except Exception as e:
        chat_settings = await db_service.get_chat_settings(message.chat.id)
        t = get_text(chat_settings.language)
        await message.reply(t.ADMIN_REPLY_ERROR.format(error=e))

@router.message(Command("test_render", "tr"))
async def cmd_test_render(message: types.Message, settings):
    if not await is_admin(message.from_user.id, settings):
        return

    try:
        renderer = BoardRenderer()
        light_colors = await db_service.get_system_setting("theme_colors_light")
        dark_colors = await db_service.get_system_setting("theme_colors_dark")
        renderer.set_custom_colors(light_colors, dark_colors)
        logger.info(f"Renderer initialized with font_path={renderer.font_path}")
        
        # Get chat settings for background image and opacity
        chat_settings = await db_service.get_chat_settings(message.chat.id)
        
        # Create dummy cards for a 5x5 board
        dummy_cards = []
        colors = [CardColor.GREEN] * 9 + [CardColor.RED] * 8 + [CardColor.BYSTANDER] * 7 + [CardColor.ASSASSIN] * 1
        import random
        random.shuffle(colors)
        
        test_words = [
            "ЯБЛУКО", "ДЕРЕВО", "КНИГА", "НЕБО", "МОРЕ",
            "КОМП'ЮТЕР", "ТЕЛЕФОН", "МАШИНА", "СОНЦЕ", "ГІТАРА",
            "ТЕЛЕВІЗОР", "ДІМ", "ВІКНО", "СТІЛ", "СТІЛЕЦЬ",
            "ДОРОГА", "МАГАЗИН", "ШКОЛА", "ЛІКАРНЯ", "МІСТО",
            "КРАЇНА", "ПЛАНЕТА", "КОСМОС", "ЗІРКА", "ЛІТАК"
        ]
        
        for i in range(25):
            dummy_cards.append({
                "word": test_words[i],
                "color": colors[i].value,
                "is_revealed": random.choice([True, False]) if i < 15 else False
            })

        # Render all images
        logger.info("Rendering Light Mode...")
        light_img = renderer.render_board(
            dummy_cards, 
            spymaster_view=False, 
            dark_mode=False,
            background_image=chat_settings.background_image,
            background_opacity=chat_settings.background_opacity,
            card_background_opacity=chat_settings.card_background_opacity
        )
        
        logger.info("Rendering Dark Mode...")
        dark_img = renderer.render_board(
            dummy_cards, 
            spymaster_view=False, 
            dark_mode=True,
            background_image=chat_settings.background_image,
            background_opacity=chat_settings.background_opacity,
            card_background_opacity=chat_settings.card_background_opacity
        )
        
        logger.info("Rendering Spymaster View (Light)...")
        spy_light = renderer.render_board(
            dummy_cards, 
            spymaster_view=True, 
            dark_mode=False,
            background_image=chat_settings.background_image,
            background_opacity=chat_settings.background_opacity,
            card_background_opacity=chat_settings.card_background_opacity
        )
        
        logger.info("Rendering Spymaster View (Dark)...")
        spy_dark = renderer.render_board(
            dummy_cards, 
            spymaster_view=True, 
            dark_mode=True,
            background_image=chat_settings.background_image,
            background_opacity=chat_settings.background_opacity,
            card_background_opacity=chat_settings.card_background_opacity
        )
        
        # Group photos into a media group
        media_group = [
            types.InputMediaPhoto(
                media=BufferedInputFile(light_img.getvalue(), filename="light_mode.png"),
                caption="☀️ <b>Light Mode Preview</b>"
            ),
            types.InputMediaPhoto(
                media=BufferedInputFile(dark_img.getvalue(), filename="dark_mode.png"),
                caption="🌙 <b>Dark Mode Preview</b>"
            ),
            types.InputMediaPhoto(
                media=BufferedInputFile(spy_light.getvalue(), filename="spy_light.png"),
                caption="👨‍✈️ <b>Spymaster View (Light)</b>"
            ),
            types.InputMediaPhoto(
                media=BufferedInputFile(spy_dark.getvalue(), filename="spy_dark.png"),
                caption="👨‍✈️ <b>Spymaster View (Dark)</b>"
            )
        ]
        
        await message.answer_media_group(media_group)
        
        logger.info("Test render complete.")
    except Exception as e:
        logger.error(f"Error in test_render: {e}", exc_info=True)
        t = get_text()
        await message.answer(t.FEEDBACK_SEND_ERROR.format(error=e))

@router.message(Command("test_render_en", "tren"))
async def cmd_test_render_en(message: types.Message, settings):
    if not await is_admin(message.from_user.id, settings):
        return

    try:
        renderer = BoardRenderer()
        light_colors = await db_service.get_system_setting("theme_colors_light")
        dark_colors = await db_service.get_system_setting("theme_colors_dark")
        renderer.set_custom_colors(light_colors, dark_colors)
        
        # Get chat settings for background image and opacity
        chat_settings = await db_service.get_chat_settings(message.chat.id)
        
        # English dummy words
        test_words = [
            "APPLE", "TREE", "BOOK", "SKY", "SEA",
            "COMPUTER", "PHONE", "CAR", "SUN", "GUITAR",
            "TELEVISION", "HOUSE", "WINDOW", "TABLE", "CHAIR",
            "ROAD", "SHOP", "SCHOOL", "HOSPITAL", "CITY",
            "COUNTRY", "PLANET", "SPACE", "STAR", "AIRPLANE"
        ]
        
        dummy_cards = []
        colors = [CardColor.GREEN] * 9 + [CardColor.RED] * 8 + [CardColor.BYSTANDER] * 7 + [CardColor.ASSASSIN] * 1
        import random
        random.shuffle(colors)
        
        for i in range(25):
            dummy_cards.append({
                "word": test_words[i],
                "color": colors[i].value,
                "is_revealed": random.choice([True, False]) if i < 15 else False
            })

        # Render all images
        light_img = renderer.render_board(
            dummy_cards, 
            spymaster_view=False, 
            dark_mode=False,
            background_image=chat_settings.background_image,
            background_opacity=chat_settings.background_opacity,
            card_background_opacity=chat_settings.card_background_opacity
        )

        dark_img = renderer.render_board(
            dummy_cards, 
            spymaster_view=False, 
            dark_mode=True,
            background_image=chat_settings.background_image,
            background_opacity=chat_settings.background_opacity,
            card_background_opacity=chat_settings.card_background_opacity
        )
        
        # Spymaster Views
        spy_light = renderer.render_board(
            dummy_cards, 
            spymaster_view=True, 
            dark_mode=False,
            background_image=chat_settings.background_image,
            background_opacity=chat_settings.background_opacity,
            card_background_opacity=chat_settings.card_background_opacity
        )
        
        spy_dark = renderer.render_board(
            dummy_cards, 
            spymaster_view=True, 
            dark_mode=True,
            background_image=chat_settings.background_image,
            background_opacity=chat_settings.background_opacity,
            card_background_opacity=chat_settings.card_background_opacity
        )
        
        # Group photos into a media group
        media_group = [
            types.InputMediaPhoto(
                media=BufferedInputFile(light_img.getvalue(), filename="light_en.png"),
                caption="☀️ <b>English Preview (Light)</b>"
            ),
            types.InputMediaPhoto(
                media=BufferedInputFile(dark_img.getvalue(), filename="dark_en.png"),
                caption="🌙 <b>English Preview (Dark)</b>"
            ),
            types.InputMediaPhoto(
                media=BufferedInputFile(spy_light.getvalue(), filename="spy_light_en.png"),
                caption="👨‍✈️ <b>English Spymaster (Light)</b>"
            ),
            types.InputMediaPhoto(
                media=BufferedInputFile(spy_dark.getvalue(), filename="spy_dark_en.png"),
                caption="👨‍✈️ <b>English Spymaster (Dark)</b>"
            )
        ]
        
        await message.answer_media_group(media_group)
        
    except Exception as e:
        logger.error(f"Error in test_render_en: {e}", exc_info=True)
        t = get_text()
        await message.answer(t.ADMIN_GB_ERROR.format(error=e))

class AdminColorState(StatesGroup):
    waiting_for_hex = State()

@router.message(Command("colors", "theme"))
async def cmd_admin_colors(message: types.Message, settings):
    if not await is_admin(message.from_user.id, settings):
        return
    await send_color_menu(message)

async def send_color_menu(message_or_callback, mode="light"):
    is_callback = isinstance(message_or_callback, types.CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback

    builder = InlineKeyboardBuilder()
    
    # Mode selector
    light_text = "🔘 Light" if mode == "light" else "Light"
    dark_text = "🔘 Dark" if mode == "dark" else "Dark"
    builder.row(
        types.InlineKeyboardButton(text=f"☀️ {light_text}", callback_data="admin_color_mode_light"),
        types.InlineKeyboardButton(text=f"🌙 {dark_text}", callback_data="admin_color_mode_dark")
    )
    
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
    
    chat_settings = await db_service.get_chat_settings(message.chat.id if hasattr(message, "chat") else message.message.chat.id)
    t = get_text(chat_settings.language)

    for name, key in elements:
        builder.row(types.InlineKeyboardButton(text=f"🎨 {name}", callback_data=f"admin_color_edit_{mode}_{key}"))
        
    builder.row(types.InlineKeyboardButton(text="🗑️ Reset to Defaults", callback_data=f"admin_color_reset_{mode}"))
    builder.row(types.InlineKeyboardButton(text=t.CLOSE_BTN, callback_data="admin_log_close"))

    text = t.GAME_SETTINGS_COLOR_TITLE.format(mode=mode.upper()) + "\n\n" + t.GAME_SETTINGS_COLOR_PROMPT
    
    if is_callback:
        await message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("admin_color_mode_"))
async def cb_admin_color_mode(callback: types.CallbackQuery, settings, state: FSMContext):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
    
    await state.clear()
    mode = callback.data.split("_")[-1]
    await send_color_menu(callback, mode)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_color_edit_"))
async def cb_admin_color_edit(callback: types.CallbackQuery, settings, state: FSMContext):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
        
    parts = callback.data.split("_")
    mode = parts[3]
    key = "_".join(parts[4:])
    
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    await state.set_state(AdminColorState.waiting_for_hex)
    await state.update_data(edit_mode=mode, edit_key=key, menu_msg_id=callback.message.message_id)
    
    await callback.message.edit_text(
        t.ADMIN_COLOR_EDIT_TITLE.format(key=key, mode=mode) + "\n\n" + t.ADMIN_COLOR_EDIT_PROMPT,
        reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text=t.BACK_BTN, callback_data=f"admin_color_mode_{mode}")).as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_color_reset_"))
async def cb_admin_color_reset(callback: types.CallbackQuery, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
        
    mode = callback.data.split("_")[-1]
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    t = get_text(chat_settings.language)
    db_key = f"theme_colors_{mode}"
    
    await db_service.update_system_setting(db_key, {})
    await callback.answer(t.ADMIN_COLOR_RESET_CONFIRM, show_alert=True)
    
    # Trigger preview
    await send_color_menu(callback, mode)

@router.message(AdminColorState.waiting_for_hex)
async def process_color_hex(message: types.Message, state: FSMContext, settings):
    if not await is_admin(message.from_user.id, settings):
        return await state.clear()
        
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    text = message.text.strip()
    if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", text):
        return await message.answer(t.ADMIN_COLOR_FORMAT_ERROR)
        
    data = await state.get_data()
    mode = data.get("edit_mode")
    key = data.get("edit_key")
    
    db_key = f"theme_colors_{mode}"
    colors = await db_service.get_system_setting(db_key)
    if not isinstance(colors, dict):
        colors = {}
        
    colors[key] = text
    await db_service.update_system_setting(db_key, colors)
    
    await state.clear()
    await message.answer(t.ADMIN_COLOR_UPDATE_SUCCESS.format(key=key, text=text))
    
    # Re-send menu
    await send_color_menu(message, mode)
    
    # Auto-generate test render
    await cmd_test_render(message, settings)


@router.message(Command("gb", "gb1", "gb2", "gb3", "gb4", "gb5"))
async def cmd_give_buff(message: types.Message, bot: Bot, settings):
    if not await is_admin(message.from_user.id, settings):
        return

    parts = message.text.split()
    cmd = parts[0][1:].lower() # e.g. "gb", "gb1"
    
    BUFF_MAP = {
        "1": "armor",
        "2": "intercept",
        "3": "detector",
        "4": "reveal",
        "5": "remap",
        "armor": "armor",
        "intercept": "intercept",
        "detector": "detector",
        "reveal": "reveal",
        "remap": "remap"
    }
    
    buff_type = None
    args_start = 1
    
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)

    if cmd == "gb":
        if len(parts) < 2:
            return await message.answer(t.ADMIN_GB_FORMAT_ERROR)
        buff_key = parts[1].lower()
        buff_type = BUFF_MAP.get(buff_key)
        if not buff_type:
            return await message.answer(t.ADMIN_GB_TYPE_ERROR)
        args_start = 2
    else:
        # cmd is gb1..gb5
        num = cmd[2:] # "1".."5"
        buff_type = BUFF_MAP.get(num)

    # Parse quantity and user from parts[args_start:]
    remaining = parts[args_start:]
    quantity = 1
    target_user_id = None
    target_name = "Користувач"
    
    # 1. Check reply
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.full_name
        await db_service.ensure_user(
            target_user_id,
            target_name,
            message.reply_to_message.from_user.username
        )
        if len(remaining) >= 1:
            try:
                quantity = int(remaining[0])
            except ValueError:
                pass
    else:
        # No reply. Parse remaining args
        if len(remaining) == 1:
            val = remaining[0]
            if val.isdigit():
                quantity = int(val)
                target_user_id = message.from_user.id
                target_name = message.from_user.full_name
            else:
                if val.startswith("@") or not val.isdigit():
                    user = await db_service.get_user_by_username(val)
                    if user:
                        target_user_id = user.id
                        target_name = user.full_name
                    else:
                        return await message.answer(t.ADMIN_USER_NOT_FOUND.format(user=val))
                else:
                    target_user_id = int(val)
                    await db_service.ensure_user(target_user_id)
        elif len(remaining) >= 2:
            val1 = remaining[0]
            val2 = remaining[1]
            # One should be digit, one should be user
            if val1.isdigit():
                quantity = int(val1)
                user_str = val2
            elif val2.isdigit():
                quantity = int(val2)
                user_str = val1
            else:
                user_str = val1 # fallback
                
            if user_str.startswith("@") or not user_str.isdigit():
                user = await db_service.get_user_by_username(user_str)
                if user:
                    target_user_id = user.id
                    target_name = user.full_name
                else:
                    return await message.answer(t.ADMIN_USER_NOT_FOUND.format(user=user_str))
            else:
                target_user_id = int(user_str)
                await db_service.ensure_user(target_user_id)
        else:
            # Default to admin themselves
            target_user_id = message.from_user.id
            target_name = message.from_user.full_name

    if not target_user_id:
        return await message.answer(t.ADMIN_GIVE_USER_REQUIRED)

    success = await db_service.update_user_buff(target_user_id, buff_type, quantity)
    if success:
        t = get_text(chat_settings.language)
        buff_names = {
            "armor": t.BUFF_ARMOR_NAME,
            "intercept": t.BUFF_INTERCEPT_NAME,
            "detector": t.BUFF_DETECTOR_NAME,
            "reveal": t.REVEAL_BUFF_NAME,
            "remap": t.BUFF_REMAP_NAME
        }
        bname = buff_names.get(buff_type, buff_type.upper())
        await message.answer(t.ADMIN_GB_SUCCESS.format(quantity=quantity, buff=bname, name=target_name, id=target_user_id))
        try:
            await bot.send_message(target_user_id, t.ADMIN_GB_NOTIFY.format(quantity=quantity, buff=bname))
        except:
            pass
    else:
        await message.answer(t.ADMIN_GB_ERROR)


