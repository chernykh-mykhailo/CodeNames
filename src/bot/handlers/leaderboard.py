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


def _build_top_keyboard(active: str, is_group: bool = False, lang: str = "uk", hardcore_mode: str = "off") -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    t = get_text(lang)

    buttons_row1 = []
    buttons_row2 = []

    labels = {
        "top_wins": t.TOP_LABEL_WINS,
        "top_classic": t.TOP_LABEL_CLASSIC,
        "top_duet": t.TOP_LABEL_DUET,
        "top_words": t.TOP_LABEL_WORDS,
        "top_chat": t.TOP_LABEL_CHAT,
        "top_chats": t.TOP_LABEL_CHATS,
    }

    hc_suffix = "" if hardcore_mode == "off" else ("_lhc" if hardcore_mode == "light" else "_hc")

    for key in ["top_wins", "top_classic", "top_duet"]:
        text = labels[key]
        if key == active:
            text = f"• {text} •"
        buttons_row1.append(types.InlineKeyboardButton(text=text, callback_data=f"{key}{hc_suffix}"))

    words_text = f"• {labels['top_words']} •" if active == "top_words" else labels["top_words"]
    buttons_row2.append(types.InlineKeyboardButton(text=words_text, callback_data=f"top_words{hc_suffix}"))

    if is_group:
        chat_text = f"• {labels['top_chat']} •" if active == "top_chat" else labels["top_chat"]
        buttons_row2.append(types.InlineKeyboardButton(text=chat_text, callback_data=f"top_chat{hc_suffix}"))

    chats_text = f"• {labels['top_chats']} •" if active == "top_chats" else labels["top_chats"]
    buttons_row2.append(types.InlineKeyboardButton(text=chats_text, callback_data=f"top_chats{hc_suffix}"))

    # Cycle: off -> light -> hard -> off
    next_mode = {"off": "light", "light": "hard", "hard": "off"}[hardcore_mode]
    next_suffix = "" if next_mode == "off" else ("_lhc" if next_mode == "light" else "_hc")
    if hardcore_mode == "off":
        hc_text = f"💀 Hardcore: ❌" if lang != "uk" else f"💀 Хардкор: ❌"
    elif hardcore_mode == "light":
        hc_text = f"💀 Light HC: ✅" if lang != "uk" else f"💀 Лайт HC: ✅"
    else:
        hc_text = f"💀 Hardcore: ✅" if lang != "uk" else f"💀 Хардкор: ✅"

    kb.row(*buttons_row1)
    kb.row(*buttons_row2)
    kb.row(
        types.InlineKeyboardButton(text=hc_text, callback_data=f"{active}{next_suffix}"),
        types.InlineKeyboardButton(text="❌", callback_data="top_close")
    )
    return kb.as_markup()


async def _render_top_wins(lang: str, mode: str = None, chat_id: int = None, hardcore_mode: str = "off") -> str:
    rows = await db_service.get_top_players(limit=15, mode=mode, chat_id=chat_id, hardcore_mode=hardcore_mode)

    t = get_text(lang)
    if mode:
        mode_label = mode.capitalize()
    elif chat_id:
        mode_label = t.TOP_CHAT
    else:
        mode_label = t.TOP_GLOBAL

    if hardcore_mode == "hard":
        mode_label = f"{mode_label} (Hardcore)" if lang != "uk" else f"{mode_label} (Хардкор)"
    elif hardcore_mode == "light":
        mode_label = f"{mode_label} (Light HC)" if lang != "uk" else f"{mode_label} (Лайт HC)"

    title = t.TOP_TITLE_WINS.format(mode=mode_label)

    if not rows:
        return title + "\n" + t.TOP_NO_DATA

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
    t = get_text(lang)

    title = t.TOP_TITLE_WORDS

    if not rows:
        return title + "\n" + t.TOP_NO_DATA

    lines = [title, "━━━━━━━━━━━━━━━━━━"]
    for i, row in enumerate(rows):
        val = f"🎯{row.guessed_words or 0}"
        lines.append(_player_line(i, row.full_name, row.username, val))

    return "\n".join(lines)


async def _render_top_chats(lang: str) -> str:
    rows = await db_service.get_top_chats(limit=15)
    t = get_text(lang)

    title = t.TOP_TITLE_CHATS

    if not rows:
        return title + "\n" + t.TOP_NO_DATA

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

    text = await _render_top_wins(lang, hardcore_mode="off")
    kb = _build_top_keyboard("top_wins", is_group=is_group, lang=lang, hardcore_mode="off")
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("top_"))
async def cb_top_handler(callback: types.CallbackQuery):
    data = callback.data
    if data == "top_close":
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.answer()
        return

    chat_settings = await db_service.get_chat_settings(callback.message.chat.id)
    lang = chat_settings.language
    is_group = callback.message.chat.type != "private"
    chat_id = callback.message.chat.id

    hardcore_mode = "hard" if data.endswith("_hc") else ("light" if data.endswith("_lhc") else "off")
    if hardcore_mode == "hard":
        base_data = data[:-3]
    elif hardcore_mode == "light":
        base_data = data[:-4]
    else:
        base_data = data

    if base_data == "top_wins":
        text = await _render_top_wins(lang, hardcore_mode=hardcore_mode)
    elif base_data == "top_classic":
        text = await _render_top_wins(lang, mode="classic", hardcore_mode=hardcore_mode)
    elif base_data == "top_duet":
        text = await _render_top_wins(lang, mode="duet", hardcore_mode=hardcore_mode)
    elif base_data == "top_words":
        text = await _render_top_words(lang)
    elif base_data == "top_chat":
        text = await _render_top_wins(lang, chat_id=chat_id, hardcore_mode=hardcore_mode)
    elif base_data == "top_chats":
        text = await _render_top_chats(lang)
    else:
        return await callback.answer()

    kb = _build_top_keyboard(base_data, is_group=is_group, lang=lang, hardcore_mode=hardcore_mode)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()
