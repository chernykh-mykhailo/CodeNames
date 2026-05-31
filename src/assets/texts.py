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
    SET_BOARD_SIZE: str
    CLOSE_BTN: str
    START_BTN: str
    CANCEL_BTN: str
    SETTINGS_BTN: str
    ALREADY_JOINED: str
    JOIN_SUCCESS: str
    BACK_TO_GAME: str
    MIN_PLAYERS: str
    REG_TIMEOUT: str
    PLAYERS_LIST: str
    JOINED_MID_GAME: str
    GAME_ALREADY_STARTED: str
    TEAM_SIMPLE: str
    TEAM_GREEN: str
    TEAM_RED: str

    # Game UI
    TURN_GREEN: str
    TURN_RED: str
    TURN_DUET: str
    CLUE_HINT: str
    SPYMASTER_WAIT: str
    OPERATIVES_TURN: str
    TIME_UP: str
    PASS_BTN: str
    BUFF_BTN: str
    WIN_GREEN: str
    WIN_RED: str
    WIN_DUET: str
    LOSE_DUET: str
    GAME_OVER: str
    DUET_HEADER: str
    CLASSIC_HEADER: str
    TEAM_GREEN_GEN: str
    TEAM_RED_GEN: str
    DUET_TURN_MSG: str

    # Spymaster specific
    SPYMASTER_ROLE: str
    SPYMASTER_DUAL_ROLE: str
    SPYMASTER_INSTRUCTIONS: str
    SPYMASTER_DM_ERROR: str
    GIVE_HINT_BTN: str
    CHOOSE_WORD_BTN: str

    # Results & Buffs cleanup
    GAME_ENDED_TITLE: str
    GAME_STATS: str
    NEW_CLUE: str
    REVEAL_BUFF_NAME: str
    SELECT_BUFF_TITLE: str
    REVEAL_BUFF_RESULT: str
    BUFF_USED_ERROR: str
    NO_REVEAL_WORDS: str
    SPYMASTER_GUESS_ERROR: str
    SPYMASTER_BUFF_ONLY: str
    START_GAME_FIRST: str
    NO_GAME_IN_CHAT: str
    START_GAME_BTN: str
    REG_START_DESC: str

    # Inline Query results
    INLINE_VALID_HINT_TITLE: str
    INLINE_VALID_HINT_DESC: str
    INLINE_HINT_TITLE: str
    INLINE_HINT_DESC: str
    SECONDS: str
    TURN_NOTIFICATION: str
    INLINE_INVALID_HINT_TITLE: str
    INLINE_INVALID_HINT_DESC: str
    EXAMPLE_WORD: str
    NOT_YOUR_TURN: str
    NOT_YOUR_TURN_DESC: str
    NOT_A_PLAYER: str
    NOT_A_PLAYER_DESC: str

    # Chat settings
    CHAT_SETTINGS_TITLE: str
    SETTING_ALLOW_EVERYONE_START: str
    ADMIN_ONLY_ERROR: str
    SETTING_BUTTON_BOARD: str

    # Game control
    GAME_STOPPED: str
    GAME_STOPPED_CONFIRM: str
    PLAYER_LEFT: str
    ONLY_ADMIN_STOP: str

    # Settings menu
    SETTINGS_TITLE: str
    SET_MODE: str
    SET_LANG: str
    SET_WORDS: str
    SET_TIMER_REG: str
    SETTING_DARK_MODE: str
    SETTING_BUFFS: str

    # Diamond Shop
    SHOP_DIAMONDS_TITLE: str
    SHOP_DIAMONDS_DESC: str
    BUY_VIA_MONO: str
    BUY_VIA_STARS: str
    PAYMENT_SUCCESS: str
    PAYMENT_CHECK_BTN: str
    PAYMENT_PENDING: str
    PAYMENT_EXPIRED: str
    PAYMENT_ERROR: str
    ITEM_1000_NAME: str
    ITEM_5000_NAME: str
    ITEM_10000_NAME: str
    INVOICE_TITLE: str
    INVOICE_DESC: str
    MONO_MANUAL_INSTRUCTIONS: str
    MONO_MANUAL_CODE: str
    OPEN_JAR_BTN: str
    COPY_CODE_BTN: str
    MANUAL_PAYMENT_NOTICE: str
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

    # Mode Descriptions
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

    # Admin tools
    ADMIN_LOG_TITLE: str
    ADMIN_LOG_DEST: str
    ADMIN_LOG_TYPES: str
    ADMIN_CHOOSE_ACTION: str
    ADMIN_LOG_HERE_BTN: str
    ADMIN_LOG_ERRORS_BTN: str
    ADMIN_LOG_FEEDBACK_BTN: str
    ADMIN_CLOSE_BTN: str
    ADMIN_NO_RIGHTS: str
    ADMIN_LOG_SET_SUCCESS: str
    ADMIN_UPDATED: str
    BUFFS_ENABLED_MSG: str

    # Feedback
    FEEDBACK_PROMPT: str
    FEEDBACK_SENT: str
    FEEDBACK_REPLY_TEMPLATE: str
    FEEDBACK_HEADER: str
    FINISH_FEEDBACK_BTN: str
    FEEDBACK_SESSION_STARTED: str
    FEEDBACK_TOO_FAST: str
    FEEDBACK_LIMIT_REACHED: str

    # Other
    GAME_NOT_FOUND: str
    NO_STATS: str
    STATS_TEMPLATE: str

    # Shop & Buffs
    SHOP_TITLE: str
    SHOP_BALANCE: str
    SHOP_BTN: str
    SHOP_ITEM_DESC: str
    BUY_SUCCESS: str
    BUY_FAIL: str
    BUFF_NOT_AVAILABLE: str
    BUFF_ARMOR_NAME: str
    BUFF_DETECTOR_NAME: str
    BUFF_INTERCEPT_NAME: str
    BUFF_REMAP_NAME: str
    BUFF_ARMOR_DESC: str
    BUFF_DETECTOR_DESC: str
    BUFF_INTERCEPT_DESC: str
    BUFF_REMAP_DESC: str
    BUFF_TARGETED_REMAP_NAME: str
    BUFF_TARGETED_REMAP_DESC: str
    SELECT_TARGETED_REMAP: str
    ALREADY_REVEALED: str
    SPYMASTER_REMAP_ONLY: str
    BUFF_ARMOR_PRICE: int = 350
    BUFF_DETECTOR_PRICE: int = 150
    BUFF_INTERCEPT_PRICE: int = 250
    BUFF_REMAP_PRICE: int = 100
    BUFF_TARGETED_REMAP_PRICE: int = 200


TEXTS: Dict[str, CodenamesTexts] = {
    "uk": CodenamesTexts(
        WELCOME="🕵️‍♂️ Вітаємо у <b>Codenames Master</b>!\n\nНайкращий бот для гри у 'Кодові Імена' прямо в Telegram.\n\n🎮 Щоб почати: /codenames\n📊 Твоя статистика: /stats\n⚙️ Налаштування: /settings",
        CMD_CODENAMES="codenames",
        CMD_STATS="stats",
        CMD_SETTINGS="settings",
        REGISTRATION_TITLE="📝 <b>Реєстрація на гру Кодові Імена</b>\nГравців: {count}",
        JOIN_BTN="🙋‍♂️ Приєднатися",
        SET_BOARD_SIZE="📐 Розмір карти: {size}x{size}",
        CLOSE_BTN="Закрити",
        START_BTN="🚀 Розпочати",
        CANCEL_BTN="🛑 Відмінити",
        SETTINGS_BTN="⚙️ Налаштування",
        ALREADY_JOINED="ℹ️ Ви вже зареєстровані у цій грі.",
        JOIN_SUCCESS="✅ Ви приєдналися до гри у чаті!",
        BACK_TO_GAME="⬅️ Повернутися до гри",
        MIN_PLAYERS="❌ Необхідно мінімум 2 гравці!",
        REG_TIMEOUT="🕒 <b>Час на реєстрацію вичерпано.</b> Гру скасовано.",
        PLAYERS_LIST="Поточний склад:",
        JOINED_MID_GAME="приєднався до гри!",
        GAME_ALREADY_STARTED="❌ <b>Гра вже триває або лоббі вже створене!</b>\nВи не можете запустити кілька ігор одночасно в одному чаті.",
        TEAM_SIMPLE="Команда",
        TEAM_GREEN="Зелені",
        TEAM_RED="Червоні",

        TURN_GREEN="🟢 Хід ЗЕЛЕНИХ",
        TURN_RED="🔴 Хід ЧЕРВОНИХ",
        TURN_DUET="👥 Режим: Дует",
        CLUE_HINT="💡 Підказка: <b>{clue}</b> ({count})",
        SPYMASTER_WAIT="👨‍✈️ Капітан дає підказку...",
        OPERATIVES_TURN="🤔 Оперативники, ваш вибір!",
        TIME_UP="⏰ <b>Час вичерпано!</b> Хід автоматично передано.",
        PASS_BTN="⏭ Пас",
        BUFF_BTN="⚡ Баф: Розвідка",
        WIN_GREEN="🎉 <b>ПЕРЕМОГА ЗЕЛЕНИХ!</b>",
        WIN_RED="🎉 <b>ПЕРЕМОГА ЧЕРВОНИХ!</b>",
        WIN_DUET="🎉 <b>ПЕРЕМОГА!</b> Ви знайшли всіх агентів!",
        LOSE_DUET="💀 <b>ПОРАЗКА!</b> Ви натрапили на вбивцю.",
        GAME_OVER="🏁 <b>Гра завершена!</b>",
        DUET_HEADER="👥 <b>Режим: Дует</b>",
        CLASSIC_HEADER="🔍 <b>Черга {team}</b>",
        TEAM_GREEN_GEN="🟢 ЗЕЛЕНИХ",
        TEAM_RED_GEN="🔴 ЧЕРВОНИХ",
        DUET_TURN_MSG="🔍 Підказку дає: <b>{name}</b>",

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
        GAME_STATS="⏱ Час гри: <b>{duration}</b>\n🔎 Відгадано слів: <b>{found}/{total}</b>",
        NEW_CLUE="🔎 Нова підказка: <b>{clue}</b> ({count})",
        REVEAL_BUFF_NAME="🕵️‍♂️ Розвідка (Відкрити 1 слово)",
        SELECT_BUFF_TITLE="⚡ <b>Оберіть баф:</b>",
        REVEAL_BUFF_RESULT="🔍 Розвідка відкрила слово: {word}",
        BUFF_USED_ERROR="❌ Цей баф вже використано вашою командою!",
        NO_REVEAL_WORDS="❌ Немає слів для розвідки.",
        SPYMASTER_GUESS_ERROR="🧙‍♂️ Капітанам не можна відгадувати слова!",
        SPYMASTER_BUFF_ONLY="🔒 Тільки капітани можуть використовувати бафи!",
        START_GAME_FIRST="🎮 Спочатку почніть гру в групі!",
        NO_GAME_IN_CHAT="У цьому чаті зараз немає активної гри",
        START_GAME_BTN="🎮 Почати нову гру",
        REG_START_DESC="⚙️ <b>Налаштування Codenames Master</b>",

        INLINE_VALID_HINT_TITLE="💡 {word} {count}",
        INLINE_VALID_HINT_DESC="Надіслати підказку гравцям",
        INLINE_HINT_TITLE="💡 Введіть підказку",
        INLINE_HINT_DESC="Напишіть слово та кількість, наприклад: яблуко 2",
        SECONDS="сек",
        TURN_NOTIFICATION="{icon} {mention}, ваш хід! (⏳ {time})",
        INLINE_INVALID_HINT_TITLE="⚠️ Введіть слово та число",
        INLINE_INVALID_HINT_DESC="Наприклад: {input} 2",
        EXAMPLE_WORD="Дерево",
        NOT_YOUR_TURN="🚫 Не ваш хід",
        NOT_YOUR_TURN_DESC="Зачекайте своєї черги, щоб вибирати слова або давати підказки.",
        NOT_A_PLAYER="🚫 Ви не є учасником гри",
        NOT_A_PLAYER_DESC="Натисніть тут, щоб приєднатися до гри та потрапити у випадкову команду!",

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
        ),
        CHAT_SETTINGS_TITLE="🛠 <b>Налаштування чату</b>",
        SETTING_ALLOW_EVERYONE_START="👥 Будь-хто може почати гру: {status}",
        ADMIN_ONLY_ERROR="❌ У цьому чаті тільки адміністратори можуть запускати гру.",

        SETTING_BUTTON_BOARD="⌨️ Карта кнопками в чаті: {status}",
        GAME_STOPPED="🛑 Гра зупинена адміністратором.",
        GAME_STOPPED_CONFIRM="Ви впевнені, що хочете зупинити гру?",
        PLAYER_LEFT="🏃 {name} покинув гру.",
        ONLY_ADMIN_STOP="❌ Тільки адміністратори або той, хто запустив гру, можуть її зупинити.",
        ADMIN_LOG_TITLE="⚙️ <b>Налаштування логів</b>",
        ADMIN_LOG_DEST="📍 Куди: <code>{dest}</code>",
        ADMIN_LOG_TYPES="✅ Типи: {types}",
        ADMIN_CHOOSE_ACTION="Оберіть дію:",
        ADMIN_LOG_HERE_BTN="📍 Обрати цей чат",
        ADMIN_LOG_ERRORS_BTN="Системні помилки",
        ADMIN_LOG_FEEDBACK_BTN="Фідбек гравців",
        ADMIN_CLOSE_BTN="❌ Закрити",
        ADMIN_NO_RIGHTS="У вас немає прав",
        ADMIN_LOG_SET_SUCCESS="✅ Логи перенаправлено сюди",
        ADMIN_UPDATED="Оновлено",
        SETTING_BUFFS="⚡ Бафи (Магазин): {status}",
        SETTING_DARK_MODE="🌙 Темна тема: {status}",
        BUFFS_ENABLED_MSG="✅ Бафи тепер {status} у цьому чаті.",
        FEEDBACK_PROMPT="📝 <b>Надішліть ваш відгук або повідомлення про помилку:</b>\n\nПросто напишіть текст нижче, і адміністратори отримають його.",
        FEEDBACK_SENT="✅ Дякуємо! Ваші повідомлення надіслано адміністраторам. Ви можете надіслати ще або завершити.",
        FEEDBACK_REPLY_TEMPLATE="💬 <b>Відповідь від адміністратора:</b>\n\n{text}",
        FEEDBACK_HEADER="👤 <code>[{id}]</code> {name}:",
        FINISH_FEEDBACK_BTN="✅ Завершити",
        FEEDBACK_SESSION_STARTED="📝 <b>Режим фідбеку активовано.</b> Усі ваші наступні повідомлення (текст, фото, голос) будуть передані адмінам, поки ви не натиснете кнопку або не напишете /done.",
        FEEDBACK_TOO_FAST="⏳ Занадто швидко! Зачекайте секунду перед наступним повідомленням.",
        FEEDBACK_LIMIT_REACHED="🛑 Ви досягли ліміту повідомлень для одного тікета (20). Будь ласка, завершіть цей та відкрийте новий пізніше.",
        SHOP_TITLE="🛒 <b>Магазин Тактичних Бафів</b>",
        SHOP_BALANCE="💎 Ваш баланс: <b>{balance}</b>",
        SHOP_BTN="🛒 Бафи",
        SHOP_ITEM_DESC="<b>{name}</b> — {price} 💎\n<i>{desc}</i>",
        BUY_SUCCESS="✅ Предмет придбано!",
        BUY_FAIL="❌ Недостатньо діамантів!",
        BUFF_NOT_AVAILABLE="Цей баф не можна використати зараз.",
        BUFF_ARMOR_NAME="🛡 Бронежилет",
        BUFF_DETECTOR_NAME="📡 Детектор",
        BUFF_INTERCEPT_NAME="⚡ Перехоплення",
        BUFF_REMAP_NAME="🗺 Зміна карти",
        BUFF_ARMOR_DESC="Рятує від 'Вбивці'. Дорогий, бо це 'друге життя'.",
        BUFF_DETECTOR_DESC="Підсвічує 1 нейтральне слово. Корисно для Капітана.",
        BUFF_INTERCEPT_DESC="Дозволяє не передавати хід після 1 помилки.",
        BUFF_REMAP_DESC="Змінює всі слова на полі на нові. Працює ТІЛЬКИ якщо ще жодне слово не відкрите.",
        BUFF_TARGETED_REMAP_NAME="🎯 Точкова заміна",
        BUFF_TARGETED_REMAP_DESC="Ви самі обираєте, яке слово на полі треба змінити.",
        SELECT_TARGETED_REMAP="🎯 <b>Оберіть слово для заміни:</b>\nНатисніть на номер картки на полі.",
        ALREADY_REVEALED="❌ Ця карта вже відкрита!",
        SPYMASTER_REMAP_ONLY="❌ Тільки капітан, що купив бафф, може змінити слово.",
        SHOP_DIAMONDS_TITLE="💎 <b>Магазин Алмазів</b>",
        SHOP_DIAMONDS_DESC="Оберіть пакет алмазів для купівлі тактичних бафів.",
        BUY_VIA_MONO="💳 Monobank (Карта)",
        BUY_VIA_STARS="🌟 Telegram Stars (x2)",
        PAYMENT_SUCCESS="✅ Оплата успішна! Вам нараховано <b>{amount}</b> 💎",
        PAYMENT_CHECK_BTN="🔄 Перевірити оплату",
        PAYMENT_PENDING="⏳ Оплата ще не надійшла. Спробуйте через хвилину.",
        PAYMENT_EXPIRED="❌ Час на оплату вичерпано. Створіть новий інвойс.",
        PAYMENT_ERROR="❌ Сталася помилка при створенні платежу.",
        ITEM_1000_NAME="💎 1,000 Алмазів",
        ITEM_5000_NAME="💎 5,000 Алмазів",
        ITEM_10000_NAME="💎 10,000 Алмазів",
        INVOICE_TITLE="Купівля {amount} 💎",
        INVOICE_DESC="Пакет алмазів для гри Codenames Master",
        MONO_MANUAL_INSTRUCTIONS="🏦 <b>Оплата через Monobank</b>\n\n1. Перейдіть за посиланням на Банку.\n2. Вкажіть суму: <b>{price} грн</b>.\n3. ⚠️ <b>ВАЖЛИВО:</b> В коментарі до платежу вкажіть код нижче.\n\nПісля перевірки адмін нарахує вам алмази.",
        MONO_MANUAL_CODE="Код для коментаря (натисніть, щоб скопіювати):\n<code>{code}</code>",
        OPEN_JAR_BTN="🏦 Перейти до Банки",
        COPY_CODE_BTN="📋 Скопіювати код",
        MANUAL_PAYMENT_NOTICE="📌 Адмін побачить ваш платіж і нарахує 💎 протягом 1-12 годин.",

    ),
    "en": CodenamesTexts(
        WELCOME="🕵️‍♂️ Welcome to <b>Codenames Master</b>!\n\nThe best bot for playing Codenames directly in Telegram.\n\n🎮 To start: /codenames\n📊 Your stats: /stats\n⚙️ Settings: /settings",
        CMD_CODENAMES="codenames",
        CMD_STATS="stats",
        CMD_SETTINGS="settings",
        REGISTRATION_TITLE="📝 <b>Codenames Registration</b>\nPlayers: {count}",
        JOIN_BTN="🙋‍♂️ Join Game",
        SET_BOARD_SIZE="📐 Board Size: {size}x{size}",
        CLOSE_BTN="Close",
        START_BTN="🚀 Start",
        CANCEL_BTN="🛑 Cancel",
        SETTINGS_BTN="⚙️ Settings",
        ALREADY_JOINED="ℹ️ You are already joined.",
        JOIN_SUCCESS="✅ You've joined the game in this chat!",
        BACK_TO_GAME="⬅️ Back to Game",
        MIN_PLAYERS="❌ At least 2 players required!",
        REG_TIMEOUT="🕒 <b>Registration timed out.</b> Game cancelled.",
        PLAYERS_LIST="Current players:",
        JOINED_MID_GAME="joined the game!",
        GAME_ALREADY_STARTED="❌ <b>Game is already in progress or lobby is created!</b>\nYou cannot start multiple games simultaneously in one chat.",
        TEAM_SIMPLE="Team",
        TEAM_GREEN="Green",
        TEAM_RED="Red",

        TURN_GREEN="🟢 GREEN Team's turn",
        TURN_RED="🔴 RED Team's turn",
        TURN_DUET="👥 Mode: Duet",
        CLUE_HINT="💡 Clue: <b>{clue}</b> ({count})",
        SPYMASTER_WAIT="👨‍✈️ Spymaster is giving a clue...",
        OPERATIVES_TURN="🤔 Operatives, make your choice!",
        TIME_UP="⏰ <b>Time's up!</b> Turn automatically passed.",
        PASS_BTN="⏭ Pass",
        BUFF_BTN="⚡ Buff: Recon",
        WIN_GREEN="🎉 <b>GREEN TEAM WINS!</b>",
        WIN_RED="🎉 <b>RED TEAM WINS!</b>",
        WIN_DUET="🎉 <b>VICTORY!</b> You've found all agents!",
        LOSE_DUET="💀 <b>DEFEAT!</b> You met the assassin.",
        GAME_OVER="🏁 <b>Game Over!</b>",
        DUET_HEADER="👥 <b>Mode: Duet</b>",
        CLASSIC_HEADER="🔍 <b>{team}'s turn</b>",
        TEAM_GREEN_GEN="🟢 GREEN",
        TEAM_RED_GEN="🔴 RED",
        DUET_TURN_MSG="🔍 Clue by: <b>{name}</b>",

        SPYMASTER_ROLE="🕵️‍♂️ You are the Spymaster for <b>{team}</b> team.",
        SPYMASTER_DUAL_ROLE="🕵️‍♂️ You are the <b>sole Spymaster</b> for both teams!",
        SPYMASTER_INSTRUCTIONS=(
            "🗺 <b>Your secret map</b> is above.\n"
            "💡 Type your clue <b>directly in the group chat</b>: <code>word number</code>"
        ),
        SPYMASTER_DM_ERROR=(
            "⚠️ Failed to send map to Spymaster {mention}.\n"
            "Make sure they have started the bot in DM!"
        ),
        GIVE_HINT_BTN="💡 Give Hint",
        CHOOSE_WORD_BTN="🔍 Choose Word",

        GAME_ENDED_TITLE="🎉 GAME OVER! <b>{winner}</b> won",
        GAME_STATS="⏱ Duration: <b>{duration}</b>\n🔎 Words found: <b>{found}/{total}</b>",
        NEW_CLUE="🔎 New clue: <b>{clue}</b> ({count})",
        REVEAL_BUFF_NAME="🕵️‍♂️ Recon (Reveal 1 word)",
        SELECT_BUFF_TITLE="⚡ <b>Select buff:</b>",
        REVEAL_BUFF_RESULT="🔍 Recon revealed: {word}",
        BUFF_USED_ERROR="❌ This buff was already used by your team!",
        NO_REVEAL_WORDS="❌ No words left to reveal.",
        SPYMASTER_GUESS_ERROR="🧙‍♂️ Spymasters cannot guess words!",
        SPYMASTER_BUFF_ONLY="🔒 Only spymasters can use buffs!",
        START_GAME_FIRST="🎮 Start the game in a group first!",
        NO_GAME_IN_CHAT="No active game in this chat",
        START_GAME_BTN="🎮 Start New Game",
        REG_START_DESC="⚙️ <b>Codenames Master Settings</b>",

        INLINE_VALID_HINT_TITLE="💡 {word} {count}",
        INLINE_VALID_HINT_DESC="Send clue to players",
        INLINE_HINT_TITLE="💡 Enter clue",
        INLINE_HINT_DESC="Type word and count, e.g.: apple 2",
        SECONDS="sec",
        TURN_NOTIFICATION="{icon} {mention}, your turn! (⏳ {time})",
        INLINE_INVALID_HINT_TITLE="⚠️ Enter word and number",
        INLINE_INVALID_HINT_DESC="Example: {input} 2",
        EXAMPLE_WORD="Tree",
        NOT_YOUR_TURN="🚫 Not your turn",
        NOT_YOUR_TURN_DESC="Wait for your turn to pick words or give clues.",
        NOT_A_PLAYER="🚫 You are not in the game",
        NOT_A_PLAYER_DESC="Click here to join and get assigned to a team!",

        SETTINGS_TITLE="⚙️ <b>Codenames Master Settings</b>",
        SET_MODE="🎮 Mode: {mode}",
        SET_LANG="🌐 Language: {lang}",
        SET_WORDS="📚 Dictionary: {words}",
        SET_TIMER_REG="🕒 Reg time: {time}m",
        SETTING_DARK_MODE="🌙 Dark Mode: {status}",
        SETTING_BUFFS="⚡ Buffs (Shop): {status}",
        SET_LANG_TITLE="🌐 <b>Select game language:</b>",
        SET_WORDS_TITLE="📚 <b>Select dictionary:</b>",
        SET_TMR_REG_TITLE="🕒 <b>Registration time:</b>",
        SET_TMR_TURN_TITLE="⏳ <b>Time per turn:</b>",
        SET_MODE_TITLE="🎮 <b>Select game mode:</b>",
        MODE_CLASSIC_BTN="⚔️ Classic (Team)",
        MODE_DUET_BTN="🤝 Duet (Co-op)",
        LANG_UK_BTN="Ukrainian 🇺🇦",
        LANG_EN_BTN="English 🇺🇸",
        WORD_SET_FORMAT="📖 {name}",
        MODE_DUET_DESC="👥 <b>Duet</b>: Cooperative mode!",
        MODE_3P_DESC="👥 <b>3-Player Mode</b>: One Spymaster for both teams!",
        MODE_CLASSIC_DESC="👥 Classic team-based mode.",
        GAME_STARTED_MSG="🏁 Game started! {desc}\nMaps sent to spymasters.",
        TIME_1M="1 minute",
        TIME_2M="2 minutes",
        TIME_3M="3 minutes",
        TIME_5M="5 minutes",
        TIME_10M="10 minutes",
        BACK_BTN="⬅️ Back",
        RETURN_BTN="⬅️ Return to Game",
        GAME_NOT_FOUND="❌ Game finished or not found.",
        NO_STATS="📊 You haven't played any games yet. Try it! /codenames",
        STATS_TEMPLATE=(
            "📊 <b>Your Codenames Stats</b>\n\n"
            "🎮 Total games: <b>{total}</b>\n"
            "✅ Wins: <b>{wins}</b>\n"
            "❌ Losses: <b>{losses}</b>\n\n"
            "🏆 Winrate: <b>{winrate:.1f}%</b>"
        ),
        CHAT_SETTINGS_TITLE="🛠 <b>Chat Settings</b>",
        SETTING_ALLOW_EVERYONE_START="👥 Anyone can start game: {status}",
        ADMIN_ONLY_ERROR="❌ Only administrators can start the game in this chat.",

        SETTING_BUTTON_BOARD="⌨️ Button board in chat: {status}",
        BUFFS_ENABLED_MSG="✅ Buffs are now {status} in this chat.",
        FEEDBACK_PROMPT="📝 <b>Send your feedback or bug report:</b>\n\nJust type your message below, and the administrators will receive it.",
        FEEDBACK_SENT="✅ Thank you! Your messages have been sent to the admins. You can send more or finish.",
        FEEDBACK_REPLY_TEMPLATE="💬 <b>Reply from administrator:</b>\n\n{text}",
        FEEDBACK_HEADER="👤 <code>[{id}]</code> {name}:",
        FINISH_FEEDBACK_BTN="✅ Finish",
        FEEDBACK_SESSION_STARTED="📝 <b>Feedback mode activated.</b> All your next messages (text, photos, voice) will be forwarded to admins until you click the button or type /done.",
        FEEDBACK_TOO_FAST="⏳ Too fast! Wait a second before the next message.",
        FEEDBACK_LIMIT_REACHED="🛑 You have reached the message limit for one ticket (20). Please finish this one and open a new one later.",

        GAME_STOPPED="🛑 Game stopped by administrator.",
        GAME_STOPPED_CONFIRM="Are you sure you want to stop the game?",
        PLAYER_LEFT="🏃 {name} left the game.",
        ONLY_ADMIN_STOP="❌ Only admins or the one who started can stop the game.",
        ADMIN_LOG_TITLE="⚙️ <b>Log Settings</b>",
        ADMIN_LOG_DEST="📍 Destination: <code>{dest}</code>",
        ADMIN_LOG_TYPES="✅ Types: {types}",
        ADMIN_CHOOSE_ACTION="Choose action:",
        ADMIN_LOG_HERE_BTN="📍 Select this chat",
        ADMIN_LOG_ERRORS_BTN="System Errors",
        ADMIN_LOG_FEEDBACK_BTN="Player Feedback",
        ADMIN_CLOSE_BTN="❌ Close",
        ADMIN_NO_RIGHTS="Insufficient permissions",
        ADMIN_LOG_SET_SUCCESS="✅ Logs redirected here",
        ADMIN_UPDATED="Updated",

        SHOP_TITLE="🛒 <b>Tactical Buff Shop</b>",
        SHOP_BALANCE="💎 Your balance: <b>{balance}</b>",
        SHOP_BTN="🛒 Buffs",
        SHOP_ITEM_DESC="<b>{name}</b> — {price} 💎\n<i>{desc}</i>",
        BUY_SUCCESS="✅ Item purchased!",
        BUY_FAIL="❌ Not enough diamonds!",
        BUFF_NOT_AVAILABLE="This buff cannot be used right now.",
        BUFF_ARMOR_NAME="🛡 Body Armor",
        BUFF_DETECTOR_NAME="📡 Detector",
        BUFF_INTERCEPT_NAME="⚡ Interception",
        BUFF_REMAP_NAME="🗺 Map Change",
        BUFF_ARMOR_DESC="Saves from 'Assassin'. Expensive because it's a 'second life'.",
        BUFF_DETECTOR_DESC="Highlights 1 neutral word. Useful for the Captain.",
        BUFF_INTERCEPT_DESC="Allows staying on turn after 1 mistake.",
        BUFF_REMAP_DESC="Replaces all words on the board with new ones. Works ONLY if no words have been revealed yet.",
        BUFF_TARGETED_REMAP_NAME="🎯 Targeted Swap",
        BUFF_TARGETED_REMAP_DESC="You choose exactly which word on the field to change.",
        SELECT_TARGETED_REMAP="🎯 <b>Select word to swap:</b>\nClick the card number on the field.",
        ALREADY_REVEALED="❌ This card is already revealed!",
        SPYMASTER_REMAP_ONLY="❌ Only the spymaster who bought the buff can swap the word.",

        SHOP_DIAMONDS_TITLE="💎 <b>Diamond Shop</b>",
        SHOP_DIAMONDS_DESC="Choose a diamond pack to buy tactical buffs.",
        BUY_VIA_MONO="💳 Monobank (Card)",
        BUY_VIA_STARS="🌟 Telegram Stars (x2)",
        PAYMENT_SUCCESS="✅ Payment successful! You received <b>{amount}</b> 💎",
        PAYMENT_CHECK_BTN="🔄 Check Payment",
        PAYMENT_PENDING="⏳ Payment not received yet. Try again in a minute.",
        PAYMENT_EXPIRED="❌ Payment time expired. Create a new invoice.",
        PAYMENT_ERROR="❌ Error creating payment.",
        ITEM_1000_NAME="💎 1,000 Diamonds",
        ITEM_5000_NAME="💎 5,000 Diamonds",
        ITEM_10000_NAME="💎 10,000 Diamonds",
        INVOICE_TITLE="Purchase {amount} 💎",
        INVOICE_DESC="Diamond pack for Codenames Master game",
        MONO_MANUAL_INSTRUCTIONS="🏦 <b>Payment via Monobank</b>\n\n1. Follow the link to the Jar.\n2. Enter the amount: <b>{price} UAH</b>.\n3. ⚠️ <b>IMPORTANT:</b> Include the code below in the payment comment.\n\nAfter verification, the admin will credit your diamonds.",
        MONO_MANUAL_CODE="Comment code (tap to copy):\n<code>{code}</code>",
        OPEN_JAR_BTN="🏦 Open Jar",
        COPY_CODE_BTN="📋 Copy Code",
        MANUAL_PAYMENT_NOTICE="📌 The admin will see your payment and credit 💎 within 1-12 hours.",
        SET_TIMER_TURN="⏳ Turn time: {time}m",
    ),
}


def get_text(lang: str = "uk") -> CodenamesTexts:
    return TEXTS.get(lang, TEXTS["uk"])
