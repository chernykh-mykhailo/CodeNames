from dataclasses import dataclass
from typing import Dict

@dataclass
class CodenamesTexts:
    # Main menu & registration
    WELCOME: str
    CMD_CODENAMES: str
    CMD_STATS: str
    CMD_SETTINGS: str
    REGISTRATION_TITLE: str
    JOIN_BTN: str
    START_BTN: str
    SETTINGS_BTN: str
    ALREADY_JOINED: str
    JOIN_SUCCESS: str
    BACK_TO_GAME: str
    MIN_PLAYERS: str
    REG_TIMEOUT: str
    PLAYERS_LIST: str
    
    # Game UI
    TURN_RED: str
    TURN_BLUE: str
    TURN_DUET: str
    CLUE_HINT: str
    SPYMASTER_WAIT: str
    OPERATIVES_TURN: str
    TIME_UP: str
    PASS_BTN: str
    BUFF_BTN: str
    WIN_RED: str
    WIN_BLUE: str
    WIN_DUET: str
    LOSE_DUET: str
    GAME_OVER: str
    DUET_HEADER: str
    CLASSIC_HEADER: str
    TEAM_RED_GEN: str
    TEAM_BLUE_GEN: str
    
    # Spymaster specific
    SPYMASTER_ROLE: str
    SPYMASTER_DUAL_ROLE: str
    SPYMASTER_INSTRUCTIONS: str
    SPYMASTER_DM_ERROR: str
    GIVE_HINT_BTN: str
    CHOOSE_WORD_BTN: str
    
    # Results & Buffs cleanup
    GAME_ENDED_TITLE: str
    NEW_CLUE: str
    REVEAL_BUFF_NAME: str
    SELECT_BUFF_TITLE: str
    REVEAL_BUFF_RESULT: str
    BUFF_USED_ERROR: str
    NO_REVEAL_WORDS: str
    SPYMASTER_GUESS_ERROR: str
    SPYMASTER_BUFF_ONLY: str
    START_GAME_FIRST: str
    REG_START_DESC: str
    
    # Inline Query results
    INLINE_VALID_HINT_TITLE: str
    INLINE_VALID_HINT_DESC: str
    INLINE_INVALID_HINT_TITLE: str
    INLINE_INVALID_HINT_DESC: str
    EXAMPLE_WORD: str
    
    # Settings menu
    SETTINGS_TITLE: str
    SET_MODE: str
    SET_LANG: str
    SET_WORDS: str
    SET_TIMER_REG: str
    SET_TIMER_TURN: str
    SET_LANG_TITLE: str
    SET_WORDS_TITLE: str
    SET_TMR_REG_TITLE: str
    SET_TMR_TURN_TITLE: str
    SET_MODE_TITLE: str
    MODE_CLASSIC_BTN: str
    MODE_DUET_BTN: str
    LANG_UK_BTN: str
    LANG_EN_BTN: str
    WORD_SET_FORMAT: str
    
    # Mode Descriptions (NEW)
    MODE_DUET_DESC: str
    MODE_3P_DESC: str
    MODE_CLASSIC_DESC: str
    GAME_STARTED_MSG: str
    
    # Values
    TIME_1M: str
    TIME_2M: str
    TIME_3M: str
    TIME_5M: str
    TIME_10M: str
    BACK_BTN: str
    RETURN_BTN: str
    
    # Other
    GAME_NOT_FOUND: str
    NO_STATS: str
    STATS_TEMPLATE: str

TEXTS: Dict[str, CodenamesTexts] = {
    "uk": CodenamesTexts(
        WELCOME="🕵️‍♂️ Вітаємо у <b>Codenames Master</b>!\n\nНайкращий бот для гри у 'Кодові Імена' прямо в Telegram.\n\n🎮 Щоб почати: /codenames\n📊 Твоя статистика: /stats\n⚙️ Налаштування: /settings",
        CMD_CODENAMES="codenames",
        CMD_STATS="stats",
        CMD_SETTINGS="settings",
        REGISTRATION_TITLE="📝 <b>Реєстрація на гру Кодові Імена</b>\nГравців: {count}",
        JOIN_BTN="🙋‍♂️ Приєднатися",
        START_BTN="🚀 Розпочати",
        SETTINGS_BTN="⚙️ Налаштування",
        ALREADY_JOINED="ℹ️ Ви вже зареєстровані у цій грі.",
        JOIN_SUCCESS="✅ Ви приєдналися до гри у чаті!",
        BACK_TO_GAME="⬅️ Повернутися до гри",
        MIN_PLAYERS="❌ Необхідно мінімум 2 гравці!",
        REG_TIMEOUT="🕒 <b>Час на реєстрацію вичерпано.</b> Гру скасовано.",
        PLAYERS_LIST="Поточний склад:",
        
        TURN_RED="🔴 Хід ЧЕРВОНИХ",
        TURN_BLUE="🔵 Хід СИНІХ",
        TURN_DUET="👥 Режим: Дует",
        CLUE_HINT="💡 Підказка: <b>{clue}</b> ({count})",
        SPYMASTER_WAIT="👨‍✈️ Капітан дає підказку...",
        OPERATIVES_TURN="🤔 Оперативники, ваш вибір!",
        TIME_UP="⏰ <b>Час вичерпано!</b> Хід автоматично передано.",
        PASS_BTN="⏭ Пас",
        BUFF_BTN="⚡ Баф: Розвідка",
        WIN_RED="🎉 <b>ПЕРЕМОГА ЧЕРВОНИХ!</b>",
        WIN_BLUE="🎉 <b>ПЕРЕМОГА СИНІХ!</b>",
        WIN_DUET="🎉 <b>ПЕРЕМОГА!</b> Ви знайшли всіх агентів!",
        LOSE_DUET="💀 <b>ПОРАЗКА!</b> Ви натрапили на вбивцю.",
        GAME_OVER="🏁 <b>Гра завершена!</b>",
        DUET_HEADER="👥 <b>Режим: Дует</b>",
        CLASSIC_HEADER="🔍 <b>Черга {team}</b>",
        TEAM_RED_GEN="🔴 ЧЕРВОНИХ",
        TEAM_BLUE_GEN="🔵 СИНІХ",
        
        SPYMASTER_ROLE="🕵️‍♂️ Ви — зв'язківець команди <b>{team}</b>.",
        SPYMASTER_DUAL_ROLE="🕵️‍♂️ Ви — <b>єдиний зв'язківець</b> для обох команд!",
        SPYMASTER_INSTRUCTIONS=(
            "🗺 <b>Ваша секретна карта</b> вище.\n"
            "💡 Пишіть підказку <b>прямо в груповий чат</b> у форматі: <code>слово кількість</code>"
        ),
        SPYMASTER_DM_ERROR=(
            "⚠️ Не вдалося надіслати карту зв'язківцю {mention}.\n"
            "Перевірте, чи він запустив бота в приватних повідомленнях!"
        ),
        GIVE_HINT_BTN="💡 Дати підказку",
        CHOOSE_WORD_BTN="🔍 Обрати слово",

        GAME_ENDED_TITLE="🎉 ГРУ ЗАКІНЧЕНО! Перемогли <b>{winner}</b>",
        NEW_CLUE="🔎 Нова підказка: <b>{clue}</b> ({count})",
        REVEAL_BUFF_NAME="🕵️‍♂️ Розвідка (Відкрити 1 слово)",
        SELECT_BUFF_TITLE="⚡ <b>Оберіть баф:</b>",
        REVEAL_BUFF_RESULT="🔍 Розвідка відкрила слово: {word}",
        BUFF_USED_ERROR="❌ Цей баф вже використано вашою командою!",
        NO_REVEAL_WORDS="❌ Немає слів для розвідки.",
        SPYMASTER_GUESS_ERROR="🧙‍♂️ Капітанам не можна відгадувати слова!",
        SPYMASTER_BUFF_ONLY="🔒 Тільки капітани можуть використовувати бафи!",
        START_GAME_FIRST="ℹ️ Запустіть гру спочатку: /codenames",
        REG_START_DESC="⚙️ <b>Налаштування Codenames Master</b>",
        
        INLINE_VALID_HINT_TITLE="✅ Підказка: {word} ({count})",
        INLINE_VALID_HINT_DESC="Натисніть сюди, щоб відправити",
        INLINE_INVALID_HINT_TITLE="⚠️ Введіть слово та число",
        INLINE_INVALID_HINT_DESC="Наприклад: {input} 2",
        EXAMPLE_WORD="Дерево",
        
        SETTINGS_TITLE="⚙️ <b>Налаштування Codenames Master</b>",
        SET_MODE="🎮 Режим: {mode}",
        SET_LANG="🌐 Мова: {lang}",
        SET_WORDS="📚 Словник: {words}",
        SET_TIMER_REG="🕒 Реєстрація: {time}м",
        SET_TIMER_TURN="⏳ Хід: {time}м",
        SET_LANG_TITLE="🌐 <b>Оберіть мову гри:</b>",
        SET_WORDS_TITLE="📚 <b>Оберіть словник:</b>",
        SET_TMR_REG_TITLE="🕒 <b>Час на реєстрацію:</b>",
        SET_TMR_TURN_TITLE="⏳ <b>Час на один хід:</b>",
        SET_MODE_TITLE="🎮 <b>Оберіть режим гри:</b>",
        MODE_CLASSIC_BTN="⚔️ Classic (Командна)",
        MODE_DUET_BTN="🤝 Duet (Co-op)",
        LANG_UK_BTN="Українська 🇺🇦",
        LANG_EN_BTN="English 🇺🇸",
        WORD_SET_FORMAT="📖 {name}",
        
        MODE_DUET_DESC="👥 <b>Дует</b>: Кооперативний режим!",
        MODE_3P_DESC="👥 <b>Режим для 3 гравців</b>: Один зв'язківець на дві команди!",
        MODE_CLASSIC_DESC="👥 Класичний командний режим.",
        GAME_STARTED_MSG="🏁 Гру розпочато! {desc}\nЗв'язківцям надіслано карти.",
        
        TIME_1M="1 хвилина",
        TIME_2M="2 хвилини",
        TIME_3M="3 хвилини",
        TIME_5M="5 хвилин",
        TIME_10M="10 хвилин",
        BACK_BTN="⬅️ Назад",
        RETURN_BTN="⬅️ Повернутися до гри",
        
        GAME_NOT_FOUND="❌ Гра вже закінчилася або не знайдена.",
        NO_STATS="📊 У вас ще немає зіграних ігор. Час це виправити! /codenames",
        STATS_TEMPLATE=(
            "📊 <b>Твоя статистика (Codenames)</b>\n\n"
            "🎮 Всього ігор: <b>{total}</b>\n"
            "✅ Перемог: <b>{wins}</b>\n"
            "❌ Поразок: <b>{losses}</b>\n\n"
            "🏆 Вінрейт: <b>{winrate:.1f}%</b>"
        )
    )
}

def get_text(lang: str = "uk") -> CodenamesTexts:
    return TEXTS.get(lang, TEXTS["uk"])
