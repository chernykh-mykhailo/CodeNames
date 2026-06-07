from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.database.service import db_service
from src.assets.texts import get_text

router = Router()

MEDALS = ["🥇", "🥈", "🥉"]


def _player_line(idx: int, name: str, username: str, value: str) -> str:
    medal = MEDALS[idx] if idx < 3 else f"<b>{idx + 1}.</b>"
    display = f"@{username}" if username else f"<b>{name}</b>"
    return f"{medal} {display} — {value}"


def _build_top_keyboard(active: str, is_group: bool = False, lang: str = "uk") -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons_row1 = []
    buttons_row2 = []

    if lang == "uk":
        labels = {
            "top_wins": "🏆 Перемоги",
            "top_classic": "🎯 Classic",
            "top_duet": "🤝 Duet",
            "top_hardcore": "💀 Hardcore",
            "top_words": "📝 Слова",
            "top_chat": "👥 Чат",
            "top_chats": "🏠 Чати",
        }
    else:
        labels = {
            "top_wins": "🏆 Wins",
            "top_classic": "🎯 Classic",
            "top_duet": "🤝 Duet",
            "top_hardcore": "💀 Hardcore",
            "top_words": "📝 Words",
            "top_chat": "👥 Chat",
            "top_chats": "🏠 Chats",
        }

    for key in ["top_wins", "top_classic", "top_duet", "top_hardcore"]:
        text = labels[key]
        if key == active:
            text = f"• {text} •"
        buttons_row1.append(types.InlineKeyboardButton(text=text, callback_data=key))

    buttons_row2.append(
        types.InlineKeyboardButton(
            text=f"• {labels['top_words']} •" if active == "top_words" else labels["top_words"],
            callback_data="top_words"
        )
    )

    if is_group:
        buttons_row2.append(
            types.InlineKeyboardButton(
                text=f"• {labels['top_chat']} •" if active == "top_chat" else labels["top_chat"],
                callback_data="top_chat"
            )
        )

    buttons_row2.append(
        types.InlineKeyboardButton(
            text=f"• {labels['top_chats']} •" if active == "top_chats" else labels["top_chats"],
            callback_data="top_chats"
        )
    )

    kb.row(*buttons_row1)
    kb.row(*buttons_row2)
    kb.row(types.InlineKeyboardButton(text="❌", callback_data="top_close"))
    return kb.as_markup()


async def _render_top_wins(lang: str, mode: str = None, chat_id: int = None) -> str:
    rows = await db_service.get_top_players(limit=15, mode=mode, chat_id=chat_id)

    if mode:
        mode_label = mode.capitalize()
    elif chat_id:
        mode_label = "Чат" if lang == "uk" else "Chat"
    else:
        mode_label = "Глобальний" if lang == "uk" else "Global"

    if lang == "uk":
        title = f"🏆 <b>ТОП — {mode_label}</b> · За перемогами\n"
    else:
        title = f"🏆 <b>TOP — {mode_label}</b> · By wins\n"

    if not rows:
        return title + "\n" + ("Ще немає даних 🤷" if lang == "uk" else "No data yet 🤷")

    lines = [title, "━━━━━━━━━━━━━━━━━━"]
    for i, row in enumerate(rows):
        wins = row.wins or 0
        total = row.total or 0
        losses = row.losses or 0
        wr = (wins / total * 100) if total > 0 else 0
        val = f"{wins}W / {losses}L · {wr:.0f}%"
        lines.append(_player_line(i, row.full_name, row.username, val))

    return "\n".join(lines)


async def _render_top_words(lang: str) -> str:
    rows = await db_service.get_top_players_by_words(limit=15)

    if lang == "uk":
        title = "📝 <b>ТОП — Вгадані слова</b>\n"
    else:
        title = "📝 <b>TOP — Guessed Words</b>\n"

    if not rows:
        return title + "\n" + ("Ще немає даних 🤷" if lang == "uk" else "No data yet 🤷")

    lines = [title, "━━━━━━━━━━━━━━━━━━"]
    for i, row in enumerate(rows):
        val = f"🎯{row.guessed_words or 0}"
        lines.append(_player_line(i, row.full_name, row.username, val))

    return "\n".join(lines)


async def _render_top_chats(lang: str) -> str:
    rows = await db_service.get_top_chats(limit=15)

    if lang == "uk":
        title = "🏠 <b>ТОП ЧАТІВ</b> · За іграми\n"
    else:
        title = "🏠 <b>TOP CHATS</b> · By games\n"

    if not rows:
        return title + "\n" + ("Ще немає даних 🤷" if lang == "uk" else "No data yet 🤷")

    lines = [title, "━━━━━━━━━━━━━━━━━━"]
    for i, row in enumerate(rows):
        medal = MEDALS[i] if i < 3 else f"<b>{i + 1}.</b>"
        chat_name = row.title or f"Chat {row.chat_id}"
        lines.append(f"{medal} <b>{chat_name}</b> · 🎮{row.total_records}")

    return "\n".join(lines)


@router.message(Command("top", "leaderboard"))
async def cmd_top(message: types.Message):
    chat_settings = await db_service.get_chat_settings(message.chat.id)
    lang = chat_settings.language
    is_group = message.chat.type != "private"

    text = await _render_top_wins(lang)
    kb = _build_top_keyboard("top_wins", is_group=is_group, lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "top_wins")
async def cb_top_wins(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    is_group = callback.message.chat.type != "private"
    text = await _render_top_wins(lang)
    kb = _build_top_keyboard("top_wins", is_group=is_group, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "top_classic")
async def cb_top_classic(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    is_group = callback.message.chat.type != "private"
    text = await _render_top_wins(lang, mode="classic")
    kb = _build_top_keyboard("top_classic", is_group=is_group, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "top_duet")
async def cb_top_duet(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    is_group = callback.message.chat.type != "private"
    text = await _render_top_wins(lang, mode="duet")
    kb = _build_top_keyboard("top_duet", is_group=is_group, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "top_hardcore")
async def cb_top_hardcore(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    is_group = callback.message.chat.type != "private"
    text = await _render_top_wins(lang, mode="hardcore")
    kb = _build_top_keyboard("top_hardcore", is_group=is_group, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "top_words")
async def cb_top_words(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    is_group = callback.message.chat.type != "private"
    text = await _render_top_words(lang)
    kb = _build_top_keyboard("top_words", is_group=is_group, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "top_chat")
async def cb_top_chat(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    chat_id = callback.message.chat.id
    is_group = callback.message.chat.type != "private"
    text = await _render_top_wins(lang, chat_id=chat_id)
    kb = _build_top_keyboard("top_chat", is_group=is_group, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "top_chats")
async def cb_top_chats(callback: types.CallbackQuery):
    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    is_group = callback.message.chat.type != "private"
    text = await _render_top_chats(lang)
    kb = _build_top_keyboard("top_chats", is_group=is_group, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "top_close")
async def cb_top_close(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
