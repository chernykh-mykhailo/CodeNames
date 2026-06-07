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
    PROFILE_TITLE: str
    PROFILE_CODE_NAME: str
    PROFILE_DIAMONDS: str
    PROFILE_COINS: str
    PROFILE_LEVEL: str
    PROFILE_NEXT_LEVEL: str
    PROFILE_COMBAT_STATS: str
    PROFILE_TOTAL_GAMES: str
    PROFILE_WINS: str
    PROFILE_LOSSES: str
    PROFILE_WINRATE: str
    PROFILE_GUESSED_WORDS: str
    PROFILE_ASSASSINS_HIT: str
    PROFILE_OPPONENT_WORDS_HIT: str
    PROFILE_INVENTORY: str
    PROFILE_INVENTORY_PCS: str
    PROFILE_CAPTAIN_BUFFS_BTN: str
    PROFILE_BUY_BUFFS_BTN: str
    PROFILE_BUY_DIAMONDS_BTN: str
    PROFILE_SENT_TO_DM: str
    PROFILE_BACK_BTN: str
    PROFILE_SHOP_DIAMONDS_TITLE: str
    PROFILE_SHOP_DIAMONDS_BALANCE: str
    PROFILE_SHOP_DIAMONDS_SELECT: str
    PROFILE_CAPTAIN_BUFFS_ONLY_ONE: str
    BUFF_SHOP_TITLE: str
    BUFF_SHOP_DIAMONDS: str
    BUFF_SHOP_COINS: str
    PLAYERS_LIST: str
    JOINED_MID_GAME: str
    GAME_ALREADY_STARTED: str
    TEAM_SIMPLE: str
    TEAM_GREEN: str
    TEAM_RED: str

    # Game UI
    JOIN_DUET: str
    JOIN_TEAM: str
    JOIN_TEAM_PLAYER: str
    JOIN_DUET_PLAYER: str
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
    PAST_CLUES_LABEL: str
    GOTO_BOT_CARD_BTN: str
    SPYMASTER_SHEET_BTN: str
    DUET_ROLE_DESC: str
    GOTO_GROUP_MAP_BTN: str
    GAME_NOT_FOUND_ALERT: str
    TURN_SWITCH_GIVER: str
    TURN_SWITCH_TEAM: str
    SCORE_REWARDS_TITLE: str
    SCORE_REWARDS_PLAYER: str
    REVEAL_RESULT_MSG: str
    DUET_TURN_GIVER_WAIT: str
    DUET_TURN_GIVER_HINT_WAIT: str
    STRICT_CLUE_ERROR_TITLE: str
    STRICT_CLUE_ERROR_DESC: str
    STRICT_CLUE_ERROR_MSG: str
    TURN_INFO_GUESS: str
    TURN_INFO_OPERATIVES: str
    HINT_ANNOUNCE: str
    HINT_COUNT_REQUIRED: str
    HINT_EMPTY_QUERY: str
    BUFF_ARMOR_APPLIED: str
    BUFF_INTERCEPT_APPLIED: str
    BUFF_DETECTOR_RESULT: str
    BUFF_REMAP_APPLIED: str
    BUFF_REMAP_ERROR: str
    BUFF_USED_INVENTORY: str
    BUFF_USED_DIAMONDS: str
    BUFF_MENU_SENT: str
    BUFF_MENU_DM_ERROR: str
    REVEAL_WORD_MSG: str
    REVEAL_NOT_FOUND: str
    REVEAL_WAIT_CLUE: str
    REVEAL_CAPTAIN_ERROR: str
    ADMIN_PANEL_TITLE: str
    ADMIN_LOG_SETTINGS_BTN: str
    ADMIN_COLOR_SETTINGS_BTN: str
    ADMIN_TEST_RENDER_UA_BTN: str
    ADMIN_TEST_RENDER_EN_BTN: str
    ADMIN_GIVE_FORMAT_ERROR: str
    ADMIN_GIVE_AMOUNT_ERROR: str
    ADMIN_USER_NOT_FOUND: str
    ADMIN_GIVE_USER_REQUIRED: str
    ADMIN_GIVE_SUCCESS: str
    ADMIN_GIVE_NOTIFY: str
    ADMIN_GIVE_ERROR: str
    ADMIN_REPLY_SENT: str
    ADMIN_REPLY_ERROR: str
    ADMIN_COLOR_EDIT_TITLE: str
    ADMIN_COLOR_EDIT_PROMPT: str
    ADMIN_COLOR_RESET_CONFIRM: str
    ADMIN_COLOR_FORMAT_ERROR: str
    ADMIN_COLOR_UPDATE_SUCCESS: str
    ADMIN_GB_FORMAT_ERROR: str
    ADMIN_GB_TYPE_ERROR: str
    ADMIN_GB_SUCCESS: str
    ADMIN_GB_NOTIFY: str
    ADMIN_GB_ERROR: str
    DICT_NAME_REQUIRED: str
    DICT_CREATE_TITLE: str
    DICT_CANCELLED: str
    DICT_FILE_FORMAT_ERROR: str
    DICT_INPUT_REQUIRED: str
    DICT_TOO_FEW_WORDS: str
    DICT_SAVE_SUCCESS: str
    DICT_EMPTY_LIST: str
    DICT_MY_LIST_TITLE: str
    MODE_HARDCORE_BTN: str
    TOP_LABEL_WINS: str
    TOP_LABEL_CLASSIC: str
    TOP_LABEL_DUET: str
    TOP_LABEL_HARDCORE: str
    TOP_LABEL_WORDS: str
    TOP_LABEL_CHAT: str
    TOP_LABEL_CHATS: str
    TOP_TITLE_WINS: str
    TOP_TITLE_WORDS: str
    TOP_TITLE_CHATS: str
    TOP_NO_DATA: str
    TOP_GLOBAL: str
    TOP_CHAT: str
    TEAM_GREEN_NAME: str
    TEAM_RED_NAME: str
    TEAM_GREEN_GEN_NAME: str
    TEAM_RED_GEN_NAME: str
    ROLE_USER: str
    ROLE_PARTNER: str
    POINTS_NAME: str
    ADMIN_PASS_SKIP_MSG: str
    ADMIN_PASS_SKIP_PROMPT: str
    PLAYER_PASSED_MSG: str
    GAME_WAIT_HINT: str
    GAME_WAIT_TURN: str
    BOARD_SEARCH_NOT_FOUND: str
    BOARD_CHOOSE_WORD_MSG: str
    BOARD_REVEAL_WAIT: str
    BOARD_REVEAL_WAIT_DESC: str
    QUICK_BUFF_PRIVATE_ERROR: str
    QUICK_BUFF_NO_GAME_ERROR: str
    GAME_SETTINGS_COLOR_TITLE: str
    GAME_SETTINGS_COLOR_PROMPT: str
    BOARD_REVEAL_TEAM_TURN_ERROR: str
    BOARD_REVEAL_WAIT_HINT_ERROR: str
    BOARD_REVEAL_WORD_PREFIX: str
    BOARD_REVEAL_COLOR_AGENT: str
    BOARD_REVEAL_COLOR_ASSASSIN: str
    BOARD_REVEAL_COLOR_NEUTRAL: str
    BOARD_REVEAL_COLOR_TEAM_GREEN: str
    BOARD_REVEAL_COLOR_TEAM_RED: str
    SETUP_SIZE_SET_MSG: str
    BUFF_USED_TEAM_NAME: str
    BUFF_DETECTOR_WORD: str
    BUFF_REMAP_SUCCESS: str
    BUFF_REMAP_OPEN_ERROR: str
    BUFF_INV_ANNOUNCE: str
    BUFF_BUY_ANNOUNCE: str
    INLINE_HINT_WAIT_TURN: str
    INLINE_HINT_STRICT_TITLE: str
    INLINE_HINT_STRICT_DESC: str
    INLINE_HINT_STRICT_MSG: str
    INLINE_REVEAL_TEAM_NAME: str
    INLINE_REVEAL_TURN_GUESS: str
    INLINE_REVEAL_TURN_OPERATIVES: str
    INLINE_REVEAL_NO_GAME_TITLE: str
    INLINE_REVEAL_NO_GAME_DESC: str
    INLINE_REVEAL_NO_GAME_MSG: str
    INLINE_REVEAL_WAIT_TITLE: str
    INLINE_REVEAL_NOT_FOUND_TITLE: str

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
    SETTING_PIN_MESSAGE: str
    SETTING_CAPTAIN_SHEET: str
    SETTING_PAST_CLUES: str
    SETTING_STRICT_CLUES: str
    SETTING_AUTO_BOT: str
    SETTING_AUTO_BOT_DIFFICULTY: str
    DIFFICULTY_EASY: str
    DIFFICULTY_MEDIUM: str
    DIFFICULTY_HARD: str
    AUTO_BOT_DIFFICULTY_CHANGED: str
    AUTOBOT_TITLE: str
    SET_BOARD_SIZE_TITLE: str

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
    PAYMENT_LINK_CREATED: str
    PAYMENT_PAY_BTN: str
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
    ADMIN_NO_ACTIVE_GAME: str
    ADMIN_LOG_SET_SUCCESS: str
    ADMIN_UPDATED: str
    ADMIN_DEBUG_INFO: str
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
    FEEDBACK_FINISHED: str
    FEEDBACK_UNAVAILABLE: str
    FEEDBACK_SEND_ERROR: str

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
    BUFF_AVOID_CAPTAIN_NAME: str
    BUFF_AVOID_CAPTAIN_DESC: str
    BUFF_BECOME_CAPTAIN_NAME: str
    BUFF_BECOME_CAPTAIN_DESC: str
    AVOID_CAPTAIN_ACTIVATED: str
    BECOME_CAPTAIN_ACTIVATED: str
    AVOID_CAPTAIN_DEACTIVATED: str
    BECOME_CAPTAIN_DEACTIVATED: str
    AVOID_CAPTAIN_TRIGGERED: str
    BECOME_CAPTAIN_TRIGGERED: str
    CAPTAIN_BUFF_NO_INVENTORY: str
    CAPTAIN_BUFF_ACTIVATE_BTN: str
    CAPTAIN_BUFF_DEACTIVATE_BTN: str
    BUFFS_MENU_TITLE: str
    BUFFS_ACTIVE_STATUS: str
    BUFFS_INACTIVE_STATUS: str
    CAPTAIN_BUFFS_SECTION: str
    BUY_AVOID_CAPTAIN_BTN: str
    BUY_BECOME_CAPTAIN_BTN: str
    BUFF_AVOID_CAPTAIN_SHORT: str
    BUFF_BECOME_CAPTAIN_SHORT: str
    BUFF_REVEAL_SHORT: str
    BUFF_ARMOR_PRICE: int = 35
    BUFF_DETECTOR_PRICE: int = 15
    BUFF_INTERCEPT_PRICE: int = 25
    BUFF_REMAP_PRICE: int = 10
    BUFF_TARGETED_REMAP_PRICE: int = 20
    BUFF_AVOID_CAPTAIN_PRICE: int = 50
    BUFF_BECOME_CAPTAIN_PRICE: int = 75
    BUFF_AVOID_CAPTAIN_PRICE_COINS: int = 250
    BUFF_BECOME_CAPTAIN_PRICE_COINS: int = 375


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
        PROFILE_TITLE="👤 <b>ОСОБОВА СПРАВА АГЕНТА:</b>",
        PROFILE_CODE_NAME="🔓 <b>Кодовий позивний:</b> {name}",
        PROFILE_DIAMONDS="💎 <b>Баланс (Діаманти):</b> <code>{balance}</code> 💎",
        PROFILE_COINS="🪙 <b>Баланс (Монети):</b> <code>{balance}</code> 🪙",
        PROFILE_LEVEL="🎖 <b>Рівень:</b> {level}",
        PROFILE_NEXT_LEVEL="✨ <i>До наступного рівня: {xp}/{needed} XP</i>",
        PROFILE_COMBAT_STATS="📊 <b>БОЙОВА СТАТИСТИКА:</b>",
        PROFILE_TOTAL_GAMES="├─ 🎮 Всього ігор: <b>{count}</b>",
        PROFILE_WINS="├─ 🏆 Перемоги: <b>{count}</b>",
        PROFILE_LOSSES="├─ 💀 Поразки: <b>{count}</b>",
        PROFILE_WINRATE="├─ 💯 Вінрейт: <b>{rate:.1f}%</b>",
        PROFILE_GUESSED_WORDS="├─ 🎯 Вгадано слів: <b>{count}</b>",
        PROFILE_ASSASSINS_HIT="├─ 💀 Обрано вбивць: <b>{count}</b>",
        PROFILE_OPPONENT_WORDS_HIT="└─ 💥 Слів чужої команди: <b>{count}</b>",
        PROFILE_INVENTORY="🎒 <b>СПЕЦ-ІНВЕНТАР (БАФИ):</b>",
        PROFILE_INVENTORY_PCS="",
        PROFILE_CAPTAIN_BUFFS_BTN="👑 Бафи капітана",
        PROFILE_BUY_BUFFS_BTN="🛒 Купити Бафи",
        PROFILE_BUY_DIAMONDS_BTN="💎 Купити Алмази",
        PROFILE_SENT_TO_DM="📨 Надіслав вам профіль в особисті повідомлення!",
        PROFILE_BACK_BTN="🔙 Назад до профілю",
        PROFILE_SHOP_DIAMONDS_TITLE="💎 <b>МАГАЗИН АЛМАЗІВ:</b>",
        PROFILE_SHOP_DIAMONDS_BALANCE="🛒 Баланс: <b>{balance}</b> алмазів",
        PROFILE_SHOP_DIAMONDS_SELECT="Оберіть пакет алмазів для придбання:",
        PROFILE_CAPTAIN_BUFFS_ONLY_ONE="⚠️ Можна активувати лише один баф одночасно!",
        BUFF_SHOP_TITLE="🛒 <b>МАГАЗИН БАФІВ</b>",
        BUFF_SHOP_DIAMONDS="💎 Діаманти: <b>{balance}</b>",
        BUFF_SHOP_COINS="🪙 Монети: <b>{balance}</b>",
        PLAYERS_LIST="Поточний склад:",
        JOINED_MID_GAME="приєднався до гри!",
        GAME_ALREADY_STARTED="❌ <b>Гра вже триває або лоббі вже створене!</b>\nВи не можете запустити кілька ігор одночасно в одному чаті.",
        TEAM_SIMPLE="Команда",
        TEAM_GREEN="Зелені",
        TEAM_RED="Червоні",
        JOIN_DUET="✅ Ви приєдналися до гри у кооперативному режимі (Duet)!",
        JOIN_TEAM="✅ Ви приєдналися до {team} команди!",
        JOIN_TEAM_PLAYER="➕ {emoji} {name} приєднався до {team} команди!",
        JOIN_DUET_PLAYER="➕ 🤝 {name} приєднався до кооперативної гри!",
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
        PAST_CLUES_LABEL="📜 Минулі загадки: {history}",
        GOTO_BOT_CARD_BTN="🤖 Перейти в бота (Карта)",
        SPYMASTER_SHEET_BTN="📋 Шпаргалка капітана",
        DUET_ROLE_DESC="🤝 <b>Кооперативний режим </b>\nВаша мета — відгадати всі зелені картки агентів разом з напарником!",
        GOTO_GROUP_MAP_BTN="🗺 До карти в групі",
        GAME_NOT_FOUND_ALERT="❌ Гра не знайдена",
        TURN_SWITCH_GIVER="🛑 Хід переходить до: {name} (дає підказку)!",
        TURN_SWITCH_TEAM="🛑 Хід переходить до команди: <b>{name}</b>!",
        SCORE_REWARDS_TITLE="📊 <b>Рахунок гри та Нагороди:</b>",
        SCORE_REWARDS_PLAYER="👤 {name}: {points} очок (🪙 +{coins})",
        REVEAL_RESULT_MSG="👉 <b>{name}</b>: <b>{word}</b> — <b>{color}</b>",
        DUET_TURN_GIVER_WAIT="Зараз черга вашої команди давати підказку, а не відгадувати!",
        DUET_TURN_GIVER_HINT_WAIT="Зачекайте, поки ваш напарник напише підказку!",
        STRICT_CLUE_ERROR_TITLE="⚠️ Підказка занадто схожа на слово на полі!",
        STRICT_CLUE_ERROR_DESC="Схожі: {words}",
        STRICT_CLUE_ERROR_MSG="⚠️ Підказка '{word}' занадто схожа на: {words}",
        TURN_INFO_GUESS="\n\n👉 Зараз черга відгадувати: {mentions}!",
        TURN_INFO_OPERATIVES="\n\n👉 Зараз хід оперативників команди: <b>{team}</b>!",
        HINT_ANNOUNCE="📢 Підказка: <b>{word}</b> {count}{info}",
        HINT_COUNT_REQUIRED="Введіть число, -, НЕОБМЕЖЕНО після слова {word}",
        HINT_EMPTY_QUERY="Введіть слово та число або - чи НЕОБМЕЖЕНО для безлімітних спроб, через пробіл",
        BUFF_ARMOR_APPLIED="🛡 Команда <b>{team}</b> застосувала {name}!",
        BUFF_INTERCEPT_APPLIED="⚡ Команда <b>{team}</b> застосувала {name}!",
        BUFF_DETECTOR_RESULT="📡 {name} виявив нейтральне слово: <b>{word}</b>!",
        BUFF_REMAP_APPLIED="🗺 <b>{name}</b> використав баф {buff} і змінив всі слова на полі!",
        BUFF_REMAP_ERROR="Цей баф можна використати ТІЛЬКИ до відкриття першого слова!",
        BUFF_USED_INVENTORY="✅ <b>{name}</b> використав баф <b>{buff}</b> з інвентарю!\n\n{result}",
        BUFF_USED_DIAMONDS="✅ <b>{name}</b> придбав баф за {price} 💎!\n\n{result}",
        BUFF_MENU_SENT="Відправив меню бафів вам в особисті повідомлення!",
        BUFF_MENU_DM_ERROR="❌ Спочатку почніть діалог з ботом в особистих повідомленнях!",
        REVEAL_WORD_MSG="🔎 Обрано слово: <b>{word}</b>",
        REVEAL_NOT_FOUND="Слово не знайдено на дошці",
        REVEAL_WAIT_CLUE="Чекаю на підказку.",
        REVEAL_CAPTAIN_ERROR="Капітани не можуть обирати слова.",
        ADMIN_PANEL_TITLE="👑 <b>Панель Адміністратора Codenames</b>\n\nТут ви можете керувати налаштуваннями бота та тестувати функції.\n\n💎 <b>Видача кристалів:</b>\nКоманда: <code>/give &lt;кількість&gt; [юзернейм/ID]</code> (або відповіддю на повідомлення користувача).",
        ADMIN_LOG_SETTINGS_BTN="⚙️ Налаштування логів",
        ADMIN_COLOR_SETTINGS_BTN="🎨 Налаштування теми кольорів",
        ADMIN_TEST_RENDER_UA_BTN="🖼️ Тест Рендеру (UA)",
        ADMIN_TEST_RENDER_EN_BTN="🖼️ Тест Рендеру (EN)",
        ADMIN_GIVE_FORMAT_ERROR="❌ Формат: <code>/give <кількість> [юзернейм/ID]</code> (або реплаєм)",
        ADMIN_GIVE_AMOUNT_ERROR="❌ Кількість має бути числом.",
        ADMIN_USER_NOT_FOUND="❌ Користувача {user} не знайдено в базі.",
        ADMIN_GIVE_USER_REQUIRED="❌ Використайте реплай або вкажіть юзернейм/ID.",
        ADMIN_GIVE_SUCCESS="✅ Видано <b>{amount}</b> 💎 користувачу <b>{name}</b> (ID: <code>{id}</code>)",
        ADMIN_GIVE_NOTIFY="🎁 Адміністратор видав вам <b>{amount}</b> 💎!",
        ADMIN_GIVE_ERROR="❌ Помилка при оновленні балансу.",
        ADMIN_REPLY_SENT="✅ Відповідь надіслано!",
        ADMIN_REPLY_ERROR="❌ Помилка при надсиланні: {error}",
        ADMIN_COLOR_EDIT_TITLE="🎨 <b>Зміна кольору: {key} ({mode})</b>",
        ADMIN_COLOR_EDIT_PROMPT="Введіть новий колір у форматі HEX (наприклад, <code>#FF0000</code>):",
        ADMIN_COLOR_RESET_CONFIRM="✅ Скинуто до стандартних кольорів!",
        ADMIN_COLOR_FORMAT_ERROR="❌ Некоректний формат. Спробуйте ще раз (наприклад, <code>#FF0000</code>):",
        ADMIN_COLOR_UPDATE_SUCCESS="✅ Колір <b>{key}</b> оновлено на <b>{text}</b>!",
        ADMIN_GB_FORMAT_ERROR="❌ Формат: <code>/gb <номер_бафу_або_назва> [кількість] [юзернейм/ID]</code>",
        ADMIN_GB_TYPE_ERROR="❌ Невірний тип бафу. Доступні: 1-5 або armor, intercept, detector, reveal, remap",
        ADMIN_GB_SUCCESS="✅ Нараховано <b>{quantity}x {buff}</b> користувачу <b>{name}</b> (ID: <code>{id}</code>)",
        ADMIN_GB_NOTIFY="🎁 Адміністратор видав вам баф: <b>{quantity}x {buff}</b>!",
        ADMIN_GB_ERROR="❌ Помилка при нарахуванні бафів.",
        DICT_NAME_REQUIRED="❌ Будь ласка, вкажіть назву словника: `/add_dict назва`",
        DICT_CREATE_TITLE="📝 <b>Створення словника '{name}'</b>\n\nБудь ласка, надішліть список слів через кому, кожне з нового рядка <b>або надішліть .txt файл</b>.\nМінімальна кількість слів для гри: 16 (рекомендовано 50+).\n\nНапишіть /cancel для скасування.",
        DICT_CANCELLED="❌ Скасовано.",
        DICT_FILE_FORMAT_ERROR="❌ Будь ласка, надішліть файл у форматі .txt",
        DICT_INPUT_REQUIRED="❌ Будь ласка, надішліть текст або .txt файл.",
        DICT_TOO_FEW_WORDS="❌ Занадто мало слів ({count}). Потрібно хоча б 16 для маленької карти (4х4). Надішліть ще.",
        DICT_SAVE_SUCCESS="✅ Словник <b>'{name}'</b> збережено! ({count} слів)\nТепер ви можете обрати його в налаштуваннях гри.",
        DICT_EMPTY_LIST="📭 У цьому чаті ще немає власних словників. Створіть перший: `/add_dict назва`",
        DICT_MY_LIST_TITLE="📚 <b>Власні словники чату:</b>\n\n",
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
        GAME_ENDED_TITLE="🎉 ГРУ ЗАКІНЧЕНО! <b>{winner}</b>",
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
        INLINE_INVALID_HINT_TITLE="⚠️ Введіть слово та число або - для необмеженої кількості",
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
        MODE_HARDCORE_BTN="💀 Hardcore (Хардкор)",
        TOP_LABEL_WINS="🏆 Перемоги",
        TOP_LABEL_CLASSIC="🎯 Classic",
        TOP_LABEL_DUET="🤝 Duet",
        TOP_LABEL_HARDCORE="💀 Hardcore",
        TOP_LABEL_WORDS="📝 Слова",
        TOP_LABEL_CHAT="👥 Чат",
        TOP_LABEL_CHATS="🏠 Чати",
        TOP_TITLE_WINS="🏆 <b>ТОП — {mode}</b> · За перемогами\n",
        TOP_TITLE_WORDS="📝 <b>ТОП — Вгадані слова</b>\n",
        TOP_TITLE_CHATS="🏠 <b>ТОП ЧАТІВ</b> · За іграми\n",
        TOP_NO_DATA="Ще немає даних 🤷",
        TOP_GLOBAL="Глобальний",
        TOP_CHAT="Чат",
        TEAM_GREEN_NAME="Зеленої 🟢",
        TEAM_RED_NAME="Червоної 🔴",
        TEAM_GREEN_GEN_NAME="Зеленої",
        TEAM_RED_GEN_NAME="Червоної",
        ROLE_USER="Користувач",
        ROLE_PARTNER="Напарник",
        POINTS_NAME="очок",
        ADMIN_PASS_SKIP_MSG="⚡ Адмін <b>{name}</b> примусово пропустив хід (AFK скіп)!",
        ADMIN_PASS_SKIP_PROMPT="⚠️ Натисніть «Пас» ще раз протягом 10 секунд, щоб ПРИМУСОВО скіпнути чужий хід (AFK).",
        PLAYER_PASSED_MSG="⏭ <b>{name}</b> натиснув(ла) пас.",
        GAME_WAIT_HINT="Я чекаю своєї черги.",
        GAME_WAIT_TURN="Чекаю на підказку.",
        BOARD_SEARCH_NOT_FOUND="Слово не знайдено на дошці",
        BOARD_CHOOSE_WORD_MSG="Я лише капітан.",
        BOARD_REVEAL_WAIT="Зачекайте",
        BOARD_REVEAL_WAIT_DESC="Чекаю на підказку.",
        QUICK_BUFF_PRIVATE_ERROR="🎮 Будь ласка, використовуйте швидкі команди бафів у групі, де йде гра!",
        QUICK_BUFF_NO_GAME_ERROR="❌ Зараз немає активної гри у цьому чаті!",
        GAME_SETTINGS_COLOR_TITLE="<b>🎨 Налаштування кольорів ({mode})</b>",
        GAME_SETTINGS_COLOR_PROMPT="Оберіть елемент для зміни кольору (формат: #RRGGBB):",
        BOARD_REVEAL_TEAM_TURN_ERROR="Зараз черга вашої команди давати підказку, а не відгадувати!",
        BOARD_REVEAL_WAIT_HINT_ERROR="Зачекайте, поки ваш напарник напише підказку!",
        BOARD_REVEAL_WORD_PREFIX="🔎 Обрано слово: ",
        BOARD_REVEAL_COLOR_AGENT="🟢 Агент (Зелене)",
        BOARD_REVEAL_COLOR_ASSASSIN="💀 Вбивця",
        BOARD_REVEAL_COLOR_NEUTRAL="⚪ Нейтральне",
        BOARD_REVEAL_COLOR_TEAM_GREEN="🟢 Зелена команда",
        BOARD_REVEAL_COLOR_TEAM_RED="🔴 Червона команда",
        SETUP_SIZE_SET_MSG="Розмір змінено на {size}x{size}",
        BUFF_USED_TEAM_NAME="{emoji} {name}",
        BUFF_DETECTOR_WORD="📡 {name} виявив нейтральне слово: <b>{word}</b>!",
        BUFF_REMAP_SUCCESS="🗺 <b>{name}</b> використав баф {buff} і змінив всі слова на полі!",
        BUFF_REMAP_OPEN_ERROR="Цей баф можна використати ТІЛЬКИ до відкриття першого слова!",
        BUFF_INV_ANNOUNCE="✅ <b>{name}</b> використав баф <b>{buff}</b> з інвентарю!\n\n{result}",
        BUFF_BUY_ANNOUNCE="✅ <b>{name}</b> придбав баф за {price} 💎!\n\n{result}",
        INLINE_HINT_WAIT_TURN="Я чекаю своєї черги.",
        INLINE_HINT_STRICT_TITLE="⚠️ Підказка занадто схожа на слово на полі!",
        INLINE_HINT_STRICT_DESC="Схожі: {words}",
        INLINE_HINT_STRICT_MSG="⚠️ Підказка '{word}' занадто схожа на: {words}",
        INLINE_REVEAL_TEAM_NAME="{emoji} {name}",
        INLINE_REVEAL_TURN_GUESS="\n\n👉 Зараз черга відгадувати: {mentions}!",
        INLINE_REVEAL_TURN_OPERATIVES="\n\n👉 Зараз хід оперативників команди: <b>{team}</b>!",
        INLINE_REVEAL_NO_GAME_TITLE="Гра не знайдена або вже завершена",
        INLINE_REVEAL_NO_GAME_DESC="Створіть нову гру за допомогою /codenames",
        INLINE_REVEAL_NO_GAME_MSG="Гра вже завершена. Створіть нову гру за допомогою /codenames",
        INLINE_REVEAL_WAIT_TITLE="Зачекайте",
        INLINE_REVEAL_NOT_FOUND_TITLE="Не знайдено",
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
        ADMIN_NO_ACTIVE_GAME="❌ У цьому чаті зараз немає активної гри",
        ADMIN_DEBUG_INFO="\n\n👑 Command to enable captain auto-bot debug mode: <code>/debug_autobot</code>",        ADMIN_LOG_SET_SUCCESS="✅ Логи перенаправлено сюди",
        ADMIN_UPDATED="Оновлено",
        SETTING_BUFFS="⚡ Бафи (Магазин): {status}",
        SETTING_DARK_MODE="🌙 Темна тема: {status}",
        SETTING_PIN_MESSAGE="📌 Закріпити повідомлення: {status}",
        SETTING_CAPTAIN_SHEET="📋 Шпаргалка капітана: {status}",
        SETTING_PAST_CLUES="📜 Минулі загадки: {status}",
        SETTING_STRICT_CLUES="🔍 Строгі підказки: {status}",
        SETTING_AUTO_BOT="🤖 Авто-бот ведучий: {status}",
        SETTING_AUTO_BOT_DIFFICULTY="🎯 Складність бота: {level}",
        DIFFICULTY_EASY="Легко",
        DIFFICULTY_MEDIUM="Середньо",
        DIFFICULTY_HARD="Важко",
        AUTO_BOT_DIFFICULTY_CHANGED="🤖 Складність бота змінена на: {level}",
        AUTOBOT_TITLE="Авто-бот ведучий",
        BUFFS_ENABLED_MSG="✅ Бафи тепер {status} у цьому чаті.",
        SET_BOARD_SIZE_TITLE="📐 <b>Оберіть розмір поля (кількість слів):</b>",
        FEEDBACK_PROMPT="📝 <b>Надішліть ваш відгук або повідомлення про помилку:</b>\n\nПросто напишіть текст нижче, і адміністратори отримають його.",
        FEEDBACK_SENT="✅ Дякуємо! Ваші повідомлення надіслано адміністраторам. Ви можете надіслати ще або завершити.",
        FEEDBACK_REPLY_TEMPLATE="💬 <b>Відповідь від адміністратора:</b>\n\n{text}",
        FEEDBACK_HEADER="👤 <code>[{id}]</code> {name}:",
        FINISH_FEEDBACK_BTN="✅ Завершити",
        FEEDBACK_SESSION_STARTED="📝 <b>Режим фідбеку активовано.</b> Усі ваші наступні повідомлення (текст, фото, голос) будуть передані адмінам, поки ви не натиснете кнопку або не напишете /done.",
        FEEDBACK_TOO_FAST="⏳ Занадто швидко! Зачекайте секунду перед наступним повідомленням.",
        FEEDBACK_LIMIT_REACHED="🛑 Ви досягли ліміту повідомлень для одного тікета (20). Будь ласка, завершіть цей та відкрийте новий пізніше.",
        FEEDBACK_FINISHED="✅ Режим фідбеку завершено. Дякуємо!",
        FEEDBACK_UNAVAILABLE="⚠️ Функція фідбеку тимчасово недоступна.",
        FEEDBACK_SEND_ERROR="❌ Помилка надсилання: {error}",
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
        BUFF_AVOID_CAPTAIN_NAME="🚫 Уникнути капітанства",
        BUFF_AVOID_CAPTAIN_DESC="Якщо бот обере вас капітаном (тим, хто дає підказки), баф спрацює і обере іншого гравця замість вас.",
        BUFF_BECOME_CAPTAIN_NAME="👑 Стати капітаном",
        BUFF_BECOME_CAPTAIN_DESC="Якщо бот обере когось іншого капітаном, баф може зробити капітаном вас замість нього.",
        BUFF_AVOID_CAPTAIN_PRICE=50,
        BUFF_BECOME_CAPTAIN_PRICE=75,
        AVOID_CAPTAIN_ACTIVATED="✅ Баф «Уникнути капітанства» активовано! Якщо вас оберуть капітаном — він спрацює.",
        BECOME_CAPTAIN_ACTIVATED="✅ Баф «Стати капітаном» активовано! Якщо оберуть іншого капітаном — ви маєте шанс стати ним.",
        AVOID_CAPTAIN_DEACTIVATED="🔄 Баф «Уникнути капітанства» деактивовано.",
        BECOME_CAPTAIN_DEACTIVATED="🔄 Баф «Стати капітаном» деактивовано.",
        AVOID_CAPTAIN_TRIGGERED="⚡ Баф «Уникнути капітанства» спрацював!\nГравець {player} мав стати капітаном, але замість нього капітаном став {replacement}.",
        BECOME_CAPTAIN_TRIGGERED="⚡ Баф «Стати капітаном» спрацював!\n{player} стає капітаном замість {original}!",
        CAPTAIN_BUFF_NO_INVENTORY="❌ У вас немає цього бафа в інвентарі.",
        CAPTAIN_BUFF_ACTIVATE_BTN="✅ Активувати",
        CAPTAIN_BUFF_DEACTIVATE_BTN="🔄 Деактивувати",
        BUFFS_MENU_TITLE="⚡ <b>Керування капітанськими бафами</b>\n\nАктивуйте баф в інвентарі, і він спрацює автоматично під час розподілу ролей у грі.",
        BUFFS_ACTIVE_STATUS="✅ АКТИВНО",
        BUFFS_INACTIVE_STATUS="❌ НЕАКТИВНО",
        BUFF_AVOID_CAPTAIN_PRICE_COINS=250,
        BUFF_BECOME_CAPTAIN_PRICE_COINS=375,
        BUFF_AVOID_CAPTAIN_SHORT="🚫 Уникнути кап.",
        BUFF_BECOME_CAPTAIN_SHORT="👑 Стати кап",
        BUFF_REVEAL_SHORT="🕵️ Розвідка",
        CAPTAIN_BUFFS_SECTION="👑 <b>Капітанські бафи (активуються в інвентарі):</b>",
        BUY_AVOID_CAPTAIN_BTN="🚫 Купити Уникнути кап.",
        BUY_BECOME_CAPTAIN_BTN="👑 Купити Стати кап.",
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
        PAYMENT_LINK_CREATED="🔗 Посилання на оплату {price} грн створено!",
        PAYMENT_PAY_BTN="💳 Оплатити",
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
        PROFILE_TITLE="👤 <b>AGENT DOSSIER:</b>",
        PROFILE_CODE_NAME="🔓 <b>Code Name:</b> {name}",
        PROFILE_DIAMONDS="💎 <b>Diamonds:</b> <code>{balance}</code> 💎",
        PROFILE_COINS="🪙 <b>Coins:</b> <code>{balance}</code> 🪙",
        PROFILE_LEVEL="🎖 <b>Level:</b> {level}",
        PROFILE_NEXT_LEVEL="✨ <i>Next Level in: {xp}/{needed} XP</i>",
        PROFILE_COMBAT_STATS="📊 <b>COMBAT STATS:</b>",
        PROFILE_TOTAL_GAMES="├─ 🎮 Total Games: <b>{count}</b>",
        PROFILE_WINS="├─ 🏆 Wins: <b>{count}</b>",
        PROFILE_LOSSES="├─ 💀 Losses: <b>{count}</b>",
        PROFILE_WINRATE="├─ 💯 Win Rate: <b>{rate:.1f}%</b>",
        PROFILE_GUESSED_WORDS="├─ 🎯 Guessed Words: <b>{count}</b>",
        PROFILE_ASSASSINS_HIT="├─ 💀 Hit Assassins: <b>{count}</b>",
        PROFILE_OPPONENT_WORDS_HIT="└─ 💥 Opponent Words: <b>{count}</b>",
        PROFILE_INVENTORY="🎒 <b>SPECIAL INVENTORY (BUFFS):</b>",
        PROFILE_INVENTORY_PCS=" pcs.",
        PROFILE_CAPTAIN_BUFFS_BTN="👑 Captain Buffs",
        PROFILE_BUY_BUFFS_BTN="🛒 Buy Buffs",
        PROFILE_BUY_DIAMONDS_BTN="💎 Buy Diamonds",
        PROFILE_SENT_TO_DM="📨 Sent your profile to DM!",
        PROFILE_BACK_BTN="🔙 Back to Profile",
        PROFILE_SHOP_DIAMONDS_TITLE="💎 <b>DIAMOND SHOP:</b>",
        PROFILE_SHOP_DIAMONDS_BALANCE="🛒 Balance: <b>{balance}</b> diamonds",
        PROFILE_SHOP_DIAMONDS_SELECT="Select a package to buy:",
        PROFILE_CAPTAIN_BUFFS_ONLY_ONE="⚠️ Only one buff can be active at a time!",
        BUFF_SHOP_TITLE="🛒 <b>BUFF SHOP</b>",
        BUFF_SHOP_DIAMONDS="💎 Diamonds: <b>{balance}</b>",
        BUFF_SHOP_COINS="🪙 Coins: <b>{balance}</b>",
        PLAYERS_LIST="Current players:",
        JOINED_MID_GAME="joined the game!",
        GAME_ALREADY_STARTED="❌ <b>Game is already in progress or lobby is created!</b>\nYou cannot start multiple games simultaneously in one chat.",
        TEAM_SIMPLE="Team",
        TEAM_GREEN="Green",
        TEAM_RED="Red",
        JOIN_DUET="✅ You joined the game in cooperative mode (Duet)!",
        JOIN_TEAM="✅ You joined the {team} team!",
        JOIN_TEAM_PLAYER="➕ {emoji} {name} joined the {team} team!",
        JOIN_DUET_PLAYER="➕ 🤝 {name} joined the cooperative game!",
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
        PAST_CLUES_LABEL="📜 Past clues: {history}",
        GOTO_BOT_CARD_BTN="🤖 Go to Bot (Map)",
        SPYMASTER_SHEET_BTN="📋 Captain's Sheet",
        DUET_ROLE_DESC="🤝 <b>Cooperative Mode</b>\nYour goal is to find all green agent cards with your partner!",
        GOTO_GROUP_MAP_BTN="🗺 To Group Map",
        GAME_NOT_FOUND_ALERT="❌ Game not found",
        TURN_SWITCH_GIVER="🛑 Turn goes to: {name} (giving hint)!",
        TURN_SWITCH_TEAM="🛑 Turn goes to: <b>{name}</b> team!",
        SCORE_REWARDS_TITLE="📊 <b>Game Score & Rewards:</b>",
        SCORE_REWARDS_PLAYER="👤 {name}: {points} points (🪙 +{coins})",
        REVEAL_RESULT_MSG="👉 <b>{name}</b>: <b>{word}</b> — <b>{color}</b>",
        DUET_TURN_GIVER_WAIT="It's your team's turn to give hints, not to guess!",
        DUET_TURN_GIVER_HINT_WAIT="Wait for your teammate to write a hint!",
        STRICT_CLUE_ERROR_TITLE="⚠️ Clue is too similar to a board word!",
        STRICT_CLUE_ERROR_DESC="Similar: {words}",
        STRICT_CLUE_ERROR_MSG="⚠️ Clue '{word}' too similar to: {words}",
        TURN_INFO_GUESS="\n\n👉 Now it's turn to guess: {mentions}!",
        TURN_INFO_OPERATIVES="\n\n👉 Now it's turn for operatives of: <b>{team}</b> team!",
        HINT_ANNOUNCE="📢 Hint: <b>{word}</b> {count}{info}",
        HINT_COUNT_REQUIRED="Enter a number after word {word}",
        HINT_EMPTY_QUERY="Enter word and number separated by space",
        BUFF_ARMOR_APPLIED="🛡 Team <b>{team}</b> applied {name}!",
        BUFF_INTERCEPT_APPLIED="⚡ Team <b>{team}</b> applied {name}!",
        BUFF_DETECTOR_RESULT="📡 {name} detected a neutral word: <b>{word}</b>!",
        BUFF_REMAP_APPLIED="🗺 <b>{name}</b> used {buff} buff and changed all words on the board!",
        BUFF_REMAP_ERROR="This buff can ONLY be used before the first word is revealed!",
        BUFF_USED_INVENTORY="✅ <b>{name}</b> used <b>{buff}</b> buff from inventory!\n\n{result}",
        BUFF_USED_DIAMONDS="✅ <b>{name}</b> purchased buff for {price} 💎!\n\n{result}",
        BUFF_MENU_SENT="Sent buff menu to your DMs!",
        BUFF_MENU_DM_ERROR="❌ Start a conversation with the bot in DMs first!",
        REVEAL_WORD_MSG="🔎 Word chosen: <b>{word}</b>",
        REVEAL_NOT_FOUND="Word not found on board",
        REVEAL_WAIT_CLUE="Waiting for clue.",
        REVEAL_CAPTAIN_ERROR="Captains cannot choose words.",
        ADMIN_PANEL_TITLE="👑 <b>Codenames Admin Panel</b>\n\nHere you can manage bot settings and test features.\n\n💎 <b>Give Diamonds:</b>\nCommand: <code>/give &lt;amount&gt; [username/ID]</code> (or reply to user).",
        ADMIN_LOG_SETTINGS_BTN="⚙️ Log Settings",
        ADMIN_COLOR_SETTINGS_BTN="🎨 Color Theme Settings",
        ADMIN_TEST_RENDER_UA_BTN="🖼️ Test Render (UA)",
        ADMIN_TEST_RENDER_EN_BTN="🖼️ Test Render (EN)",
        ADMIN_GIVE_FORMAT_ERROR="❌ Format: <code>/give <amount> [username/ID]</code> (or reply)",
        ADMIN_GIVE_AMOUNT_ERROR="❌ Amount must be a number.",
        ADMIN_USER_NOT_FOUND="❌ User {user} not found in database.",
        ADMIN_GIVE_USER_REQUIRED="❌ Use reply or specify username/ID.",
        ADMIN_GIVE_SUCCESS="✅ Given <b>{amount}</b> 💎 to user <b>{name}</b> (ID: <code>{id}</code>)",
        ADMIN_GIVE_NOTIFY="🎁 Administrator gave you <b>{amount}</b> 💎!",
        ADMIN_GIVE_ERROR="❌ Error updating balance.",
        ADMIN_REPLY_SENT="✅ Reply sent!",
        ADMIN_REPLY_ERROR="❌ Error sending: {error}",
        ADMIN_COLOR_EDIT_TITLE="🎨 <b>Change color: {key} ({mode})</b>",
        ADMIN_COLOR_EDIT_PROMPT="Enter new color in HEX format (e.g., <code>#FF0000</code>):",
        ADMIN_COLOR_RESET_CONFIRM="✅ Reset to default colors!",
        ADMIN_COLOR_FORMAT_ERROR="❌ Invalid format. Try again (e.g., <code>#FF0000</code>):",
        ADMIN_COLOR_UPDATE_SUCCESS="✅ Color <b>{key}</b> updated to <b>{text}</b>!",
        ADMIN_GB_FORMAT_ERROR="❌ Format: <code>/gb <buff_number_or_name> [amount] [username/ID]</code>",
        ADMIN_GB_TYPE_ERROR="❌ Invalid buff type. Available: 1-5 or armor, intercept, detector, reveal, remap",
        ADMIN_GB_SUCCESS="✅ Given <b>{quantity}x {buff}</b> to user <b>{name}</b> (ID: <code>{id}</code>)",
        ADMIN_GB_NOTIFY="🎁 Administrator gave you a buff: <b>{quantity}x {buff}</b>!",
        ADMIN_GB_ERROR="❌ Error giving buffs.",
        DICT_NAME_REQUIRED="❌ Please specify dictionary name: `/add_dict name`",
        DICT_CREATE_TITLE="📝 <b>Creating dictionary '{name}'</b>\n\nPlease send a list of words separated by commas, each on a new line <b>or send a .txt file</b>.\nMinimum words for game: 16 (recommended 50+).\n\nType /cancel to cancel.",
        DICT_CANCELLED="❌ Cancelled.",
        DICT_FILE_FORMAT_ERROR="❌ Please send a .txt file",
        DICT_INPUT_REQUIRED="❌ Please send text or a .txt file.",
        DICT_TOO_FEW_WORDS="❌ Too few words ({count}). Need at least 16 for a small map (4x4). Send more.",
        DICT_SAVE_SUCCESS="✅ Dictionary <b>'{name}'</b> saved! ({count} words)\nYou can now select it in game settings.",
        DICT_EMPTY_LIST="📭 This chat doesn't have custom dictionaries yet. Create one: `/add_dict name`",
        DICT_MY_LIST_TITLE="📚 <b>Chat's custom dictionaries:</b>\n\n",
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
        SET_TIMER_TURN="⏳ Turn time: {time}m",
        SET_LANG_TITLE="🌐 <b>Select game language:</b>",
        SET_WORDS_TITLE="📚 <b>Select dictionary:</b>",
        SET_TMR_REG_TITLE="🕒 <b>Registration time:</b>",
        SET_TMR_TURN_TITLE="⏳ <b>Time per turn:</b>",
        SET_MODE_TITLE="🎮 <b>Select game mode:</b>",
        MODE_CLASSIC_BTN="⚔️ Classic (Team)",
        MODE_DUET_BTN="🤝 Duet (Co-op)",
        MODE_HARDCORE_BTN="💀 Hardcore",
        TOP_LABEL_WINS="🏆 Wins",
        TOP_LABEL_CLASSIC="🎯 Classic",
        TOP_LABEL_DUET="🤝 Duet",
        TOP_LABEL_HARDCORE="💀 Hardcore",
        TOP_LABEL_WORDS="📝 Words",
        TOP_LABEL_CHAT="👥 Chat",
        TOP_LABEL_CHATS="🏠 Chats",
        TOP_TITLE_WINS="🏆 <b>TOP — {mode}</b> · By wins\n",
        TOP_TITLE_WORDS="📝 <b>TOP — Guessed Words</b>\n",
        TOP_TITLE_CHATS="🏠 <b>TOP CHATS</b> · By games\n",
        TOP_NO_DATA="No data yet 🤷",
        TOP_GLOBAL="Global",
        TOP_CHAT="Chat",
        TEAM_GREEN_NAME="Green 🟢",
        TEAM_RED_NAME="Red 🔴",
        TEAM_GREEN_GEN_NAME="Green",
        TEAM_RED_GEN_NAME="Red",
        ROLE_USER="User",
        ROLE_PARTNER="Partner",
        POINTS_NAME="points",
        ADMIN_PASS_SKIP_MSG="⚡ Admin <b>{name}</b> force-skipped the turn (AFK skip)!",
        ADMIN_PASS_SKIP_PROMPT="⚠️ Press «Pass» again within 10 seconds to FORCE skip someone else's turn (AFK).",
        PLAYER_PASSED_MSG="⏭ <b>{name}</b> passed.",
        GAME_WAIT_HINT="I'm waiting for my turn.",
        GAME_WAIT_TURN="Waiting for clue.",
        BOARD_SEARCH_NOT_FOUND="Word not found on board",
        BOARD_CHOOSE_WORD_MSG="I am just a captain.",
        BOARD_REVEAL_WAIT="Wait",
        BOARD_REVEAL_WAIT_DESC="Waiting for clue.",
        QUICK_BUFF_PRIVATE_ERROR="🎮 Please use quick buff commands in the group where the game is!",
        QUICK_BUFF_NO_GAME_ERROR="❌ No active game in this chat!",
        GAME_SETTINGS_COLOR_TITLE="<b>🎨 Color Settings ({mode})</b>",
        GAME_SETTINGS_COLOR_PROMPT="Choose element to change color (format: #RRGGBB):",
        BOARD_REVEAL_TEAM_TURN_ERROR="It's your team's turn to give hints, not to guess!",
        BOARD_REVEAL_WAIT_HINT_ERROR="Wait for your teammate to write a hint!",
        BOARD_REVEAL_WORD_PREFIX="🔎 Word chosen: ",
        BOARD_REVEAL_COLOR_AGENT="🟢 Agent (Green)",
        BOARD_REVEAL_COLOR_ASSASSIN="💀 Assassin",
        BOARD_REVEAL_COLOR_NEUTRAL="⚪ Neutral",
        BOARD_REVEAL_COLOR_TEAM_GREEN="🟢 Green Team",
        BOARD_REVEAL_COLOR_TEAM_RED="🔴 Red Team",
        SETUP_SIZE_SET_MSG="Size set to {size}x{size}",
        BUFF_USED_TEAM_NAME="{emoji} {name}",
        BUFF_DETECTOR_WORD="📡 {name} detected a neutral word: <b>{word}</b>!",
        BUFF_REMAP_SUCCESS="🗺 <b>{name}</b> used {buff} buff and changed all words on the board!",
        BUFF_REMAP_OPEN_ERROR="This buff can ONLY be used before the first word is revealed!",
        BUFF_INV_ANNOUNCE="✅ <b>{name}</b> used <b>{buff}</b> buff from inventory!\n\n{result}",
        BUFF_BUY_ANNOUNCE="✅ <b>{name}</b> purchased buff for {price} 💎!\n\n{result}",
        INLINE_HINT_WAIT_TURN="I'm waiting for my turn.",
        INLINE_HINT_STRICT_TITLE="⚠️ Clue is too similar to a board word!",
        INLINE_HINT_STRICT_DESC="Similar: {words}",
        INLINE_HINT_STRICT_MSG="⚠️ Clue '{word}' too similar to: {words}",
        INLINE_REVEAL_TEAM_NAME="{emoji} {name}",
        INLINE_REVEAL_TURN_GUESS="\n\n👉 Now it's turn to guess: {mentions}!",
        INLINE_REVEAL_TURN_OPERATIVES="\n\n👉 Now it's turn for operatives of: <b>{team}</b> team!",
        INLINE_REVEAL_NO_GAME_TITLE="Game not found or finished",
        INLINE_REVEAL_NO_GAME_DESC="Create a new game with /codenames",
        INLINE_REVEAL_NO_GAME_MSG="Game finished. Create a new game with /codenames",
        INLINE_REVEAL_WAIT_TITLE="Wait",
        INLINE_REVEAL_NOT_FOUND_TITLE="Not found",
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
        FEEDBACK_FINISHED="✅ Feedback mode finished. Thank you!",
        FEEDBACK_UNAVAILABLE="⚠️ Feedback feature is temporarily unavailable.",
        FEEDBACK_SEND_ERROR="❌ Send error: {error}",
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
        ADMIN_NO_ACTIVE_GAME="❌ No active game in this chat",
        ADMIN_DEBUG_INFO="\n\n👑 Команда для включення режиму налагодження авто-бота ведучого капітана: <code>/debug_autobot</code>",
        ADMIN_LOG_SET_SUCCESS="✅ Logs redirected here",
        ADMIN_UPDATED="Updated",
        SETTING_BUFFS="⚡ Buffs (Shop): {status}",
        SETTING_DARK_MODE="🌙 Dark Mode: {status}",
        SETTING_PIN_MESSAGE="📌 Pin message: {status}",
        SETTING_CAPTAIN_SHEET="📋 Captain's sheet: {status}",
        SETTING_PAST_CLUES="📜 Past clues: {status}",
        SETTING_STRICT_CLUES="🔍 Strict clues: {status}",
        SETTING_AUTO_BOT="🤖 Auto-bot host: {status}",
        SETTING_AUTO_BOT_DIFFICULTY="🎯 Bot difficulty: {level}",
        DIFFICULTY_EASY="Easy",
        DIFFICULTY_MEDIUM="Medium",
        DIFFICULTY_HARD="Hard",
        AUTO_BOT_DIFFICULTY_CHANGED="🤖 Bot difficulty changed to: {level}",
        AUTOBOT_TITLE="Auto-bot host",
        SET_BOARD_SIZE_TITLE="📐 <b>Select board size (word count):</b>",
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
        BUFF_AVOID_CAPTAIN_NAME="🚫 Avoid Captain",
        BUFF_AVOID_CAPTAIN_DESC="If the bot picks you as captain (spymaster), this buff will trigger and pick someone else instead.",
        BUFF_BECOME_CAPTAIN_NAME="👑 Become Captain",
        BUFF_BECOME_CAPTAIN_DESC="If the bot picks someone else as captain, this buff may make YOU the captain instead.",
        BUFF_AVOID_CAPTAIN_PRICE=50,
        BUFF_BECOME_CAPTAIN_PRICE=75,
        AVOID_CAPTAIN_ACTIVATED="✅ «Avoid Captain» buff activated! If you get picked as captain, it will trigger.",
        BECOME_CAPTAIN_ACTIVATED="✅ «Become Captain» buff activated! If someone else gets picked as captain, you might take over.",
        AVOID_CAPTAIN_DEACTIVATED="🔄 «Avoid Captain» buff deactivated.",
        BECOME_CAPTAIN_DEACTIVATED="🔄 «Become Captain» buff deactivated.",
        AVOID_CAPTAIN_TRIGGERED="⚡ «Avoid Captain» buff triggered!\nPlayer {player} was supposed to be captain, but {replacement} becomes captain instead.",
        BECOME_CAPTAIN_TRIGGERED="⚡ «Become Captain» buff triggered!\n{player} becomes captain instead of {original}!",
        CAPTAIN_BUFF_NO_INVENTORY="❌ You don't have this buff in inventory.",
        CAPTAIN_BUFF_ACTIVATE_BTN="✅ Activate",
        CAPTAIN_BUFF_DEACTIVATE_BTN="🔄 Deactivate",
        BUFFS_MENU_TITLE="⚡ <b>Captain Buff Management</b>\n\nActivate a buff from your inventory, and it will automatically trigger during role assignment.",
        BUFFS_ACTIVE_STATUS="✅ ACTIVE",
        BUFFS_INACTIVE_STATUS="❌ INACTIVE",
        BUFF_AVOID_CAPTAIN_PRICE_COINS=250,
        BUFF_BECOME_CAPTAIN_PRICE_COINS=375,
        BUFF_AVOID_CAPTAIN_SHORT="🚫 Avoid",
        BUFF_BECOME_CAPTAIN_SHORT="👑 Become",
        BUFF_REVEAL_SHORT="🕵️ Recon",
        CAPTAIN_BUFFS_SECTION="👑 <b>Captain Buffs (activate from inventory):</b>",
        BUY_AVOID_CAPTAIN_BTN="🚫 Buy Avoid Captain",
        BUY_BECOME_CAPTAIN_BTN="👑 Buy Become Captain",
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
        PAYMENT_LINK_CREATED="🔗 Payment link for {price} UAH created!",
        PAYMENT_PAY_BTN="💳 Pay",
    ),
}


def get_text(lang: str = "uk") -> CodenamesTexts:
    return TEXTS.get(lang, TEXTS["uk"])


def b(lang: str, uk: str, en: str) -> str:
    """Quick helper for localized strings."""
    return uk if lang == "uk" else en
