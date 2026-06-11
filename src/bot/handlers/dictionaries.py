from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.core.database.service import db_service
from src.assets.texts import get_text, b
import re

router = Router()

class DictStates(StatesGroup):
    waiting_for_words = State()
    waiting_for_add_words = State()
    waiting_for_del_words = State()

async def check_dict_permission(chat_id: int, dict_name: str, user_id: int, bot: Bot, settings) -> tuple[bool, str]:
    dicts = await db_service.get_custom_dictionaries(chat_id)
    dict_item = next((d for d in dicts if d.name == dict_name), None)
    if not dict_item:
        return False, "dict_not_found"

    is_private = False
    is_bot_owner = bool(settings.admin_ids and user_id in settings.admin_ids)
    is_creator = dict_item.creator_id == user_id
    is_chat_admin = False

    try:
        chat = await bot.get_chat(chat_id)
        if chat.type == "private":
            is_private = True
    except Exception:
        pass

    if not is_private:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            is_chat_admin = member.status in ["administrator", "creator"]
        except Exception:
            is_chat_admin = False

    if is_private or is_bot_owner or is_chat_admin or is_creator:
        return True, ""
    return False, "permission_denied"

@router.message(Command("add_dict"))
async def cmd_add_dict(message: types.Message, command: CommandObject, state: FSMContext):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    
    if not command.args:
        return await message.answer(t.DICT_NAME_REQUIRED, parse_mode="Markdown")
        
    name = command.args.strip()
    await state.update_data(dict_name=name)
    await state.set_state(DictStates.waiting_for_words)
    
    await message.answer(t.DICT_CREATE_TITLE.format(name=name), parse_mode="HTML")

@router.message(DictStates.waiting_for_words)
async def process_words(message: types.Message, state: FSMContext, bot: Bot):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)

    if message.text and message.text.startswith("/"):
        if message.text == "/cancel":
            await state.clear()
            return await message.answer(t.DICT_CANCELLED)
        return # Ignore other commands
        
    words_raw = []
    if message.document:
        if not message.document.file_name.endswith(".txt"):
            return await message.answer(t.DICT_FILE_FORMAT_ERROR)
            
        file = await bot.get_file(message.document.file_id)
        content = await bot.download_file(file.file_path)
        text = content.read().decode("utf-8")
        words_raw = text.replace("\n", ",").split(",")
    elif message.text:
        words_raw = message.text.replace("\n", ",").split(",")
    else:
        return await message.answer(t.DICT_INPUT_REQUIRED)

    # Deduplicate keeping order
    seen = set()
    words = []
    duplicates_count = 0
    for w in words_raw:
        cleaned = w.strip().upper()
        if cleaned:
            if cleaned in seen:
                duplicates_count += 1
            else:
                seen.add(cleaned)
                words.append(cleaned)
    
    if len(words) < 16:
        return await message.answer(t.DICT_TOO_FEW_WORDS.format(count=len(words)))
        
    data = await state.get_data()
    name = data.get("dict_name")
    
    await db_service.add_custom_dictionary(
        message.chat.id,
        name,
        words,
        creator_id=message.from_user.id if message.from_user else None,
    )
    await state.clear()
    
    success_msg = t.DICT_SAVE_SUCCESS.format(name=name, count=len(words))
    if duplicates_count > 0:
        success_msg += f"\n\n⚠️ <b>Видалено дублікатів: {duplicates_count}</b>" if chat_settings.language == "uk" else f"\n\n⚠️ <b>Removed duplicates: {duplicates_count}</b>"
    
    await message.answer(success_msg, parse_mode="HTML")

@router.message(Command("my_dicts"))
async def cmd_my_dicts(message: types.Message):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    dicts = await db_service.get_custom_dictionaries(message.chat.id)
    if not dicts:
        return await message.answer(t.DICT_EMPTY_LIST, parse_mode="Markdown")
        
    text = t.DICT_MY_LIST_TITLE
    for d in dicts:
        text += f"• <b>{d.name}</b> ({len(d.words)} слів)\n"
        
    await message.answer(text, parse_mode="HTML")

@router.message(Command("del_dict"))
async def cmd_del_dict(message: types.Message, command: CommandObject, state: FSMContext, bot: Bot, settings):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)

    if not command.args:
        return await message.answer(t.DICT_NAME_REQUIRED, parse_mode="Markdown")

    name = command.args.strip()
    dicts = await db_service.get_custom_dictionaries(message.chat.id)
    dict_item = next((d for d in dicts if d.name == name), None)

    if not dict_item:
        return await message.answer(t.DICT_NOT_FOUND.format(name=name), parse_mode="Markdown")

    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return await message.answer(t.DICT_PERMISSION_DENIED, parse_mode="HTML")

    allowed, err = await check_dict_permission(message.chat.id, name, user_id, bot, settings)
    if not allowed:
        return await message.answer(t.DICT_PERMISSION_DENIED, parse_mode="HTML")

    await db_service.delete_custom_dictionary(message.chat.id, name)
    await state.clear()

    await message.answer(t.DICT_DELETE_SUCCESS.format(name=name), parse_mode="HTML")

@router.message(Command("add_words"))
async def cmd_add_words(message: types.Message, command: CommandObject, state: FSMContext, bot: Bot, settings):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    
    if not command.args:
        return await message.answer(t.DICT_NAME_REQUIRED, parse_mode="Markdown")
        
    name = command.args.strip()
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return await message.answer(t.DICT_PERMISSION_DENIED, parse_mode="HTML")
        
    allowed, err = await check_dict_permission(message.chat.id, name, user_id, bot, settings)
    if not allowed:
        if err == "dict_not_found":
            return await message.answer(t.DICT_NOT_FOUND.format(name=name), parse_mode="Markdown")
        else:
            return await message.answer(t.DICT_PERMISSION_DENIED, parse_mode="HTML")
            
    await state.update_data(dict_name=name)
    await state.set_state(DictStates.waiting_for_add_words)
    
    prompt = (
        f"➕ <b>Додавання слів до словника '{name}'</b>\n\n"
        "Будь ласка, надішліть список слів через кому, кожне з нового рядка або надішліть .txt файл.\n"
        "Напишіть /cancel для скасування."
        if chat_settings.language == "uk"
        else f"➕ <b>Adding words to dictionary '{name}'</b>\n\n"
        "Please send a list of words separated by commas, each on a new line, or send a .txt file.\n"
        "Type /cancel to cancel."
    )
    await message.answer(prompt, parse_mode="HTML")

@router.message(DictStates.waiting_for_add_words)
async def process_add_words(message: types.Message, state: FSMContext, bot: Bot):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)

    if message.text and message.text.startswith("/"):
        if message.text == "/cancel":
            await state.clear()
            return await message.answer(t.DICT_CANCELLED)
        return
        
    words_raw = []
    if message.document:
        if not message.document.file_name.endswith(".txt"):
            return await message.answer(t.DICT_FILE_FORMAT_ERROR)
            
        file = await bot.get_file(message.document.file_id)
        content = await bot.download_file(file.file_path)
        text = content.read().decode("utf-8")
        words_raw = text.replace("\n", ",").split(",")
    elif message.text:
        words_raw = message.text.replace("\n", ",").split(",")
    else:
        return await message.answer(t.DICT_INPUT_REQUIRED)

    data = await state.get_data()
    name = data.get("dict_name")
    
    dicts = await db_service.get_custom_dictionaries(message.chat.id)
    dict_item = next((d for d in dicts if d.name == name), None)
    if not dict_item:
        await state.clear()
        return await message.answer(t.DICT_NOT_FOUND.format(name=name))
        
    existing_words = dict_item.words or []
    existing_set = set(existing_words)
    
    seen = set()
    added_words = []
    duplicates_count = 0
    
    for w in words_raw:
        cleaned = w.strip().upper()
        if cleaned:
            if cleaned in existing_set or cleaned in seen:
                duplicates_count += 1
            else:
                seen.add(cleaned)
                added_words.append(cleaned)
                
    if not added_words:
        await state.clear()
        msg = (
            f"ℹ️ Жодного нового слова не додано. Усі надіслані слова вже є в словнику або дублюються."
            if chat_settings.language == "uk"
            else f"ℹ️ No new words added. All sent words are already in the dictionary or duplicated."
        )
        return await message.answer(msg)
        
    updated_words = existing_words + added_words
    await db_service.add_custom_dictionary(
        message.chat.id,
        name,
        updated_words,
        creator_id=dict_item.creator_id,
    )
    await state.clear()
    
    success_msg = (
        f"✅ У словник <b>'{name}'</b> успішно додано {len(added_words)} нових слів! (Загалом: {len(updated_words)} слів)"
        if chat_settings.language == "uk"
        else f"✅ Successfully added {len(added_words)} new words to dictionary <b>'{name}'</b>! (Total: {len(updated_words)} words)"
    )
    if duplicates_count > 0:
        success_msg += f"\n\n⚠️ <b>Видалено дублікатів: {duplicates_count}</b>" if chat_settings.language == "uk" else f"\n\n⚠️ <b>Removed duplicates: {duplicates_count}</b>"
        
    await message.answer(success_msg, parse_mode="HTML")

@router.message(Command("del_words"))
async def cmd_del_words(message: types.Message, command: CommandObject, state: FSMContext, bot: Bot, settings):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    
    if not command.args:
        return await message.answer(t.DICT_NAME_REQUIRED, parse_mode="Markdown")
        
    name = command.args.strip()
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return await message.answer(t.DICT_PERMISSION_DENIED, parse_mode="HTML")
        
    allowed, err = await check_dict_permission(message.chat.id, name, user_id, bot, settings)
    if not allowed:
        if err == "dict_not_found":
            return await message.answer(t.DICT_NOT_FOUND.format(name=name), parse_mode="Markdown")
        else:
            return await message.answer(t.DICT_PERMISSION_DENIED, parse_mode="HTML")
            
    await state.update_data(dict_name=name)
    await state.set_state(DictStates.waiting_for_del_words)
    
    prompt = (
        f"➖ <b>Вилучення слів зі словника '{name}'</b>\n\n"
        "Будь ласка, надішліть список слів, які ви хочете видалити, через кому або кожне з нового рядка, або надішліть .txt файл.\n"
        "Напишіть /cancel для скасування."
        if chat_settings.language == "uk"
        else f"➖ <b>Removing words from dictionary '{name}'</b>\n\n"
        "Please send a list of words you want to delete separated by commas, each on a new line, or send a .txt file.\n"
        "Type /cancel to cancel."
    )
    await message.answer(prompt, parse_mode="HTML")

@router.message(DictStates.waiting_for_del_words)
async def process_del_words(message: types.Message, state: FSMContext, bot: Bot):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)

    if message.text and message.text.startswith("/"):
        if message.text == "/cancel":
            await state.clear()
            return await message.answer(t.DICT_CANCELLED)
        return
        
    words_raw = []
    if message.document:
        if not message.document.file_name.endswith(".txt"):
            return await message.answer(t.DICT_FILE_FORMAT_ERROR)
            
        file = await bot.get_file(message.document.file_id)
        content = await bot.download_file(file.file_path)
        text = content.read().decode("utf-8")
        words_raw = text.replace("\n", ",").split(",")
    elif message.text:
        words_raw = message.text.replace("\n", ",").split(",")
    else:
        return await message.answer(t.DICT_INPUT_REQUIRED)

    data = await state.get_data()
    name = data.get("dict_name")
    
    dicts = await db_service.get_custom_dictionaries(message.chat.id)
    dict_item = next((d for d in dicts if d.name == name), None)
    if not dict_item:
        await state.clear()
        return await message.answer(t.DICT_NOT_FOUND.format(name=name))
        
    existing_words = dict_item.words or []
    
    words_to_delete = {w.strip().upper() for w in words_raw if w.strip()}
    
    updated_words = [w for w in existing_words if w not in words_to_delete]
    removed_count = len(existing_words) - len(updated_words)
    
    if removed_count == 0:
        await state.clear()
        msg = (
            f"ℹ️ Жодного слова не було видалено. Вказаних слів немає в словнику."
            if chat_settings.language == "uk"
            else f"ℹ️ No words were deleted. None of the specified words exist in the dictionary."
        )
        return await message.answer(msg)
        
    await db_service.add_custom_dictionary(
        message.chat.id,
        name,
        updated_words,
        creator_id=dict_item.creator_id,
    )
    await state.clear()
    
    success_msg = (
        f"✅ Видалено {removed_count} слів зі словника <b>'{name}'</b>. (Загалом залишилось: {len(updated_words)} слів)"
        if chat_settings.language == "uk"
        else f"✅ Removed {removed_count} words from dictionary <b>'{name}'</b>. (Total remaining: {len(updated_words)} words)"
    )
    await message.answer(success_msg, parse_mode="HTML")


@router.message(Command("view_dict"))
async def cmd_view_dict(message: types.Message, command: CommandObject):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    t = get_text(chat_settings.language)
    
    if not command.args:
        return await message.answer(t.DICT_NAME_REQUIRED, parse_mode="Markdown")
        
    name = command.args.strip()
    dicts = await db_service.get_custom_dictionaries(message.chat.id)
    dict_item = next((d for d in dicts if d.name == name), None)
    
    if not dict_item:
        return await message.answer(t.DICT_NOT_FOUND.format(name=name), parse_mode="Markdown")
        
    words = dict_item.words or []
    words_str = ", ".join(words)
    
    header = (
        f"📖 <b>Словник: '{name}'</b> ({len(words)} слів):\n\n"
        if chat_settings.language == "uk"
        else f"📖 <b>Dictionary: '{name}'</b> ({len(words)} words):\n\n"
    )
    
    if len(header) + len(words_str) > 4000:
        import io
        file_content = "\n".join(words)
        file_io = io.BytesIO(file_content.encode("utf-8"))
        file_io.name = f"{name}.txt"
        
        await message.answer_document(
            document=types.BufferedInputFile(file_io.read(), filename=f"{name}.txt"),
            caption=header,
            parse_mode="HTML"
        )
    else:
        await message.answer(f"{header}<code>{words_str}</code>", parse_mode="HTML")
