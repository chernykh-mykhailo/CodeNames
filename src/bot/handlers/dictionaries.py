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
    t = get_text() # Default to UA for now or get from chat
    
    if not command.args:
        return await message.answer("❌ Будь ласка, вкажіть назву словника: `/add_dict назва`", parse_mode="Markdown")
        
    name = command.args.strip()
    await state.update_data(dict_name=name)
    await state.set_state(DictStates.waiting_for_words)
    
    await message.answer(
        f"📝 <b>Створення словника '{name}'</b>\n\n"
        "Будь ласка, надішліть список слів через кому, кожне з нового рядка <b>або надішліть .txt файл</b>.\n"
        "Мінімальна кількість слів для гри: 16 (рекомендовано 50+).\n\n"
        "Напишіть /cancel для скасування."
    , parse_mode="HTML")

@router.message(DictStates.waiting_for_words)
async def process_words(message: types.Message, state: FSMContext, bot: Bot):
    if message.text and message.text.startswith("/"):
        if message.text == "/cancel":
            await state.clear()
            return await message.answer("❌ Скасовано.")
        return # Ignore other commands
        
    words_raw = []
    if message.document:
        if not message.document.file_name.endswith(".txt"):
            return await message.answer("❌ Будь ласка, надішліть файл у форматі .txt")
            
        file = await bot.get_file(message.document.file_id)
        content = await bot.download_file(file.file_path)
        text = content.read().decode("utf-8")
        words_raw = text.replace("\n", ",").split(",")
    elif message.text:
        words_raw = message.text.replace("\n", ",").split(",")
    else:
        return await message.answer("❌ Будь ласка, надішліть текст або .txt файл.")

    words = [w.strip().upper() for w in words_raw if w.strip()]
    
    if len(words) < 16:
        return await message.answer(f"❌ Занадто мало слів ({len(words)}). Потрібно хоча б 16 для маленької карти (4х4). Надішліть ще.")
        
    data = await state.get_data()
    name = data.get("dict_name")
    
    await db_service.add_custom_dictionary(message.chat.id, name, words)
    await state.clear()
    
    await message.answer(f"✅ Словник <b>'{name}'</b> збережено! ({len(words)} слів)\nТепер ви можете обрати його в налаштуваннях гри.", parse_mode="HTML")

@router.message(Command("my_dicts"))
async def cmd_my_dicts(message: types.Message):
    dicts = await db_service.get_custom_dictionaries(message.chat.id)
    if not dicts:
        return await message.answer("📭 У цьому чаті ще немає власних словників. Створіть перший: `/add_dict назва`", parse_mode="Markdown")
        
    text = "📚 <b>Власні словники чату:</b>\n\n"
    for d in dicts:
        text += f"• <b>{d.name}</b> ({len(d.words)} слів)\n"
        
    await message.answer(text, parse_mode="HTML")
