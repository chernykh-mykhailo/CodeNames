from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.core.database.service import db_service
from src.assets.texts import get_text
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

    text = (
        "👑 <b>Панель Адміністратора Codenames</b>\n\n"
        "Тут ви можете керувати основними налаштуваннями бота та тестувати функції.\n\n"
        "💎 <b>Видача кристалів:</b>\n"
        "Команда: <code>/give &lt;кількість&gt; [юзернейм/ID]</code> (або реплаєм на повідомлення користувача)."
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⚙️ Налаштування логів", callback_data="admin_panel_logs"))
    builder.row(types.InlineKeyboardButton(text="🎨 Налаштування теми кольорів", callback_data="admin_panel_colors"))
    builder.row(
        types.InlineKeyboardButton(text="🖼️ Тест Рендеру (UA)", callback_data="admin_panel_tr"),
        types.InlineKeyboardButton(text="🖼️ Тест Рендеру (EN)", callback_data="admin_panel_tren")
    )
    builder.row(types.InlineKeyboardButton(text="❌ Закрити", callback_data="admin_log_close"))

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
async def cb_admin_panel_tr(callback: types.CallbackQuery, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
    await cmd_test_render(callback.message, settings)
    await callback.answer()


@router.callback_query(F.data == "admin_panel_tren")
async def cb_admin_panel_tren(callback: types.CallbackQuery, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
    await cmd_test_render_en(callback.message, settings)
    await callback.answer()


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

@router.message(Command("give"))
async def cmd_give_diamonds(message: types.Message, bot: Bot, settings):
    if not await is_admin(message.from_user.id, settings):
        return

    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("❌ Формат: <code>/give &lt;кількість&gt; [юзернейм/ID]</code> (або реплаєм)")

    try:
        amount = int(parts[1])
    except ValueError:
        return await message.answer("❌ Кількість має бути числом.")

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
                return await message.answer(f"❌ Користувача {input_val} не знайдено в базі.")
        else:
            target_user_id = int(input_val)
            await db_service.ensure_user(target_user_id)

    if not target_user_id:
        return await message.answer("❌ Використайте реплай або вкажіть юзернейм/ID.")

    success = await db_service.update_user_diamonds(target_user_id, amount)
    if success:
        await message.answer(f"✅ Видано <b>{amount}</b> 💎 користувачу <b>{target_name}</b> (ID: <code>{target_user_id}</code>)")
        # Notify user if possible
        try:
            await bot.send_message(target_user_id, f"🎁 Адміністратор видав вам <b>{amount}</b> 💎!")
        except:
            pass
    else:
        await message.answer("❌ Помилка при оновленні балансу.")

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
        await message.reply("✅ Відповідь надіслано!")
    except Exception as e:
        await message.reply(f"❌ Помилка при надсиланні: {e}")

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

        # Render Light Mode
        logger.info("Rendering Light Mode...")
        light_img = renderer.render_board(dummy_cards, spymaster_view=False, dark_mode=False)
        await message.answer_photo(
            BufferedInputFile(light_img.getvalue(), filename="light_mode.png"),
            caption="☀️ <b>Light Mode Preview</b>"
        )
        
        # Render Dark Mode
        logger.info("Rendering Dark Mode...")
        dark_img = renderer.render_board(dummy_cards, spymaster_view=False, dark_mode=True)
        await message.answer_photo(
            BufferedInputFile(dark_img.getvalue(), filename="dark_mode.png"),
            caption="🌙 <b>Dark Mode Preview</b>"
        )
        
        # Spymaster View (Light)
        spy_light = renderer.render_board(dummy_cards, spymaster_view=True, dark_mode=False)
        await message.answer_photo(
            BufferedInputFile(spy_light.getvalue(), filename="spy_light.png"),
            caption="👨‍✈️ <b>Spymaster View (Light)</b>"
        )
        
        # Spymaster View (Dark)
        spy_dark = renderer.render_board(dummy_cards, spymaster_view=True, dark_mode=True)
        await message.answer_photo(
            BufferedInputFile(spy_dark.getvalue(), filename="spy_dark.png"),
            caption="👨‍✈️ <b>Spymaster View (Dark)</b>"
        )
        
        logger.info("Test render complete.")
    except Exception as e:
        logger.error(f"Error in test_render: {e}", exc_info=True)
        await message.answer(f"❌ Помилка рендерингу: <code>{e}</code>")

@router.message(Command("test_render_en", "tren"))
async def cmd_test_render_en(message: types.Message, settings):
    if not await is_admin(message.from_user.id, settings):
        return

    try:
        renderer = BoardRenderer()
        light_colors = await db_service.get_system_setting("theme_colors_light")
        dark_colors = await db_service.get_system_setting("theme_colors_dark")
        renderer.set_custom_colors(light_colors, dark_colors)
        
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

        # Render previews
        light_img = renderer.render_board(dummy_cards, spymaster_view=False, dark_mode=False)
        await message.answer_photo(
            BufferedInputFile(light_img.getvalue(), filename="light_en.png"),
            caption="☀️ <b>English Preview (Light)</b>"
        )

        dark_img = renderer.render_board(dummy_cards, spymaster_view=False, dark_mode=True)
        await message.answer_photo(
            BufferedInputFile(dark_img.getvalue(), filename="dark_en.png"),
            caption="🌙 <b>English Preview (Dark)</b>"
        )
        
        # Spymaster Views
        spy_light = renderer.render_board(dummy_cards, spymaster_view=True, dark_mode=False)
        await message.answer_photo(
            BufferedInputFile(spy_light.getvalue(), filename="spy_light_en.png"),
            caption="👨‍✈️ <b>English Spymaster (Light)</b>"
        )
        
        spy_dark = renderer.render_board(dummy_cards, spymaster_view=True, dark_mode=True)
        await message.answer_photo(
            BufferedInputFile(spy_dark.getvalue(), filename="spy_dark_en.png"),
            caption="👨‍✈️ <b>English Spymaster (Dark)</b>"
        )
        
    except Exception as e:
        logger.error(f"Error in test_render_en: {e}", exc_info=True)
        await message.answer(f"❌ Помилка: {e}")

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
    
    for name, key in elements:
        builder.row(types.InlineKeyboardButton(text=f"🎨 {name}", callback_data=f"admin_color_edit_{mode}_{key}"))
        
    builder.row(types.InlineKeyboardButton(text="🗑️ Reset to Defaults", callback_data=f"admin_color_reset_{mode}"))
    builder.row(types.InlineKeyboardButton(text="Закрити", callback_data="admin_log_close"))

    text = f"<b>🎨 Налаштування кольорів ({mode.upper()})</b>\n\nОберіть елемент для зміни кольору (формат: #RRGGBB):"
    
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
    
    await state.set_state(AdminColorState.waiting_for_hex)
    await state.update_data(edit_mode=mode, edit_key=key, menu_msg_id=callback.message.message_id)
    
    await callback.message.edit_text(
        f"🎨 <b>Зміна кольору: {key} ({mode})</b>\n\nВведіть новий колір у форматі HEX (наприклад, <code>#FF0000</code>):",
        reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_color_mode_{mode}")).as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_color_reset_"))
async def cb_admin_color_reset(callback: types.CallbackQuery, settings):
    if not await is_admin(callback.from_user.id, settings):
        return await callback.answer()
        
    mode = callback.data.split("_")[-1]
    db_key = f"theme_colors_{mode}"
    
    await db_service.update_system_setting(db_key, {})
    await callback.answer("✅ Скинуто до стандартних кольорів!", show_alert=True)
    
    # Trigger preview
    await send_color_menu(callback, mode)

@router.message(AdminColorState.waiting_for_hex)
async def process_color_hex(message: types.Message, state: FSMContext, settings):
    if not await is_admin(message.from_user.id, settings):
        return await state.clear()
        
    text = message.text.strip()
    if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", text):
        return await message.answer("❌ Некоректний формат. Спробуйте ще раз (наприклад, <code>#FF0000</code>):")
        
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
    await message.answer(f"✅ Колір <b>{key}</b> оновлено на <b>{text}</b>!")
    
    # Re-send menu
    await send_color_menu(message, mode)
    
    # Auto-generate test render
    await cmd_test_render(message, settings)
