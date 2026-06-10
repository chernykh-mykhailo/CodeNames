from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.core.database.service import db_service
from src.assets.texts import get_text
import re

router = Router()

class DictStates(StatesGroup):
    waiting_for_words = State()

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
        words_raw = message.text.replace("\n", ",").replace(" ", ",").split(",")
    else:
        return await message.answer(t.DICT_INPUT_REQUIRED)

    words = [w.strip().upper() for w in words_raw if w.strip()]
    
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
    
    await message.answer(t.DICT_SAVE_SUCCESS.format(name=name, count=len(words)), parse_mode="HTML")

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

    is_private = message.chat.type == "private"
    is_bot_owner = bool(settings.admin_id and user_id == settings.admin_id)
    is_creator = dict_item.creator_id == user_id
    is_chat_admin = False

    if not is_private:
        try:
            member = await bot.get_chat_member(message.chat.id, user_id)
            is_chat_admin = member.status in ["administrator", "creator"]
        except Exception:
            is_chat_admin = False

    if not (is_private or is_bot_owner or is_chat_admin or is_creator):
        return await message.answer(t.DICT_PERMISSION_DENIED, parse_mode="HTML")

    await db_service.delete_custom_dictionary(message.chat.id, name)
    await state.clear()

    await message.answer(t.DICT_DELETE_SUCCESS.format(name=name), parse_mode="HTML")



