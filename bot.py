"""
╔══════════════════════════════════════╗
║     MARK AI — Telegram Bot v3.0      ║
║     Максимально повна версія         ║
╚══════════════════════════════════════╝
"""
import logging
import requests
import json
import os
import random
import asyncio
import qrcode
import io
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ══════════════════════════════════════
#  КОНФІГ
# ══════════════════════════════════════
TELEGRAM_TOKEN = "8542977906:AAHAWLOUpzhawn6UCDytCdhH8Xdqh4XnVkE"
GROQ_API_KEY   = "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"
GROQ_URL       = "https://api.groq.com/openai/v1/chat/completions"
DIALOG_FILE    = "dialog_history.json"
NOTES_FILE     = "notes_tg.txt"
TASKS_FILE     = "tasks_tg.json"
USERS_FILE     = "users_tg.json"
REFS_FILE      = "refs_tg.json"
PREMIUM_FILE   = "premium_tg.json"
MEMORY_FILE    = "memory_tg.json"
DIARY_FILE     = "diary_tg.json"
HABITS_FILE    = "habits_tg.json"
DIGEST_FILE    = "digest_tg.json"
HF_TOKEN       = "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"
STABILITY_KEY  = "sk-BhmOhn4eiBj5hEUE3WF5StJ60iRZ6QSwDErt3Gr4csvptG0z"
TOGETHER_KEY   = "key_CZZo6AfLjQFmWppys8ZDj"
ANTISPAM       : dict[int, list] = {}   # {user_id: [timestamps]}
ADMIN_ID       = 1780948739

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Стани та дані в пам'яті
user_histories : dict[int, list]  = {}
user_state     : dict[int, str]   = {}
guess_games    : dict[int, dict]  = {}   # {user_id: {number, attempts}}
user_profiles  : dict[int, dict]  = {}
user_lang      : dict[int, str]   = {}  # мова користувача

LANG_PROMPTS = {
    "uk": "Відповідай ВИКЛЮЧНО українською мовою.",
    "en": "Reply ONLY in English language.",
    "pl": "Odpowiadaj WYŁĄCZNIE w języku polskim.",
    "de": "Antworte NUR auf Deutsch.",
    "fr": "Réponds UNIQUEMENT en français.",
}

# ══════════════════════════════════════
#  КОНТЕНТ
# ══════════════════════════════════════
SYSTEM_PROMPT = """Ти — Марк, геніальний AI-асистент з характером.

Твоя особистість:
- Розумний, дотепний і щирий друг — не сухий робот
- Відповідаєш з теплотою і легким гумором коли доречно
- Якщо людина сумна або стресує — підтримуєш і надихаєш
- Якщо питання просте — відповідаєш коротко і по суті
- Якщо питання складне — даєш глибоку структуровану відповідь
- Іноді додаєш цікавий факт або несподіваний кут зору
- Пам'ятаєш контекст розмови і посилаєшся на нього

Правила відповідей:
- Відповідай ВИКЛЮЧНО українською мовою
- ЗАБОРОНЕНО: **, *, ##, ###, китайські/японські/арабські символи, LaTeX ($...$)
- Числа пиши просто: 2024, не $2024$
- Структуруй через нумерацію (1. 2. 3.) або тире (-)
- Відповіді змістовні але без зайвої води
- Ніколи не кажи "Як AI я не можу..." — просто допомагай
- Якщо не знаєш точної відповіді — скажи чесно і запропонуй альтернативу"""

JOKES = [
    "😂 Чому програмісти не люблять природу? Там забагато багів 🐛",
    "😄 Є 10 типів людей: ті що розуміють двійкову систему, і ті що ні 🤓",
    "🤣 Рекурсія — це коли для розуміння рекурсії треба зрозуміти рекурсію 🔄",
    "😂 99 маленьких багів у коді. Виправив один — 127 маленьких багів 🐞",
    "😄 Чому Java-розробники носять окуляри? Бо не бачать C# 👓",
    "🤣 Git blame — найкращий детектор винних у команді 🕵️",
    "😂 Debugging — це як детектив де ти і злочинець і слідчий 🔍",
    "😄 Програміст пішов за хлібом. Дружина: купи 1 батон, якщо є яйця — купи 6. Купив 6 батонів 🥖",
    "🤣 Чому програмісти плутають Хелловін і Різдво? Бо Oct 31 == Dec 25 🎃",
    "😂 Є два типи людей: ті що роблять бекап, і ті що ще не втратили дані 💾",
]

FACTS = [
    "🐙 Восьминоги мають три серця і блакитну кров — справжні інопланетяни Землі!",
    "🍯 Мед ніколи не псується — в єгипетських пірамідах знайшли їстівний мед віком 3000 років!",
    "🍌 Банани радіоактивні через калій-40. Але не хвилюйся — треба з'їсти мільйони 😅",
    "⚡ Блискавка вдаряє в Землю ~100 разів на секунду — 8.6 мільйонів разів на день!",
    "🦈 Акули старіші за дерева — вони існують вже 450 мільйонів років!",
    "🧠 Людський мозок генерує ~70 000 думок на день — і більшість про їжу 🍕",
    "🌍 На Землі більше дерев ніж зірок у Чумацькому Шляху — 3 трильйони дерев!",
    "💤 Людина проводить у сні близько 26 років свого життя 😴",
    "🐘 Слони — єдині тварини що не вміють стрибати. Навіть якщо дуже хочуть 😄",
    "🦋 Метелики відчувають смак ногами — у них смакові рецептори на лапках!",
    "🌙 На Місяці є сліди Ніла Армстронга — і вони збережуться мільйони років бо там немає вітру!",
    "🐬 Дельфіни сплять з одним відкритим оком — половина мозку завжди чергує!",
]

MOTIVATIONS = [
    "💪 Ти можеш більше ніж думаєш — просто почни!",
    "🚀 Кожен великий проект починався з першого рядка коду!",
    "⭐ Помилки — це просто кроки до успіху. Продовжуй!",
    "🔥 Ти вже далі ніж вчора — це і є прогрес!",
    "🌟 Сьогодні хороший день щоб стати кращою версією себе!",
    "💡 Геніальні ідеї приходять до тих хто діє, а не чекає!",
    "🏆 Успіх — це сума маленьких зусиль день за днем!",
    "🌈 Після кожного важкого дня є новий шанс. Тримайся!",
]

HOROSCOPES = {
    "овен":     "♈ Овен: Зірки на твоєму боці 🌟 Сміливо беріться за нові проекти! Енергія б'є через край 💪",
    "телець":   "♉ Телець: День для відпочинку та планування 📋 Не поспішай — мудрість у паузі 🧘",
    "близнюки": "♊ Близнюки: Відмінний день для спілкування 🤝 Твоє слово — золото сьогодні ✨",
    "рак":      "♋ Рак: Прислухайся до інтуїції 🔮 Серце знає правильну відповідь ❤️",
    "лев":      "♌ Лев: Твій час сяяти! ☀️ Покажи всім на що здатен — сцена твоя 🎭",
    "діва":     "♍ Діва: Зосередься на деталях 🔍 Перфекціонізм — твоя суперсила 💎",
    "терези":   "♎ Терези: Шукай баланс ⚖️ Компроміс — твоя сила. Гармонія близько 🌸",
    "скорпіон": "♏ Скорпіон: Глибокий аналіз відкриє правду 🕵️ Таємниці розкриваються 🗝️",
    "стрілець": "♐ Стрілець: Пригоди чекають! 🏹 Виходь із зони комфорту — там і починається життя 🌈",
    "козеріг":  "♑ Козеріг: Наполеглива праця принесе плоди 🌱 Ти будуєш щось велике 🏔️",
    "водолій":  "♒ Водолій: Твої ідеї геніальні — час реалізувати! 💡 Світ чекає на тебе 🚀",
    "риби":     "♓ Риби: Творчий день 🎨 Дай волю уяві. Муза вже поруч 🦋",
}

# ══════════════════════════════════════
#  КЛАВІАТУРА
# ══════════════════════════════════════
MAIN_KB = ReplyKeyboardMarkup([
    ["🌤 Погода",    "📰 Новини",    "💱 Валюта"],
    ["😂 Жарт",      "🧠 Факт",      "🔮 Гороскоп"],
    ["📝 Нотатки",   "✅ Задачі",    "⏰ Нагадування"],
    ["🧮 Калькулятор","📖 Вікіпедія","🌐 Переклад"],
    ["🎲 Ігри",      "📷 QR-код",    "₿ Крипта"],
    ["🎨 Генерація", "🎵 Музика",    "⭐ Преміум"],
    ["🍽 Калорії",   "📊 Статистика","❓ Допомога"],
    ["💪 Мотивація", "💻 Код",  "🖼 Цитата",  "🎭 Персонаж", "➡️ Ще функції"],], resize_keyboard=True)

PAGE2_KB = ReplyKeyboardMarkup([
    ["⭐ Купити Преміум", "👥 Реферали"],
    ["📊 Мій статус",    "🔗 Моє посилання"],
    ["🔐 Пароль",        "🎭 Настрій",    "📐 Конвертер"],
    ["🌐 Мова AI",       "📋 Шпаргалка",  "✍️ Граматика"],
    ["📱 Пост",          "💡 Бізнес-ідея","💰 Витрати"],
    ["🧠 Вікторина",     "💑 Сумісність", "😂 Мем"],
    ["📅 Розклад",       "🏆 Лідерборд",  "➡️ Сторінка 3", "⬅️ Назад"],], resize_keyboard=True)

PAGE3_KB = ReplyKeyboardMarkup([
    ["🍅 Помодоро",      "🎮 Нікнейм",    "🌐 Перевірка сайту"],
    ["📝 Резюме тексту", "🔄 Синоніми",   "🌍 Країна по IP"],
    ["🧠 Моя пам'ять",   "🔬 Глибокий аналіз", "⬅️ Назад"],
    ["🔗 Аналіз сайту",  "🎭 Дебати",  "🎬 Комікс",  "⬅️ Назад"],
    ["📓 Щоденник",      "💪 Звички",           "📋 Резюме/CV"],
    ["🌅 Дайджест",      "📺 YouTube",          "⬅️ Назад"],
], resize_keyboard=True)

def hs_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("♈ Овен",    callback_data="hs|овен"),
         InlineKeyboardButton("♉ Телець",  callback_data="hs|телець"),
         InlineKeyboardButton("♊ Близнюки",callback_data="hs|близнюки")],
        [InlineKeyboardButton("♋ Рак",     callback_data="hs|рак"),
         InlineKeyboardButton("♌ Лев",     callback_data="hs|лев"),
         InlineKeyboardButton("♍ Діва",    callback_data="hs|діва")],
        [InlineKeyboardButton("♎ Терези",  callback_data="hs|терези"),
         InlineKeyboardButton("♏ Скорпіон",callback_data="hs|скорпіон"),
         InlineKeyboardButton("♐ Стрілець",callback_data="hs|стрілець")],
        [InlineKeyboardButton("♑ Козеріг", callback_data="hs|козеріг"),
         InlineKeyboardButton("♒ Водолій", callback_data="hs|водолій"),
         InlineKeyboardButton("♓ Риби",    callback_data="hs|риби")],
    ])

def games_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Вгадай число", callback_data="game|guess"),
         InlineKeyboardButton("🎲 Кубик",        callback_data="game|dice")],
        [InlineKeyboardButton("🪙 Монетка",       callback_data="game|coin"),
         InlineKeyboardButton("🔢 Рандом 1-100",  callback_data="game|random")],
        [InlineKeyboardButton("✂️ Камінь-ножиці-папір", callback_data="game|rps")],
    ])

def crypto_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("₿ BTC",  callback_data="crypto|bitcoin"),
         InlineKeyboardButton("Ξ ETH",  callback_data="crypto|ethereum"),
         InlineKeyboardButton("◎ SOL",  callback_data="crypto|solana")],
        [InlineKeyboardButton("BNB",    callback_data="crypto|binancecoin"),
         InlineKeyboardButton("💵 USDT",callback_data="crypto|tether"),
         InlineKeyboardButton("🔵 TON", callback_data="crypto|the-open-network")],
    ])

def translate_keyboard(text: str):
    t = text[:200]  # обмеження довжини для callback_data
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇦 Укр",  callback_data=f"tr|uk|{t}"),
         InlineKeyboardButton("🇬🇧 Англ", callback_data=f"tr|en|{t}"),
         InlineKeyboardButton("🇩🇪 Нім",  callback_data=f"tr|de|{t}")],
        [InlineKeyboardButton("🇵🇱 Пол",  callback_data=f"tr|pl|{t}"),
         InlineKeyboardButton("🇫🇷 Фр",   callback_data=f"tr|fr|{t}"),
         InlineKeyboardButton("🇪🇸 Ісп",  callback_data=f"tr|es|{t}")],
    ])

# ══════════════════════════════════════
#  AI
# ══════════════════════════════════════
def ask_ai(user_id: int, message: str) -> str:
    history = user_histories.setdefault(user_id, [])
    history.append({"role": "user", "content": message})
    lang = user_lang.get(user_id, "uk")
    lang_instruction = LANG_PROMPTS.get(lang, LANG_PROMPTS["uk"])
    system = SYSTEM_PROMPT.replace(
        "Відповідай ВИКЛЮЧНО українською мовою",
        lang_instruction
    )
    # Додаємо пам'ять про користувача
    mem_text = memory_to_text(load_memory(user_id))
    if mem_text:
        system += f"\n\nЩо ти знаєш про цього користувача:\n{mem_text}\nВикористовуй цю інформацію щоб відповіді були персоналізованими."
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system}] + history[-20:],
        "temperature": 0.8,
        "max_tokens": 8000,
    }
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        if len(history) > 40:
            user_histories[user_id] = history[-40:]
        # Витягуємо факти з розмови у фоні
        extract_and_update_memory(user_id, message, reply)
        return clean_ai_text(reply)
    except Exception as e:
        return f"😴 AI тимчасово недоступний. Спробуй ще раз! ({e})"
def split_long_message(text: str, limit: int = 4000) -> list[str]:
    """Розбиває довгий текст на частини не більше limit символів"""
    if len(text) <= limit:
        return [text]
    parts = []
    while text:
        if len(text) <= limit:
            parts.append(text)
            break
        # Шукаємо останній перенос рядка в межах ліміту
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = text.rfind(" ", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(text[:cut].strip())
        text = text[cut:].strip()
    return parts

def ask_ai_deep(user_id: int, task: str) -> str:
    """Режим глибокого аналізу — бот думає крок за кроком"""
    lang = user_lang.get(user_id, "uk")
    lang_instruction = LANG_PROMPTS.get(lang, LANG_PROMPTS["uk"])
    mem_text = memory_to_text(load_memory(user_id))
    system = (
        f"Ти — Марк, геніальний AI-асистент. {lang_instruction}\n"
        f"ЗАБОРОНЕНО: **, *, ##, ###, китайські символи, LaTeX.\n"
        f"Зараз ти в режимі ГЛИБОКОГО АНАЛІЗУ.\n"
        f"Підхід: розбий задачу на кроки, виконай кожен крок ретельно, "
        f"дай вичерпну відповідь. Не поспішай — якість важливіша за швидкість."
    )
    if mem_text:
        system += f"\n\nПро користувача:\n{mem_text}"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": task}
        ],
        "temperature": 0.5,
        "max_tokens": 8000,
    }
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return clean_ai_text(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return f"😴 Помилка: {e}"

def detect_language(text: str) -> str:
    """Визначає мову тексту через Groq"""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content":
            f"Detect language of this text. Reply with ONLY 2-letter ISO code (en, uk, de, fr, pl, es, ru, it, pt, ja, zh): {text[:100]}"}],
        "max_tokens": 5, "temperature": 0
    }
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
        return r.json()["choices"][0]["message"]["content"].strip().lower()[:2]
    except:
        return "en"

# ══════════════════════════════════════
#  ЗБЕРЕЖЕННЯ ДАНИХ
# ══════════════════════════════════════
def save_dialog(user_id: int, role: str, text: str):
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id, "role": role, "text": text
    }
    history = []
    if os.path.exists(DIALOG_FILE):
        try:
            with open(DIALOG_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            pass
    history.append(entry)
    with open(DIALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def count_dialogs(user_id: int) -> int:
    if not os.path.exists(DIALOG_FILE):
        return 0
    try:
        with open(DIALOG_FILE, "r", encoding="utf-8") as f:
            h = json.load(f)
        return sum(1 for e in h if e.get("user_id") == user_id and e.get("role") == "user")
    except:
        return 0

def register_user(user):
    users = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
        except:
            pass
    uid = str(user.id)
    is_new = uid not in users
    if is_new:
        users[uid] = {
            "name": user.first_name,
            "username": user.username,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    return is_new

# ══════════════════════════════════════
#  УТИЛІТИ
# ══════════════════════════════════════
def get_weather(city: str) -> str:
    # Спроба 1: wttr.in
    try:
        r = requests.get(
            f"https://wttr.in/{city}?format=%l:+%C+%t,+вологість+%h,+вітер+%w",
            timeout=10,
            headers={"User-Agent": "MarkBot/1.0"}
        )
        if r.status_code == 200 and r.text.strip() and "Unknown" not in r.text:
            return r.text.strip()
    except Exception as e:
        logging.warning(f"wttr.in failed: {e}")

    # Спроба 2: Open-Meteo (безкоштовний, без API ключа)
    try:
        # Спочатку геокодуємо місто
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=uk",
            timeout=8
        ).json()
        if geo.get("results"):
            loc = geo["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]
            name = loc.get("name", city)
            country = loc.get("country", "")
            weather = requests.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                f"&wind_speed_unit=kmh",
                timeout=8
            ).json()
            cur = weather.get("current", {})
            temp = cur.get("temperature_2m", "?")
            hum  = cur.get("relative_humidity_2m", "?")
            wind = cur.get("wind_speed_10m", "?")
            code = cur.get("weather_code", 0)
            # Простий опис за кодом
            if code == 0: desc = "Ясно"
            elif code <= 3: desc = "Хмарно"
            elif code <= 67: desc = "Дощ"
            elif code <= 77: desc = "Сніг"
            elif code <= 99: desc = "Гроза"
            else: desc = "Змінна хмарність"
            return f"{name}, {country}: {desc} {temp}°C, вологість {hum}%, вітер {wind} км/г"
        return "😕 Місто не знайдено. Перевір назву."
    except Exception as e:
        logging.warning(f"open-meteo failed: {e}")
        return "😕 Не вдалося отримати погоду. Спробуй ще раз."

def get_news() -> str:
    try:
        import feedparser
        feed = feedparser.parse("https://www.ukrinform.ua/rss/block-lastnews")
        if feed.entries:
            lines = [f"{i+1}. {e.title}" for i, e in enumerate(feed.entries[:6])]
            return "\n\n".join(lines)
        return "😕 Новини недоступні."
    except:
        return "📡 Не вдалося завантажити новини."

def calculate(expr: str) -> str:
    try:
        safe = ''.join(c for c in expr if c in '0123456789+-*/(). %')
        if not safe.strip():
            return "❌ Порожній вираз."
        result = eval(safe)
        return f"🧮 {expr.strip()} = *{result}*"
    except ZeroDivisionError:
        return "❌ Ділення на нуль! 😅"
    except:
        return "❌ Не можу порахувати. Перевір вираз.\nПриклад: 25 * 4 + 10"

def deep_search(query: str, user_id: int) -> str:
    """Глибокий пошук: Wikipedia + DuckDuckGo + AI аналіз"""
    sources = []

    # 1. Wikipedia
    try:
        import wikipediaapi
        wiki = wikipediaapi.Wikipedia(language='uk', user_agent="MarkBot/5.0")
        page = wiki.page(query)
        if page.exists():
            sources.append(f"[Wikipedia]\n{page.summary[:1000]}")
        else:
            # Спробуємо англійською
            wiki_en = wikipediaapi.Wikipedia(language='en', user_agent="MarkBot/5.0")
            page_en = wiki_en.page(query)
            if page_en.exists():
                sources.append(f"[Wikipedia EN]\n{page_en.summary[:1000]}")
    except:
        pass

    # 2. DuckDuckGo Instant Answer API
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=8
        )
        data = r.json()
        if data.get("AbstractText"):
            sources.append(f"[DuckDuckGo]\n{data['AbstractText'][:800]}")
        if data.get("Answer"):
            sources.append(f"[Пряма відповідь]\n{data['Answer']}")
        # Пов'язані теми
        related = [t.get("Text","") for t in data.get("RelatedTopics", [])[:3] if t.get("Text")]
        if related:
            sources.append(f"[Пов'язане]\n" + "\n".join(related))
    except:
        pass

    if not sources:
        # Якщо нічого не знайшли — просто AI
        return ask_ai(user_id, f"Проведи глибокий аналіз і дай вичерпну відповідь про: {query}")

    # 3. AI аналізує всі джерела
    combined = "\n\n---\n\n".join(sources)
    prompt = (
        f"На основі цих даних з різних джерел дай ГЛИБОКИЙ і ВИЧЕРПНИЙ аналіз про '{query}'.\n"
        f"Структуруй відповідь: основне, деталі, цікаві факти, висновок.\n\n"
        f"ДАНІ:\n{combined[:3000]}"
    )
    return ask_ai(user_id, prompt)

def search_wiki(topic: str) -> str:
    try:
        import wikipediaapi
        wiki = wikipediaapi.Wikipedia(language='uk', user_agent="MarkBot/5.0")
        page = wiki.page(topic)
        if page.exists():
            text = page.summary[:700]
            return f"📖 *{page.title}*\n\n{text}\n\n🔗 {page.fullurl}"
        return f"🔍 Нічого не знайдено про '{topic}'. Спробуй інше формулювання."
    except:
        return "📡 Вікіпедія недоступна."

def get_currency(amount: float, from_cur: str, to_cur: str) -> str:
    from_cur = from_cur.upper()
    to_cur   = to_cur.upper()
    # Спробуємо frankfurter (підтримує UAH)
    try:
        r = requests.get(
            f"https://api.frankfurter.app/latest?amount={amount}&from={from_cur}&to={to_cur}",
            timeout=6
        )
        data = r.json()
        if "rates" in data and to_cur in data["rates"]:
            result = data["rates"][to_cur]
            return f"💱 {amount} {from_cur} = *{result:.2f} {to_cur}* 💰"
        if "error" in data:
            return f"❌ {data['error']}\nДоступні: USD, EUR, UAH, GBP, PLN, CZK, CHF, JPY..."
    except:
        pass
    # Запасний варіант
    try:
        r2 = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{from_cur}", timeout=6
        )
        rates = r2.json().get("rates", {})
        if to_cur in rates:
            result = round(amount * rates[to_cur], 2)
            return f"💱 {amount} {from_cur} = *{result} {to_cur}* 💰"
    except:
        pass
    return f"❌ Не вдалося конвертувати {from_cur} → {to_cur}.\nПеревір назви валют (USD, EUR, UAH, GBP...)"

def translate_text(text: str, target_lang: str) -> str:
    try:
        src = detect_language(text)
        if src == target_lang:
            src = "en" if target_lang != "en" else "uk"
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": f"{src}|{target_lang}"},
            timeout=10
        )
        result = r.json()["responseData"]["translatedText"]
        if "INVALID" in result or "ERROR" in result or "MYMEMORY" in result:
            raise ValueError("bad result")
        return result
    except:
        # Запасний — через AI
        return ask_ai(0, f"Перекладай ТІЛЬКИ текст без пояснень на мову '{target_lang}': {text}")

def generate_qr(text: str) -> io.BytesIO:
    img = qrcode.QRCode(version=1, box_size=10, border=4)
    img.add_data(text)
    img.make(fit=True)
    pil_img = img.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def get_crypto_price(coin_id: str) -> str:
    try:
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={coin_id}&vs_currencies=usd,uah&include_24hr_change=true",
            timeout=8
        )
        data = r.json()
        if coin_id in data:
            d = data[coin_id]
            usd    = d.get("usd", "?")
            uah    = d.get("uah", "?")
            change = d.get("usd_24h_change", 0)
            arrow  = "📈" if change >= 0 else "📉"
            name   = coin_id.replace("-", " ").title()
            return (f"₿ *{name}*\n"
                    f"💵 ${usd:,} USD\n"
                    f"💴 ₴{uah:,} UAH\n"
                    f"{arrow} За 24г: {change:+.2f}%")
        return "❌ Монету не знайдено."
    except:
        return "📡 Не вдалося отримати ціну криптовалюти."

def clean_ai_text(text: str) -> str:
    """Видаляє Markdown, LaTeX і сторонні символи з AI відповіді"""
    import re
    # LaTeX
    text = re.sub(r'\$+([^$]*)\$+', r'\1', text)
    # Bold/italic markdown
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    # Headers
    text = re.sub(r'#{1,6}\s*', '', text)
    # Inline code
    text = re.sub(r'`([^`]*)`', r'\1', text)
    # Китайські/японські/корейські символи
    text = re.sub(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+', '', text)
    # Зайві пробіли
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def clean_text(text: str) -> str:
    """Видаляє Markdown та LaTeX форматування"""
    import re
    text = re.sub(r'\$+([^$]*)\$+', r'\1', text)  # $...$
    text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]*)\*', r'\1', text)       # *italic*
    text = re.sub(r'#{1,6}\s*', '', text)             # ## headers
    text = re.sub(r'`([^`]*)`', r'\1', text)          # `code`
    return text.strip()

def analyze_image(image_url: str, question: str = "") -> str:
    """Розпізнає зображення через Groq Vision"""
    prompt = question if question else "Опиши детально що зображено на цій картинці українською мовою."
    prompt += "\n\nВАЖЛИВО: відповідай простим текстом БЕЗ Markdown, без **, ##, $, без жодного форматування."
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]}],
        "max_tokens": 1000,
    }
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return clean_text(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return f"❌ Не вдалося розпізнати зображення. ({e})"

def generate_image(prompt: str):
    """Генерує зображення через Pollinations AI"""
    import re as _re, urllib.parse
    # Перекладаємо якщо українська
    if _re.search(r'[а-яА-ЯіІїЇєЄ]', prompt):
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            r = requests.post(GROQ_URL, headers=headers, json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content":
                    f"Translate to English for image generation, add quality tags. Return ONLY the prompt: {prompt}"}],
                "max_tokens": 100, "temperature": 0.3
            }, timeout=10)
            improved = r.json()["choices"][0]["message"]["content"].strip()
            if improved and not _re.search(r'[а-яА-ЯіІїЇєЄ]', improved):
                prompt = improved
        except:
            pass
    seed = random.randint(1, 99999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width=1024&height=1024&nologo=true&seed={seed}"
    try:
        r = requests.get(url, timeout=35)
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
    except:
        pass
    return url  # Повертаємо URL якщо не вдалось завантажити

def get_image_url(prompt: str) -> str:
    import urllib.parse
    seed = random.randint(1, 99999)
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width=1024&height=1024&nologo=true&seed={seed}"

def generate_quote_image(quote: str, author: str = "") -> io.BytesIO:
    """Генерує мотиваційну картинку: красивий AI фон + текст цитати"""
    import urllib.parse
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    # Генеруємо красивий фон
    bg_prompts = [
        "breathtaking mountain sunset golden hour cinematic",
        "beautiful ocean waves at sunset dramatic sky",
        "misty forest morning light rays magical",
        "starry night sky milky way galaxy stunning",
        "cherry blossom trees spring light dreamy",
        "dramatic storm clouds lightning epic landscape",
        "northern lights aurora borealis night sky",
        "tropical beach paradise golden sunset",
    ]
    bg_prompt = random.choice(bg_prompts)
    # Завантажуємо фон через HuggingFace
    bg_url = generate_image(bg_prompt + ", wide landscape, no text, beautiful background")
    r_bg = requests.get(bg_url, timeout=20)
    if r_bg.status_code != 200:
        raise Exception("Не вдалося згенерувати фон")
    img = Image.open(io.BytesIO(r_bg.content)).convert("RGBA")
    img = img.resize((1080, 1080))

    # Темний градієнт знизу для читабельності тексту
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    for i in range(400):
        alpha = int(180 * (i / 400))
        draw_overlay.rectangle([(0, 1080 - 400 + i), (1080, 1080 - 400 + i + 1)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    # Шрифт — використовуємо системний або дефолтний
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        font_big = ImageFont.load_default()
        font_small = font_big

    # Переносимо текст
    wrapped = textwrap.fill(quote, width=28)
    lines = wrapped.split("\n")

    # Малюємо текст з тінню
    y = 1080 - 80 - len(lines) * 65 - (50 if author else 0)
    for line in lines:
        # Тінь
        draw.text((42, y + 2), line, font=font_big, fill=(0, 0, 0, 180))
        # Текст
        draw.text((40, y), line, font=font_big, fill=(255, 255, 255))
        y += 65

    if author:
        draw.text((42, y + 2), f"— {author}", font=font_small, fill=(0, 0, 0, 180))
        draw.text((40, y), f"— {author}", font=font_small, fill=(200, 200, 200))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf

def get_ip_info(ip: str = "") -> str:
    try:
        url = f"https://ipapi.co/{ip}/json/" if ip else "https://ipapi.co/json/"
        d = requests.get(url, timeout=6).json()
        if "error" in d:
            return f"❌ {d.get('reason', 'Помилка')}"
        return (f"🌍 *IP інформація*\n\n"
                f"📡 IP: `{d.get('ip')}`\n"
                f"🏳️ Країна: {d.get('country_name')} {d.get('country_code','')}\n"
                f"🏙 Місто: {d.get('city')}\n"
                f"🗺 Регіон: {d.get('region')}\n"
                f"🕐 Часовий пояс: {d.get('timezone')}\n"
                f"📶 Провайдер: {d.get('org')}")
    except:
        return "❌ Не вдалося отримати інформацію про IP."

def generate_password(length: int = 16) -> str:
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def analyze_mood(text: str) -> str:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content":
            f"Визнач настрій цього тексту. Відповідай ТІЛЬКИ одним рядком українською у форматі:\n"
            f"[емодзі] [настрій]: [коротке пояснення 1 речення]\n"
            f"Наприклад: 😊 Радісний: текст виражає позитивні емоції.\n\nТекст: {text[:500]}"}],
        "max_tokens": 100, "temperature": 0.3
    }
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return "😐 Нейтральний: не вдалося визначити настрій."

def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    conversions = {
        ("km", "mi"): 0.621371, ("mi", "km"): 1.60934,
        ("kg", "lb"): 2.20462,  ("lb", "kg"): 0.453592,
        ("m", "ft"):  3.28084,  ("ft", "m"):  0.3048,
        ("c", "f"):   None,     ("f", "c"):   None,
        ("l", "gal"): 0.264172, ("gal", "l"): 3.78541,
        ("cm", "in"): 0.393701, ("in", "cm"): 2.54,
    }
    f, t = from_unit.lower(), to_unit.lower()
    if (f, t) == ("c", "f"):
        result = value * 9/5 + 32
    elif (f, t) == ("f", "c"):
        result = (value - 32) * 5/9
    elif (f, t) in conversions and conversions[(f, t)]:
        result = value * conversions[(f, t)]
    else:
        return f"❌ Не знаю як конвертувати {from_unit} → {to_unit}\nДоступні: km/mi, kg/lb, m/ft, °C/°F, l/gal, cm/in"
    return f"📐 {value} {from_unit} = *{result:.4g} {to_unit}*"

def shorten_url(url: str) -> str:
    try:
        r = requests.get(f"https://tinyurl.com/api-create.php?url={url}", timeout=6)
        if r.status_code == 200 and r.text.startswith("http"):
            return f"🔗 Коротке посилання:\n{r.text}"
        return "❌ Не вдалося скоротити посилання."
    except:
        return "❌ Помилка скорочення посилання."

# ══════════════════════════════════════
#  ЛІМІТ ПОВІДОМЛЕНЬ
# ══════════════════════════════════════
FREE_DAILY_LIMIT = 20

def count_today_messages(user_id: int) -> int:
    if not os.path.exists(DIALOG_FILE):
        return 0
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        h = json.load(open(DIALOG_FILE, "r", encoding="utf-8"))
        return sum(1 for e in h
                   if e.get("user_id") == user_id
                   and e.get("role") == "user"
                   and e.get("date", "").startswith(today))
    except:
        return 0

def check_limit(user_id: int) -> tuple[bool, int]:
    """Повертає (дозволено, залишилось). Преміум і адмін — без ліміту."""
    if user_id == ADMIN_ID or is_premium(user_id):
        return True, 999
    used = count_today_messages(user_id)
    remaining = max(0, FREE_DAILY_LIMIT - used)
    return remaining > 0, remaining

# ══════════════════════════════════════
#  АНАЛІЗ ПОСИЛАНЬ
# ══════════════════════════════════════
def fetch_url_text(url: str) -> str:
    """Завантажує текст сторінки"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MarkBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        # Простий парсинг — видаляємо HTML теги
        import re
        text = r.text
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:5000]
    except Exception as e:
        return f"ERROR:{e}"

# ══════════════════════════════════════
#  АНТИСПАМ
# ══════════════════════════════════════
def check_antispam(user_id: int) -> bool:
    """Повертає True якщо дозволено, False якщо спам (>10 повід за 60 сек)"""
    if user_id == ADMIN_ID:
        return True
    now = datetime.now().timestamp()
    times = ANTISPAM.get(user_id, [])
    times = [t for t in times if now - t < 60]
    times.append(now)
    ANTISPAM[user_id] = times
    return len(times) <= 10

# ══════════════════════════════════════
#  ЩОДЕННИК
# ══════════════════════════════════════
def load_diary(user_id: int) -> list:
    if not os.path.exists(DIARY_FILE):
        return []
    try:
        data = json.load(open(DIARY_FILE, "r", encoding="utf-8"))
        return data.get(str(user_id), [])
    except:
        return []

def save_diary_entry(user_id: int, text: str):
    data = {}
    if os.path.exists(DIARY_FILE):
        try:
            data = json.load(open(DIARY_FILE, "r", encoding="utf-8"))
        except:
            pass
    entries = data.get(str(user_id), [])
    entries.append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "text": text})
    data[str(user_id)] = entries[-100:]  # зберігаємо останні 100
    json.dump(data, open(DIARY_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ══════════════════════════════════════
#  ТРЕКЕР ЗВИЧОК
# ══════════════════════════════════════
def load_habits(user_id: int) -> dict:
    if not os.path.exists(HABITS_FILE):
        return {}
    try:
        data = json.load(open(HABITS_FILE, "r", encoding="utf-8"))
        return data.get(str(user_id), {})
    except:
        return {}

def save_habits(user_id: int, habits: dict):
    data = {}
    if os.path.exists(HABITS_FILE):
        try:
            data = json.load(open(HABITS_FILE, "r", encoding="utf-8"))
        except:
            pass
    data[str(user_id)] = habits
    json.dump(data, open(HABITS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ══════════════════════════════════════
#  ДАЙДЖЕСТ
# ══════════════════════════════════════
def load_digest_settings() -> dict:
    if not os.path.exists(DIGEST_FILE):
        return {}
    try:
        return json.load(open(DIGEST_FILE, "r", encoding="utf-8"))
    except:
        return {}

def save_digest_settings(data: dict):
    json.dump(data, open(DIGEST_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ══════════════════════════════════════
#  НОТАТКИ# ══════════════════════════════════════
def load_refs() -> dict:
    if os.path.exists(REFS_FILE):
        try:
            return json.load(open(REFS_FILE, "r", encoding="utf-8"))
        except:
            pass
    return {}

def save_refs(refs: dict):
    json.dump(refs, open(REFS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def add_referral(inviter_id: int, new_user_id: int):
    refs = load_refs()
    key = str(inviter_id)
    if key not in refs:
        refs[key] = []
    if new_user_id not in refs[key]:
        refs[key].append(new_user_id)
        save_refs(refs)
        return True  # новий реферал
    return False

def get_ref_count(user_id: int) -> int:
    refs = load_refs()
    return len(refs.get(str(user_id), []))

def load_premium() -> dict:
    if os.path.exists(PREMIUM_FILE):
        try:
            return json.load(open(PREMIUM_FILE, "r", encoding="utf-8"))
        except:
            pass
    return {}

def save_premium(data: dict):
    json.dump(data, open(PREMIUM_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def is_premium(user_id: int) -> bool:
    data = load_premium()
    entry = data.get(str(user_id))
    if not entry:
        return False
    from datetime import datetime
    expires = datetime.fromisoformat(entry["expires"])
    return datetime.now() < expires

def grant_premium(user_id: int, days: int):
    data = load_premium()
    from datetime import datetime, timedelta
    key = str(user_id)
    # Якщо вже є преміум — продовжуємо
    if key in data:
        try:
            current = datetime.fromisoformat(data[key]["expires"])
            if current > datetime.now():
                expires = current + timedelta(days=days)
            else:
                expires = datetime.now() + timedelta(days=days)
        except:
            expires = datetime.now() + timedelta(days=days)
    else:
        expires = datetime.now() + timedelta(days=days)
    data[key] = {"expires": expires.isoformat()}
    save_premium(data)

def check_ref_rewards(user_id: int) -> str:
    """Перевіряє чи треба видати нагороду за рефералів"""
    count = get_ref_count(user_id)
    data = load_premium()
    key = str(user_id)
    rewarded = data.get(key, {}).get("ref_rewarded", 0)

    msg = ""
    if count >= 10 and rewarded < 10:
        grant_premium(user_id, 30)
        data = load_premium()
        data[key]["ref_rewarded"] = 10
        save_premium(data)
        msg = "🏆 10 друзів! Преміум на 30 днів активовано!"
    elif count >= 3 and rewarded < 3:
        grant_premium(user_id, 7)
        data = load_premium()
        data[key]["ref_rewarded"] = 3
        save_premium(data)
        msg = "🎉 3 друзі! Преміум на 7 днів активовано!"
    return msg

# ══════════════════════════════════════
#  ПАМ'ЯТЬ БОТА
# ══════════════════════════════════════
def load_memory(user_id: int) -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        data = json.load(open(MEMORY_FILE, "r", encoding="utf-8"))
        return data.get(str(user_id), {})
    except:
        return {}

def save_memory(user_id: int, mem: dict):
    data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            data = json.load(open(MEMORY_FILE, "r", encoding="utf-8"))
        except:
            pass
    data[str(user_id)] = mem
    json.dump(data, open(MEMORY_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def memory_to_text(mem: dict) -> str:
    """Перетворює словник пам'яті в текст для системного промпту"""
    if not mem:
        return ""
    lines = []
    if mem.get("name"):
        lines.append(f"Ім'я користувача: {mem['name']}")
    if mem.get("city"):
        lines.append(f"Місто: {mem['city']}")
    if mem.get("age"):
        lines.append(f"Вік: {mem['age']}")
    if mem.get("occupation"):
        lines.append(f"Робота/навчання: {mem['occupation']}")
    if mem.get("interests"):
        lines.append(f"Інтереси: {', '.join(mem['interests'])}")
    if mem.get("facts"):
        lines.append(f"Відомі факти: {'; '.join(mem['facts'][-5:])}")
    return "\n".join(lines)

def extract_and_update_memory(user_id: int, user_message: str, ai_reply: str):
    """Витягує факти з розмови і оновлює пам'ять асинхронно"""
    import threading
    def _extract():
        try:
            mem = load_memory(user_id)
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            prompt = (
                f"З цього повідомлення користувача витягни факти про нього для запам'ятовування.\n"
                f"Повідомлення: \"{user_message}\"\n\n"
                f"Поточна пам'ять: {json.dumps(mem, ensure_ascii=False)}\n\n"
                f"Поверни JSON з полями (тільки якщо є нова інформація, інакше поверни {{}}): "
                f"name (ім'я), city (місто), age (вік як число), occupation (робота/навчання), "
                f"interests (список інтересів), facts (список коротких фактів).\n"
                f"Відповідай ТІЛЬКИ валідним JSON без пояснень."
            )
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300, "temperature": 0
            }
            r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
            raw = r.json()["choices"][0]["message"]["content"].strip()
            # Витягуємо JSON з відповіді
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                new_data = json.loads(raw[start:end])
                if new_data:
                    # Мержимо з існуючою пам'яттю
                    for key in ["name", "city", "age", "occupation"]:
                        if new_data.get(key):
                            mem[key] = new_data[key]
                    # Списки — додаємо нові елементи
                    for key in ["interests", "facts"]:
                        if new_data.get(key):
                            existing = mem.get(key, [])
                            for item in new_data[key]:
                                if item not in existing:
                                    existing.append(item)
                            mem[key] = existing[-10:]  # зберігаємо останні 10
                    save_memory(user_id, mem)
        except:
            pass
    threading.Thread(target=_extract, daemon=True).start()

async def password_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = 16
    if context.args:
        try:
            length = max(8, min(32, int(context.args[0])))
        except:
            pass
    pwd = generate_password(length)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Новий пароль", callback_data=f"pwd|{length}")
    ]])
    await update.message.reply_text(
        f"🔐 *Безпечний пароль:*\n\n`{pwd}`\n\n"
        f"Довжина: {length} символів\n"
        f"/password 20 — для пароля з 20 символів",
        parse_mode="Markdown", reply_markup=kb
    )

async def cheatsheet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        topic = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "cheatsheet"
        await update.message.reply_text("📋 Введи тему для шпаргалки:\nНаприклад: `Друга світова війна` або `Python основи`")
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = ask_ai(update.effective_user.id,
        f"Зроби коротку шпаргалку по темі '{topic}'. "
        f"Формат: ключові факти, дати, визначення — коротко і по суті. "
        f"Максимум 20 пунктів. Без зайвого тексту.")
    await update.message.reply_text(f"📋 Шпаргалка: {topic}\n\n{result}")

async def grammar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        text_to_check = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "grammar"
        await update.message.reply_text("✍️ Введи текст для перевірки граматики:")
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = ask_ai(update.effective_user.id,
        f"Перевір граматику і стиль цього тексту. "
        f"Спочатку покажи виправлений текст, потім список помилок які були. "
        f"Текст: {text_to_check}")
    await update.message.reply_text(f"✍️ Перевірка тексту:\n\n{result}")

async def post_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        topic = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "post"
        await update.message.reply_text(
            "📱 Для якої платформи і на яку тему?\n"
            "Наприклад: `TikTok про мого кота` або `Instagram мотивація`"
        )
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("TikTok", callback_data=f"post|tiktok|{topic[:100]}"),
         InlineKeyboardButton("Instagram", callback_data=f"post|instagram|{topic[:100]}")],
        [InlineKeyboardButton("Twitter/X", callback_data=f"post|twitter|{topic[:100]}"),
         InlineKeyboardButton("Facebook", callback_data=f"post|facebook|{topic[:100]}")],
    ])
    await update.message.reply_text("📱 Обери платформу:", reply_markup=kb)

async def post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Генерую пост...")
    _, platform, topic = q.data.split("|", 2)
    result = ask_ai(q.from_user.id,
        f"Напиши готовий пост для {platform} на тему '{topic}'. "
        f"Включи: чіпляючий початок, основний текст, заклик до дії, хештеги. "
        f"Стиль молодіжний і живий.")
    await q.edit_message_text(f"📱 Пост для {platform}:\n\n{result}")

async def idea_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        niche = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "idea"
        await update.message.reply_text(
            "💡 В якій сфері шукаєш ідею?\n"
            "Наприклад: `онлайн`, `для школяра`, `з мінімальними вкладеннями`"
        )
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = ask_ai(update.effective_user.id,
        f"Згенеруй 5 конкретних бізнес-ідей для заробітку в сфері '{niche}'. "
        f"Для кожної: назва, суть, як почати, скільки можна заробити. "
        f"Реальні ідеї які можна почати зараз.")
    await update.message.reply_text(f"💡 Бізнес-ідеї: {niche}\n\n{result}")

async def mood_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        text = " ".join(context.args)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text(f"🎭 *Аналіз настрою:*\n\n{analyze_mood(text)}", parse_mode="Markdown")
    else:
        user_state[update.effective_user.id] = "mood"
        await update.message.reply_text("🎭 Введи текст для аналізу настрою:")

async def convert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) >= 3:
        try:
            val = float(context.args[0])
            await update.message.reply_text(
                convert_units(val, context.args[1], context.args[2]),
                parse_mode="Markdown"
            )
        except:
            await update.message.reply_text("❌ Формат: /convert 100 km mi")
    else:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("km → mi", callback_data="conv|1|km|mi"),
             InlineKeyboardButton("mi → km", callback_data="conv|1|mi|km")],
            [InlineKeyboardButton("kg → lb", callback_data="conv|1|kg|lb"),
             InlineKeyboardButton("lb → kg", callback_data="conv|1|lb|kg")],
            [InlineKeyboardButton("°C → °F", callback_data="conv|100|c|f"),
             InlineKeyboardButton("°F → °C", callback_data="conv|212|f|c")],
            [InlineKeyboardButton("m → ft",  callback_data="conv|1|m|ft"),
             InlineKeyboardButton("cm → in", callback_data="conv|1|cm|in")],
        ])
        user_state[update.effective_user.id] = "convert"
        await update.message.reply_text(
            "📐 Конвертер одиниць\n\nОбери або введи: `100 km mi`",
            parse_mode="Markdown", reply_markup=kb
        )

async def pwd_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    length = int(q.data.split("|")[1])
    pwd = generate_password(length)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Новий пароль", callback_data=f"pwd|{length}")]])
    await q.edit_message_text(
        f"🔐 *Безпечний пароль:*\n\n`{pwd}`\n\nДовжина: {length} символів",
        parse_mode="Markdown", reply_markup=kb
    )

async def conv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, val, f, t = q.data.split("|")
    await q.edit_message_text(convert_units(float(val), f, t), parse_mode="Markdown")

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang|uk"),
         InlineKeyboardButton("🇬🇧 English",    callback_data="lang|en")],
        [InlineKeyboardButton("🇵🇱 Polski",      callback_data="lang|pl"),
         InlineKeyboardButton("🇩🇪 Deutsch",     callback_data="lang|de")],
        [InlineKeyboardButton("🇫🇷 Français",    callback_data="lang|fr")],
    ])
    await update.message.reply_text("🌐 Обери мову відповідей AI:", reply_markup=kb)

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("|")[1]
    user_lang[q.from_user.id] = lang
    names = {"uk": "🇺🇦 Українська", "en": "🇬🇧 English", "pl": "🇵🇱 Polski",
             "de": "🇩🇪 Deutsch", "fr": "🇫🇷 Français"}
    await q.edit_message_text(f"✅ Мову змінено на {names.get(lang, lang)}")

EXPENSES_FILE = "expenses_tg.json"
QUIZ_FILE     = "quiz_tg.json"

def load_expenses(user_id: int) -> list:
    if os.path.exists(EXPENSES_FILE):
        try:
            data = json.load(open(EXPENSES_FILE, "r", encoding="utf-8"))
            return data.get(str(user_id), [])
        except:
            pass
    return []

def save_expense(user_id: int, amount: float, category: str, note: str = ""):
    data = {}
    if os.path.exists(EXPENSES_FILE):
        try:
            data = json.load(open(EXPENSES_FILE, "r", encoding="utf-8"))
        except:
            pass
    key = str(user_id)
    if key not in data:
        data[key] = []
    data[key].append({
        "amount": amount, "category": category, "note": note,
        "date": datetime.now().strftime("%d.%m %H:%M")
    })
    json.dump(data, open(EXPENSES_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

async def expense_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        try:
            amount = float(context.args[0])
            category = context.args[1] if len(context.args) > 1 else "Інше"
            note = " ".join(context.args[2:]) if len(context.args) > 2 else ""
            save_expense(uid, amount, category, note)
            await update.message.reply_text(f"💸 Записано: {amount} грн — {category}")
        except:
            await update.message.reply_text("❌ Формат: /expense 150 Їжа кава")
    else:
        expenses = load_expenses(uid)
        if not expenses:
            await update.message.reply_text(
                "💰 Трекер витрат порожній.\n\nДодай витрату:\n`/expense 150 Їжа`\n`/expense 500 Транспорт`",
                parse_mode="Markdown"
            )
            return
        total = sum(e["amount"] for e in expenses)
        by_cat = {}
        for e in expenses:
            by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
        lines = [f"• {cat}: {amt:.0f} грн" for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1])]
        recent = [f"{e['date']} — {e['amount']} грн ({e['category']})" for e in expenses[-5:]]
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Очистити витрати", callback_data=f"exp_clear|{uid}")]])
        await update.message.reply_text(
            f"💰 Твої витрати:\n\n" + "\n".join(lines) +
            f"\n\n💵 Всього: {total:.0f} грн\n\n📋 Останні:\n" + "\n".join(recent),
            reply_markup=kb
        )

async def exp_clear_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("|")[1])
    if q.from_user.id != uid:
        return
    data = {}
    if os.path.exists(EXPENSES_FILE):
        try:
            data = json.load(open(EXPENSES_FILE, "r", encoding="utf-8"))
        except:
            pass
    data[str(uid)] = []
    json.dump(data, open(EXPENSES_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    await q.edit_message_text("🗑 Витрати очищено!")

QUIZ_QUESTIONS = [
    {"q": "Яка столиця України?", "a": ["Київ", "Харків", "Львів", "Одеса"], "correct": 0},
    {"q": "Скільки планет у Сонячній системі?", "a": ["7", "8", "9", "10"], "correct": 1},
    {"q": "Хто написав 'Кобзар'?", "a": ["Франко", "Шевченко", "Леся Українка", "Котляревський"], "correct": 1},
    {"q": "Яка найбільша країна у світі?", "a": ["США", "Китай", "Росія", "Канада"], "correct": 2},
    {"q": "Скільки байт в 1 кілобайті?", "a": ["512", "1000", "1024", "2048"], "correct": 2},
    {"q": "Який рік заснування Києва?", "a": ["482", "882", "1054", "1240"], "correct": 0},
    {"q": "Що означає HTML?", "a": ["High Text ML", "HyperText Markup Language", "Home Tool ML", "Hyper Transfer ML"], "correct": 1},
    {"q": "Яка формула води?", "a": ["H2O2", "HO2", "H2O", "H3O"], "correct": 2},
]

quiz_scores: dict[int, dict] = {}

async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    q_idx = random.randint(0, len(QUIZ_QUESTIONS)-1)
    quiz_scores[uid] = quiz_scores.get(uid, {"score": 0, "total": 0})
    quiz_scores[uid]["current"] = q_idx
    q = QUIZ_QUESTIONS[q_idx]
    buttons = [[InlineKeyboardButton(ans, callback_data=f"quiz|{q_idx}|{i}")]
               for i, ans in enumerate(q["a"])]
    score = quiz_scores[uid]
    await update.message.reply_text(
        f"🧠 Вікторина!\n\n{q['q']}\n\nРахунок: {score['score']}/{score['total']}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_obj = update.callback_query
    await q_obj.answer()
    _, q_idx, answer = q_obj.data.split("|")
    q_idx, answer = int(q_idx), int(answer)
    uid = q_obj.from_user.id
    question = QUIZ_QUESTIONS[q_idx]
    if uid not in quiz_scores:
        quiz_scores[uid] = {"score": 0, "total": 0}
    quiz_scores[uid]["total"] += 1
    if answer == question["correct"]:
        quiz_scores[uid]["score"] += 1
        result = f"✅ Правильно! +1 бал"
    else:
        result = f"❌ Неправильно! Правильна відповідь: {question['a'][question['correct']]}"
    score = quiz_scores[uid]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Наступне питання", callback_data="quiz_next")]])
    await q_obj.edit_message_text(
        f"{result}\n\nРахунок: {score['score']}/{score['total']}",
        reply_markup=kb
    )

async def compat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Гороскоп сумісності двох знаків"""
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("♈ Овен",    callback_data="compat1|овен"),
         InlineKeyboardButton("♉ Телець",  callback_data="compat1|телець"),
         InlineKeyboardButton("♊ Близнюки",callback_data="compat1|близнюки")],
        [InlineKeyboardButton("♋ Рак",     callback_data="compat1|рак"),
         InlineKeyboardButton("♌ Лев",     callback_data="compat1|лев"),
         InlineKeyboardButton("♍ Діва",    callback_data="compat1|діва")],
        [InlineKeyboardButton("♎ Терези",  callback_data="compat1|терези"),
         InlineKeyboardButton("♏ Скорпіон",callback_data="compat1|скорпіон"),
         InlineKeyboardButton("♐ Стрілець",callback_data="compat1|стрілець")],
        [InlineKeyboardButton("♑ Козеріг", callback_data="compat1|козеріг"),
         InlineKeyboardButton("♒ Водолій", callback_data="compat1|водолій"),
         InlineKeyboardButton("♓ Риби",    callback_data="compat1|риби")],
    ])
    await update.message.reply_text("💑 Обери свій знак зодіаку:", reply_markup=kb)

async def compat1_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    sign1 = q.data.split("|")[1]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("♈ Овен",    callback_data=f"compat2|{sign1}|овен"),
         InlineKeyboardButton("♉ Телець",  callback_data=f"compat2|{sign1}|телець"),
         InlineKeyboardButton("♊ Близнюки",callback_data=f"compat2|{sign1}|близнюки")],
        [InlineKeyboardButton("♋ Рак",     callback_data=f"compat2|{sign1}|рак"),
         InlineKeyboardButton("♌ Лев",     callback_data=f"compat2|{sign1}|лев"),
         InlineKeyboardButton("♍ Діва",    callback_data=f"compat2|{sign1}|діва")],
        [InlineKeyboardButton("♎ Терези",  callback_data=f"compat2|{sign1}|терези"),
         InlineKeyboardButton("♏ Скорпіон",callback_data=f"compat2|{sign1}|скорпіон"),
         InlineKeyboardButton("♐ Стрілець",callback_data=f"compat2|{sign1}|стрілець")],
        [InlineKeyboardButton("♑ Козеріг", callback_data=f"compat2|{sign1}|козеріг"),
         InlineKeyboardButton("♒ Водолій", callback_data=f"compat2|{sign1}|водолій"),
         InlineKeyboardButton("♓ Риби",    callback_data=f"compat2|{sign1}|риби")],
    ])
    await q.edit_message_text(f"Твій знак: {sign1}\nТепер обери знак партнера:", reply_markup=kb)

async def compat2_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Аналізую сумісність...")
    _, sign1, sign2 = q.data.split("|")
    result = ask_ai(q.from_user.id,
        f"Проаналізуй сумісність знаків зодіаку {sign1} і {sign2}. "
        f"Дай: відсоток сумісності, сильні сторони пари, слабкі сторони, загальний висновок. "
        f"Відповідь цікава і жива.")
    await q.edit_message_text(f"💑 Сумісність {sign1} + {sign2}\n\n{result}")

SCHEDULE_FILE = "schedule_tg.json"

def load_schedule(user_id: int) -> dict:
    if os.path.exists(SCHEDULE_FILE):
        try:
            data = json.load(open(SCHEDULE_FILE, "r", encoding="utf-8"))
            return data.get(str(user_id), {})
        except:
            pass
    return {}

def save_schedule(user_id: int, schedule: dict):
    data = {}
    if os.path.exists(SCHEDULE_FILE):
        try:
            data = json.load(open(SCHEDULE_FILE, "r", encoding="utf-8"))
        except:
            pass
    data[str(user_id)] = schedule
    json.dump(data, open(SCHEDULE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    schedule = load_schedule(uid)
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    if not schedule:
        await update.message.reply_text(
            "📅 Розклад порожній.\n\n"
            "Додай урок командою:\n"
            "`/schedule_add Пн 08:00 Математика`\n\n"
            "Або напиши весь розклад:\n"
            "`/schedule_set Пн: Математика 08:00, Фізика 09:45`",
            parse_mode="Markdown"
        )
        return
    lines = []
    for day in days:
        if day in schedule:
            lessons = schedule[day]
            lines.append(f"*{day}:*\n" + "\n".join(f"  {l}" for l in lessons))
    await update.message.reply_text("📅 Твій розклад:\n\n" + "\n\n".join(lines), parse_mode="Markdown")

async def schedule_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) >= 3:
        day = context.args[0]
        time = context.args[1]
        subject = " ".join(context.args[2:])
        uid = update.effective_user.id
        schedule = load_schedule(uid)
        if day not in schedule:
            schedule[day] = []
        schedule[day].append(f"{time} — {subject}")
        schedule[day].sort()
        save_schedule(uid, schedule)
        await update.message.reply_text(f"✅ Додано: {day} {time} — {subject}")
    else:
        await update.message.reply_text("❌ Формат: /schedule_add Пн 08:00 Математика")

async def pomodoro_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🍅 25 хв роботи",   callback_data="pomo|25|5"),
         InlineKeyboardButton("⚡ 50 хв роботи",   callback_data="pomo|50|10")],
        [InlineKeyboardButton("🎯 90 хв роботи",   callback_data="pomo|90|20")],
    ])
    await update.message.reply_text(
        "🍅 *Таймер Помодоро*\n\n"
        "Обери режим роботи:\n"
        "Після закінчення отримаєш нагадування!",
        parse_mode="Markdown", reply_markup=kb
    )

async def pomo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, work, rest = q.data.split("|")
    work, rest = int(work), int(rest)
    chat_id = q.from_user.id
    await q.edit_message_text(
        f"🍅 Таймер запущено!\n\n"
        f"⏱ Працюй {work} хвилин\n"
        f"Нагадаю коли час відпочити!"
    )
    async def _pomo():
        await asyncio.sleep(work * 60)
        await context.bot.send_message(chat_id=chat_id,
            text=f"🍅 Час вийшов! Відпочинь {rest} хвилин 😌\n/pomodoro — запустити знову")
    asyncio.create_task(_pomo())

async def nickname_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        style = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "nickname"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Ігровий",    callback_data="nick|gaming"),
             InlineKeyboardButton("😎 Крутий",     callback_data="nick|cool")],
            [InlineKeyboardButton("🌙 Містичний",  callback_data="nick|mystic"),
             InlineKeyboardButton("😂 Смішний",    callback_data="nick|funny")],
            [InlineKeyboardButton("💪 Сильний",    callback_data="nick|strong"),
             InlineKeyboardButton("🌸 Милий",      callback_data="nick|cute")],
        ])
        await update.message.reply_text("🎮 Обери стиль нікнейму:", reply_markup=kb)
        return

async def nick_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Генерую...")
    style = q.data.split("|")[1]
    styles = {
        "gaming": "крутий ігровий нікнейм для стрілялок/RPG",
        "cool": "стильний і крутий нікнейм для соцмереж",
        "mystic": "містичний і таємничий нікнейм",
        "funny": "смішний і мемний нікнейм",
        "strong": "сильний і потужний нікнейм",
        "cute": "милий і позитивний нікнейм",
    }
    result = ask_ai(q.from_user.id,
        f"Згенеруй 10 унікальних нікнеймів у стилі '{styles.get(style, style)}'. "
        f"Тільки список нікнеймів, без пояснень. Кожен з нового рядка.")
    await q.edit_message_text(f"🎮 Нікнейми ({style}):\n\n{result}")

async def checksite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        url = context.args[0]
        if not url.startswith("http"):
            url = "https://" + url
        try:
            r = requests.get(url, timeout=8)
            status = r.status_code
            if status == 200:
                await update.message.reply_text(f"✅ Сайт {url} працює! (код {status})")
            else:
                await update.message.reply_text(f"⚠️ Сайт відповідає з кодом {status}")
        except:
            await update.message.reply_text(f"❌ Сайт {url} недоступний або не існує")
    else:
        user_state[update.effective_user.id] = "checksite"
        await update.message.reply_text("🌐 Введи адресу сайту:\nНаприклад: `google.com`", parse_mode="Markdown")

async def diary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        text = " ".join(context.args)
        save_diary_entry(uid, text)
        await update.message.reply_text("Запис збережено в щоденник.")
        return
    entries = load_diary(uid)
    if not entries:
        user_state[uid] = "diary"
        await update.message.reply_text(
            "Щоденник порожній.\n\nНапиши як пройшов твій день — я збережу:"
        )
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Новий запис", callback_data="diary|new"),
         InlineKeyboardButton("Переглянути", callback_data="diary|view"),
         InlineKeyboardButton("Аналіз", callback_data="diary|analyze")],
    ])
    last = entries[-1]
    await update.message.reply_text(
        f"Щоденник: {len(entries)} записів\nОстанній: {last['date']}\n\n{last['text'][:200]}...",
        reply_markup=kb
    )

async def diary_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    action = q.data.split("|")[1]
    if action == "new":
        user_state[uid] = "diary"
        await q.edit_message_text("Напиши що хочеш записати в щоденник:")
    elif action == "view":
        entries = load_diary(uid)
        lines = [f"{e['date']}: {e['text'][:100]}" for e in entries[-10:]]
        await q.edit_message_text("Останні 10 записів:\n\n" + "\n\n".join(lines))
    elif action == "analyze":
        entries = load_diary(uid)
        if not entries:
            await q.edit_message_text("Немає записів для аналізу.")
            return
        combined = "\n".join(f"{e['date']}: {e['text']}" for e in entries[-20:])
        await q.edit_message_text("Аналізую щоденник...")
        result = ask_ai(uid, f"Проаналізуй ці записи щоденника і дай інсайти: настрій, патерни, поради:\n\n{combined[:3000]}")
        await context.bot.send_message(chat_id=uid, text=result)

async def habits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    habits = load_habits(uid)
    today = datetime.now().strftime("%Y-%m-%d")
    if not habits:
        user_state[uid] = "habits_add"
        await update.message.reply_text(
            "Трекер звичок порожній.\n\nНапиши назву звички яку хочеш відстежувати:\nНаприклад: спорт, вода, читання"
        )
        return
    lines = ["Твої звички на сьогодні:\n"]
    kb_buttons = []
    for name, data in habits.items():
        done_today = today in data.get("done_dates", [])
        streak = data.get("streak", 0)
        status = "✅" if done_today else "⬜"
        lines.append(f"{status} {name} — серія: {streak} днів")
        if not done_today:
            kb_buttons.append([InlineKeyboardButton(f"✅ {name}", callback_data=f"habit|done|{name}")])
    kb_buttons.append([InlineKeyboardButton("➕ Нова звичка", callback_data="habit|add")])
    kb_buttons.append([InlineKeyboardButton("🗑 Видалити", callback_data="habit|delete")])
    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(kb_buttons)
    )

async def habits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    parts = q.data.split("|")
    action = parts[1]
    if action == "done":
        habit_name = parts[2]
        habits = load_habits(uid)
        today = datetime.now().strftime("%Y-%m-%d")
        if habit_name in habits:
            done_dates = habits[habit_name].get("done_dates", [])
            if today not in done_dates:
                done_dates.append(today)
                # Рахуємо серію
                streak = 0
                check_date = datetime.now()
                while check_date.strftime("%Y-%m-%d") in done_dates:
                    streak += 1
                    check_date = check_date.replace(day=check_date.day - 1)
                habits[habit_name]["done_dates"] = done_dates[-60:]
                habits[habit_name]["streak"] = streak
                save_habits(uid, habits)
                await q.edit_message_text(f"✅ {habit_name} виконано! Серія: {streak} днів")
            else:
                await q.answer("Вже відмічено сьогодні!")
    elif action == "add":
        user_state[uid] = "habits_add"
        await q.edit_message_text("Напиши назву нової звички:")
    elif action == "delete":
        habits = load_habits(uid)
        if habits:
            user_state[uid] = "habits_delete"
            names = ", ".join(habits.keys())
            await q.edit_message_text(f"Яку звичку видалити?\n{names}")

async def digest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_premium(uid) and uid != ADMIN_ID:
        await update.message.reply_text(
            "Щоденний дайджест доступний тільки для Преміум.\n\n"
            "Купи Преміум: /premium\nАбо запроси 3 друзів: /ref"
        )
        return
    settings = load_digest_settings()
    user_settings = settings.get(str(uid), {})
    if user_settings.get("enabled"):
        hour = user_settings.get("hour", 8)
        city = user_settings.get("city", "Київ")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Вимкнути", callback_data="digest|off"),
             InlineKeyboardButton("Змінити час", callback_data="digest|time"),
             InlineKeyboardButton("Змінити місто", callback_data="digest|city")],
        ])
        await update.message.reply_text(
            f"Дайджест увімкнено: щодня о {hour}:00, місто: {city}",
            reply_markup=kb
        )
    else:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("7:00", callback_data="digest|set|7"),
             InlineKeyboardButton("8:00", callback_data="digest|set|8"),
             InlineKeyboardButton("9:00", callback_data="digest|set|9")],
        ])
        await update.message.reply_text(
            "Щоденний дайджест — кожен ранок отримуєш:\n"
            "- Погода в твоєму місті\n"
            "- Топ новини\n"
            "- Мотивація на день\n\n"
            "О котрій надсилати?",
            reply_markup=kb
        )

async def digest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    parts = q.data.split("|")
    action = parts[1]
    settings = load_digest_settings()
    key = str(uid)
    if action == "set":
        hour = int(parts[2])
        settings[key] = {"enabled": True, "hour": hour, "city": "Київ"}
        save_digest_settings(settings)
        user_state[uid] = "digest_city"
        await q.edit_message_text(f"Дайджест о {hour}:00. Тепер напиши своє місто:")
    elif action == "off":
        if key in settings:
            settings[key]["enabled"] = False
            save_digest_settings(settings)
        await q.edit_message_text("Дайджест вимкнено.")
    elif action == "time":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("7:00", callback_data="digest|set|7"),
             InlineKeyboardButton("8:00", callback_data="digest|set|8"),
             InlineKeyboardButton("9:00", callback_data="digest|set|9"),
             InlineKeyboardButton("10:00", callback_data="digest|set|10")],
        ])
        await q.edit_message_text("Обери новий час:", reply_markup=kb)
    elif action == "city":
        user_state[uid] = "digest_city"
        await q.edit_message_text("Напиши своє місто:")

async def cv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = "cv"
    await update.message.reply_text(
        "Генератор резюме/CV.\n\n"
        "Напиши про себе у вільній формі:\n"
        "- Ім'я і вік\n"
        "- Досвід роботи\n"
        "- Навички\n"
        "- Освіта\n"
        "- Що шукаєш\n\n"
        "Я зроблю готове резюме:"
    )

async def comic_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерує комікс-стиль картинки з текстом як у TikTok"""
    uid = update.effective_user.id
    if context.args:
        topic = " ".join(context.args)
    else:
        user_state[uid] = "comic"
        await update.message.reply_text(
            "Напиши тему для комікс-картинок.\n\n"
            "Наприклад:\n"
            "- будуй бізнес\n"
            "- займайся спортом\n"
            "- вчися кожен день\n\n"
            "Я згенерую 3 картинки в стилі мотиваційного коміксу:"
        )
        return
    await _generate_comic(update, uid, topic)

async def _generate_comic(update, uid: int, topic: str):
    """Генерує серію мотиваційних картинок з текстом"""
    import urllib.parse

    # AI придумує пари (дія + "Нікому не говори" або інший підпис)
    pairs_raw = ask_ai(uid,
        f"Придумай 3 пари коротких мотиваційних написів українською на тему '{topic}'. "
        f"Формат: кожна пара на новому рядку через | "
        f"Наприклад: Будуй бізнес | Нікому не говори\n"
        f"Тільки 3 рядки, нічого більше."
    )
    pairs = []
    for line in pairs_raw.strip().split("\n"):
        if "|" in line:
            parts = line.split("|", 1)
            pairs.append((parts[0].strip(), parts[1].strip()))

    if not pairs:
        pairs = [(topic, "Нікому не говори")]

    # Генеруємо картинки
    bg_styles = [
        f"anime style man in black suit {topic} city night cinematic",
        f"anime character working studying {topic} dramatic lighting",
        f"motivational scene {topic} urban background night",
    ]

    for i, (text1, text2) in enumerate(pairs[:3]):
        try:
            prompt = bg_styles[i % len(bg_styles)]
            from PIL import Image, ImageDraw, ImageFont
            import io as _io

            bg_url = generate_image(prompt)
            r_bg = requests.get(bg_url, timeout=20)
            if r_bg.status_code != 200:
                continue
            img = Image.open(_io.BytesIO(r_bg.content)).convert("RGB")
            img = img.resize((1080, 1080))

            # Розбиваємо на 2 частини вертикально
            top = img.crop((0, 0, 1080, 540))
            bottom = img.crop((0, 540, 1080, 1080))

            # Темний оверлей
            from PIL import ImageEnhance
            top = ImageEnhance.Brightness(top).enhance(0.6)
            bottom = ImageEnhance.Brightness(bottom).enhance(0.6)

            result = Image.new("RGB", (1080, 1080))
            result.paste(top, (0, 0))
            result.paste(bottom, (0, 540))

            draw = ImageDraw.Draw(result)

            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
            except:
                font = ImageFont.load_default()

            # Текст на верхній частині
            draw.text((42, 452), text1, font=font, fill=(0, 0, 0))
            draw.text((40, 450), text1, font=font, fill=(255, 255, 255))

            # Текст на нижній частині
            draw.text((42, 992), text2, font=font, fill=(0, 0, 0))
            draw.text((40, 990), text2, font=font, fill=(255, 255, 255))

            # Лінія між частинами
            draw.rectangle([(0, 538), (1080, 542)], fill=(255, 255, 255))

            buf = _io.BytesIO()
            result.save(buf, format="JPEG", quality=92)
            buf.seek(0)

            await update.message.reply_photo(photo=buf)
        except Exception as e:
            # Запасний варіант — просто картинка без тексту
            try:
                import urllib.parse as _up
                p = _up.quote(f"motivational {topic} cinematic")
                url = f"https://image.pollinations.ai/prompt/{p}?width=1080&height=1080&nologo=true"
                await update.message.reply_photo(photo=url, caption=f"{text1} | {text2}")
            except:
                pass

async def quote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        text = " ".join(context.args)
        # Парсимо: "цитата | автор" або просто цитата
        if "|" in text:
            parts = text.split("|", 1)
            quote = parts[0].strip()
            author = parts[1].strip()
        else:
            quote = text.strip()
            author = ""
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        await update.message.reply_text("Добре, генерую картинку з цитатою. Зачекай ~15 секунд.")
        try:
            buf = generate_quote_image(quote, author)
            await update.message.reply_photo(photo=buf, caption=f'"{quote}"\n{("— " + author) if author else ""}')
        except Exception as e:
            await update.message.reply_text(f"❌ Помилка: {e}")
    else:
        user_state[uid] = "quote"
        await update.message.reply_text(
            "Напиши цитату для картинки.\n\n"
            "Формат: просто текст\n"
            "Або з автором: Ніколи не здавайся | Черчілль\n\n"
            "Або напиши 'авто' — я сам придумаю мотиваційну цитату:"
        )

async def url_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        url = context.args[0]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        text = fetch_url_text(url)
        if text.startswith("ERROR:"):
            await update.message.reply_text(f"❌ Не вдалося відкрити: {text[6:]}")
            return
        result = ask_ai(uid, f"Прочитай цей текст зі сторінки і зроби короткий переказ суті (5-7 речень). Що головне на цій сторінці?\n\n{text}")
        parts = split_long_message(result)
        for i, part in enumerate(parts):
            prefix = f"[{i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
            await update.message.reply_text(f"🔗 Аналіз сторінки:\n\n{prefix}{part}")
    else:
        user_state[uid] = "url"
        await update.message.reply_text("🔗 Надішли посилання на сторінку — я прочитаю і перекажу суть:")

async def debate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        topic = " ".join(context.args)
        user_state[uid] = f"debate_{topic}"
        result = ask_ai_deep(uid,
            f"Ти граєш роль опонента в дебатах. Тема: '{topic}'.\n"
            f"Займи ПРОТИЛЕЖНУ позицію до загальноприйнятої і аргументуй її переконливо. "
            f"Потім запитай мою думку."
        )
        await update.message.reply_text(f"🎭 Режим дебатів: {topic}\n\n{result}")
    else:
        user_state[uid] = "debate"
        await update.message.reply_text(
            "🎭 Режим дебатів!\n\n"
            "Я займу протилежну позицію і буду сперечатись з тобою.\n"
            "Назви тему для дебатів:"
        )

async def youtube_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        url = context.args[0]
        await _summarize_youtube(update, uid, url, context)
    else:
        user_state[uid] = "youtube"
        await update.message.reply_text(
            "Вставте посилання на YouTube відео — я перекажу зміст:"
        )

async def _summarize_youtube(update, uid: int, url: str, context=None):
    import re as _re
    if context:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    vid_match = _re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if not vid_match:
        await update.message.reply_text("Не вдалося знайти відео. Перевір посилання.")
        return
    vid_id = vid_match.group(1)
    try:
        r = requests.get(
            f"https://www.youtube.com/watch?v={vid_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        import re as _re2
        title_match = _re2.search(r'"title":"([^"]+)"', r.text)
        title = title_match.group(1) if title_match else "YouTube відео"
        # Витягуємо опис відео
        desc_match = _re2.search(r'"shortDescription":"([^"]{0,500})"', r.text)
        desc = desc_match.group(1).replace('\\n', ' ') if desc_match else ""
        result = ask_ai(uid,
            f"Перекажи зміст YouTube відео.\n"
            f"Назва: '{title}'\n"
            f"Опис: '{desc}'\n"
            f"Дай короткий переказ про що це відео (3-5 речень). Без зайвих слів."
        )
        await update.message.reply_text(f"YouTube: {title}\n\n{result}")
    except Exception as e:
        await update.message.reply_text(f"Не вдалося отримати інформацію: {e}")

async def calories_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        food = " ".join(context.args)
        await _track_calories(update, uid, food)
    else:
        user_state[uid] = "calories_add"
        await update.message.reply_text(
            "Що ти їв? Напиши назву страви або продукту:\n"
            "Наприклад: борщ 300г, або просто 'яблуко'"
        )

async def _track_calories(update, uid: int, food: str):
    result = ask_ai(uid,
        f"Визнач калорії для: '{food}'. "
        f"Відповідь у форматі: Назва — X ккал (білки Xг, жири Xг, вуглеводи Xг). "
        f"Тільки один рядок."
    )
    # Зберігаємо в файл
    cal_file = f"calories_{uid}.json"
    data = []
    if os.path.exists(cal_file):
        try:
            data = json.load(open(cal_file, encoding='utf-8'))
        except:
            pass
    today = datetime.now().strftime("%Y-%m-%d")
    data.append({"date": today, "food": food, "info": result})
    json.dump(data, open(cal_file, 'w', encoding='utf-8'), ensure_ascii=False)
    # Рахуємо за сьогодні
    today_items = [d for d in data if d.get("date") == today]
    await update.message.reply_text(
        f"{result}\n\nЗаписано. Сьогодні записів: {len(today_items)}\n"
        f"Напиши /calories_today щоб побачити все за день."
    )

async def calories_today_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cal_file = f"calories_{uid}.json"
    if not os.path.exists(cal_file):
        await update.message.reply_text("Ще нічого не записано. Напиши /calories їжа")
        return
    data = json.load(open(cal_file, encoding='utf-8'))
    today = datetime.now().strftime("%Y-%m-%d")
    today_items = [d for d in data if d.get("date") == today]
    if not today_items:
        await update.message.reply_text("Сьогодні ще нічого не записано.")
        return
    lines = [f"Трекер калорій за {today}:\n"]
    for i, item in enumerate(today_items, 1):
        lines.append(f"{i}. {item['info']}")
    await update.message.reply_text("\n".join(lines))

async def tiktok_post_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        topic = " ".join(context.args)
        await _generate_tiktok_post(update, uid, topic)
    else:
        user_state[uid] = "tiktok_post"
        await update.message.reply_text(
            "На яку тему зробити пост для TikTok/Instagram?\n"
            "Наприклад: мотивація, бізнес, спорт, їжа"
        )

async def _generate_tiktok_post(update, uid: int, topic: str):
    result = ask_ai(uid,
        f"Створи вірусний пост для TikTok/Instagram на тему '{topic}'.\n"
        f"Структура:\n"
        f"1. Чіпляючий заголовок (1 рядок)\n"
        f"2. Текст поста (3-5 речень)\n"
        f"3. Заклик до дії\n"
        f"4. 10 хештегів\n"
        f"Без зірочок і Markdown."
    )
    await update.message.reply_text(result)

async def mbti_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = "mbti_1"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Інтроверт (I)", callback_data="mbti|I"),
         InlineKeyboardButton("Екстраверт (E)", callback_data="mbti|E")],
    ])
    await update.message.reply_text(
        "Тест на тип особистості!\n\n"
        "Питання 1/4: Як ти відновлюєш енергію?",
        reply_markup=kb
    )

async def mbti_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data.split("|")[1]
    state = user_state.get(uid, "")
    if not state.startswith("mbti"):
        return
    # Зберігаємо відповіді
    answers = context.user_data.get("mbti_answers", "")
    answers += data
    context.user_data["mbti_answers"] = answers
    step = len(answers)
    if step == 1:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Факти і деталі (S)", callback_data="mbti|S"),
             InlineKeyboardButton("Ідеї і можливості (N)", callback_data="mbti|N")],
        ])
        await q.edit_message_text("Питання 2/4: На що ти більше звертаєш увагу?", reply_markup=kb)
    elif step == 2:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Логіка (T)", callback_data="mbti|T"),
             InlineKeyboardButton("Почуття (F)", callback_data="mbti|F")],
        ])
        await q.edit_message_text("Питання 3/4: Як ти приймаєш рішення?", reply_markup=kb)
    elif step == 3:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Планую заздалегідь (J)", callback_data="mbti|J"),
             InlineKeyboardButton("Дію за ситуацією (P)", callback_data="mbti|P")],
        ])
        await q.edit_message_text("Питання 4/4: Як ти організовуєш своє життя?", reply_markup=kb)
    elif step == 4:
        mbti_type = answers
        context.user_data["mbti_answers"] = ""
        user_state.pop(uid, None)
        result = ask_ai(uid,
            f"Опиши тип особистості MBTI: {mbti_type}. "
            f"Включи: назву типу, сильні сторони, слабкі сторони, підходящі професії, "
            f"відомі люди з цим типом. Без зірочок."
        )
        await q.edit_message_text(f"Твій тип: {mbti_type}\n\n{result}")

async def teach_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        topic = " ".join(context.args)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid,
            f"Поясни тему '{topic}' максимально просто, як для 10-річної дитини. "
            f"Використовуй прості слова, аналогії з реального життя, приклади. "
            f"Структура: 1) Що це таке (1-2 речення) 2) Як це працює (простий приклад) "
            f"3) Навіщо це потрібно. Без зірочок."
        )
        parts = split_long_message(result)
        for i, part in enumerate(parts):
            await update.message.reply_text(f"[{i+1}/{len(parts)}]\n\n{part}" if len(parts) > 1 else part)
    else:
        user_state[uid] = "teach"
        await update.message.reply_text(
            "Режим вчителя — поясню будь-яку тему простими словами.\n\n"
            "Що пояснити? Наприклад: квантова фізика, блокчейн, ШІ, фотосинтез"
        )

async def ad_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Адмін: налаштування реклами"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Немає доступу.")
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Надіслати рекламу зараз", callback_data="ad|send")],
        [InlineKeyboardButton("Встановити авторекламу", callback_data="ad|auto")],
    ])
    await update.message.reply_text(
        "Рекламна панель:\n\n"
        "Реклама надсилається всім юзерам раз на день.",
        reply_markup=kb
    )

async def ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    action = q.data.split("|")[1]
    if action == "send":
        user_state[q.from_user.id] = "ad_text"
        await q.edit_message_text(
            "Напиши рекламний текст (можна з посиланням).\n"
            "Він буде надісланий всім юзерам:"
        )
    elif action == "auto":
        user_state[q.from_user.id] = "ad_auto"
        await q.edit_message_text(
            "Напиши рекламний текст для щоденної авторозсилки.\n"
            "Буде надсилатись раз на день о 12:00:"
        )

async def realtime_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Немає доступу.")
        return
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour_ago = now.replace(minute=0, second=0).strftime("%Y-%m-%d %H:")
    users = {}
    if os.path.exists(USERS_FILE):
        try:
            users = json.load(open(USERS_FILE, encoding='utf-8'))
        except:
            pass
    msg_today = 0
    msg_hour = 0
    active_today = set()
    if os.path.exists(DIALOG_FILE):
        try:
            history = json.load(open(DIALOG_FILE, encoding='utf-8'))
            for e in history:
                if e.get("role") == "user":
                    d = e.get("date", "")
                    if d.startswith(today):
                        msg_today += 1
                        active_today.add(e.get("user_id"))
                    if d.startswith(hour_ago):
                        msg_hour += 1
        except:
            pass
    premium_count = sum(1 for uid in users if is_premium(int(uid)))
    await update.message.reply_text(
        f"Статистика в реальному часі:\n\n"
        f"Всього юзерів: {len(users)}\n"
        f"Преміум: {premium_count}\n"
        f"Активних сьогодні: {len(active_today)}\n"
        f"Повідомлень сьогодні: {msg_today}\n"
        f"Повідомлень за останню годину: {msg_hour}\n"
        f"Активних сесій зараз: {len(user_histories)}"
    )

async def persona_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ілон Маск", callback_data="persona|Elon Musk"),
         InlineKeyboardButton("Стів Джобс", callback_data="persona|Steve Jobs")],
        [InlineKeyboardButton("Альберт Ейнштейн", callback_data="persona|Albert Einstein"),
         InlineKeyboardButton("Наполеон", callback_data="persona|Napoleon Bonaparte")],
        [InlineKeyboardButton("Шевченко", callback_data="persona|Taras Shevchenko"),
         InlineKeyboardButton("Зеленський", callback_data="persona|Volodymyr Zelensky")],
        [InlineKeyboardButton("Вийти з режиму", callback_data="persona|exit")],
    ])
    await update.message.reply_text(
        "Обери з ким поговорити — я буду відповідати від їх імені:",
        reply_markup=kb
    )

async def persona_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    person = q.data.split("|")[1]
    if person == "exit":
        user_state.pop(uid, None)
        await q.edit_message_text("Вийшов з режиму персонажа.")
        return
    user_state[uid] = f"persona_{person}"
    await q.edit_message_text(
        f"Тепер я відповідаю як {person}.\n"
        f"Запитай мене про що завгодно!\n\n"
        f"Напиши /persona щоб змінити персонажа."
    )

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    refs = load_refs()
    if not refs:
        await update.message.reply_text("Поки що ніхто нікого не запросив.")
        return
    users = {}
    if os.path.exists(USERS_FILE):
        try:
            users = json.load(open(USERS_FILE, "r", encoding="utf-8"))
        except:
            pass
    sorted_refs = sorted(refs.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    lines = ["Топ запрошувачів:\n"]
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    for i, (uid_str, invited) in enumerate(sorted_refs):
        u = users.get(uid_str, {})
        name = u.get("name", f"User {uid_str}")
        count = len(invited)
        prem = "⭐" if is_premium(int(uid_str)) else ""
        lines.append(f"{medals[i]} {name}{prem} — {count} друзів")
    uid = update.effective_user.id
    my_count = get_ref_count(uid)
    lines.append(f"\nТвоя позиція: {my_count} запрошених")
    if my_count < 3:
        lines.append(f"До преміуму: ще {3 - my_count} друзів")
    await update.message.reply_text("\n".join(lines))

async def deep_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        task = " ".join(context.args)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text("🧠 Глибокий аналіз... це може зайняти до 30 секунд.")
        result = ask_ai_deep(uid, task)
        parts = split_long_message(result)
        for i, part in enumerate(parts):
            if len(parts) > 1:
                await update.message.reply_text(f"[{i+1}/{len(parts)}]\n\n{part}")
            else:
                await update.message.reply_text(part)
    else:
        user_state[uid] = "deep"
        await update.message.reply_text(
            "🧠 Режим глибокого аналізу.\n\n"
            "Опиши задачу детально — я розберу її крок за кроком і дам вичерпну відповідь.\n\n"
            "Підходить для: складних питань, великих кодів, бізнес-планів, аналізу, рефератів."
        )

async def code_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        # /code python зроби парсер сайту
        task = " ".join(context.args)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid,
            f"Ти — досвідчений програміст. Напиши код: {task}\n"
            f"Поясни коротко що робить код і як запустити."
        )
        await update.message.reply_text(result)
    else:
        user_state[uid] = "code"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Python",     callback_data="code|Python"),
             InlineKeyboardButton("JavaScript", callback_data="code|JavaScript")],
            [InlineKeyboardButton("HTML/CSS",   callback_data="code|HTML/CSS"),
             InlineKeyboardButton("SQL",        callback_data="code|SQL")],
            [InlineKeyboardButton("TypeScript", callback_data="code|TypeScript"),
             InlineKeyboardButton("Bash",       callback_data="code|Bash")],
            [InlineKeyboardButton("Java",       callback_data="code|Java"),
             InlineKeyboardButton("C#",         callback_data="code|C#")],
            [InlineKeyboardButton("Будь-яка",   callback_data="code|будь-якою мовою")],
        ])
        await update.message.reply_text(
            "💻 Обери мову програмування або просто опиши задачу:",
            reply_markup=kb
        )

async def code_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("|", 1)[1]
    uid = query.from_user.id
    user_state[uid] = f"code_{lang}"
    await query.edit_message_text(f"💻 {lang} — опиши що потрібно написати:")

async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mem = load_memory(uid)
    if not mem:
        await update.message.reply_text(
            "Я поки нічого не знаю про тебе.\n\n"
            "Просто спілкуйся зі мною — я автоматично запам'ятовую важливі деталі з розмови!"
        )
        return
    lines = ["Ось що я про тебе знаю:\n"]
    if mem.get("name"):      lines.append(f"Ім'я: {mem['name']}")
    if mem.get("city"):      lines.append(f"Місто: {mem['city']}")
    if mem.get("age"):       lines.append(f"Вік: {mem['age']}")
    if mem.get("occupation"):lines.append(f"Робота/навчання: {mem['occupation']}")
    if mem.get("interests"):
        lines.append(f"Інтереси: {', '.join(mem['interests'])}")
    if mem.get("facts"):
        lines.append("\nЗапам'ятовані факти:")
        for f in mem["facts"][-7:]:
            lines.append(f"- {f}")
    lines.append("\n/forget — щоб очистити пам'ять")
    await update.message.reply_text("\n".join(lines))

async def forget_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_memory(uid, {})
    await update.message.reply_text("Пам'ять очищена. Починаємо з чистого аркуша!")

async def food_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = "food_photo"
    await update.message.reply_text(
        "🍽 Надішли фото страви, і я визначу калорії та склад!\n\n"
        "Або напиши назву страви, наприклад: `борщ`, `піца маргарита`",
        parse_mode="Markdown"
    )

async def summarize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        text_to_sum = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "summarize"
        await update.message.reply_text("📝 Введи текст для резюме (скорочення):")
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = ask_ai(update.effective_user.id,
        f"Зроби коротке резюме цього тексту — 3-5 речень з головною суттю: {text_to_sum}")
    await update.message.reply_text(f"📝 Резюме:\n\n{result}")

async def synonyms_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        word = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "synonyms"
        await update.message.reply_text("🔄 Введи слово для пошуку синонімів:")
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = ask_ai(update.effective_user.id,
        f"Дай 10 синонімів до слова '{word}' українською. "
        f"Тільки список слів через кому, без пояснень.")
    await update.message.reply_text(f"🔄 Синоніми до '{word}':\n\n{result}")

async def meme_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        topic = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "meme"
        await update.message.reply_text("😂 На яку тему мем?\nНаприклад: `школа`, `програмісти`, `понеділок`")
        return
    await _generate_meme(update, topic)

async def _generate_meme(update: Update, topic: str):
    import urllib.parse, time
    prompts = [
        f"funny meme image about {topic}, white background, simple cartoon style, humorous",
        f"internet meme about {topic}, funny, bold caption text, simple drawing",
        f"comic meme {topic}, funny illustration, minimal style",
    ]
    for prompt in prompts:
        try:
            encoded = urllib.parse.quote(prompt)
            seed = random.randint(1, 99999)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=800&nologo=true&seed={seed}"
            r = requests.get(url, timeout=20)
            if r.status_code == 200 and len(r.content) > 5000:
                buf = io.BytesIO(r.content)
                buf.name = "meme.jpg"
                await update.message.reply_photo(photo=buf, caption=f"😂 Мем про: {topic}")
                return
        except:
            continue
    # Якщо картинка не вийшла — текстовий мем через AI
    result = ask_ai(update.effective_user.id,
        f"Придумай смішний текстовий мем про '{topic}'. "
        f"Формат: верхній текст / нижній текст. Коротко і смішно.")
    await update.message.reply_text(f"😂 Мем про {topic}:\n\n{result}")

async def quiz_next_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    q_idx = random.randint(0, len(QUIZ_QUESTIONS)-1)
    question = QUIZ_QUESTIONS[q_idx]
    buttons = [[InlineKeyboardButton(ans, callback_data=f"quiz|{q_idx}|{i}")]
               for i, ans in enumerate(question["a"])]
    score = quiz_scores.get(uid, {"score": 0, "total": 0})
    await q.edit_message_text(
        f"🧠 Вікторина!\n\n{question['q']}\n\nРахунок: {score['score']}/{score['total']}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показує список всіх користувачів — тільки для адміна"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Немає доступу.")
        return
    users = {}
    if os.path.exists(USERS_FILE):
        try:
            users = json.load(open(USERS_FILE, "r", encoding="utf-8"))
        except:
            pass
    msg_counts = {}
    last_seen = {}
    if os.path.exists(DIALOG_FILE):
        try:
            history = json.load(open(DIALOG_FILE, "r", encoding="utf-8"))
            for e in history:
                if e.get("role") == "user":
                    uid_str = str(e.get("user_id", ""))
                    msg_counts[uid_str] = msg_counts.get(uid_str, 0) + 1
                    date = e.get("date", "")
                    if date > last_seen.get(uid_str, ""):
                        last_seen[uid_str] = date
        except:
            pass
    sorted_users = sorted(users.items(), key=lambda x: msg_counts.get(x[0], 0), reverse=True)
    today = datetime.now().strftime("%Y-%m-%d")
    today_active = sum(1 for uid_str in last_seen if last_seen[uid_str].startswith(today))
    lines = [f"👥 Всього: {len(users)} | Сьогодні активних: {today_active}\n"]
    for i, (uid_str, v) in enumerate(sorted_users[:50]):
        name = v.get("name", "?")
        username = f"@{v.get('username')}" if v.get("username") else "без @"
        msgs = msg_counts.get(uid_str, 0)
        seen = last_seen.get(uid_str, v.get("joined", "?"))[:10]
        prem = "⭐" if is_premium(int(uid_str)) else ""
        lines.append(f"{i+1}. {prem}{name} ({username}) — {msgs} повід., {seen}")
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n..."
    await update.message.reply_text(text)

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Немає доступу.")
        return

    users = {}
    if os.path.exists(USERS_FILE):
        try:
            users = json.load(open(USERS_FILE, "r", encoding="utf-8"))
        except:
            pass

    total = len(users)
    premium_count = sum(1 for uid in users if is_premium(int(uid)))
    refs = load_refs()
    total_refs = sum(len(v) for v in refs.values())

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Розсилка всім", callback_data="admin|broadcast")],
        [InlineKeyboardButton("👥 Список юзерів", callback_data="admin|users")],
    ])
    await update.message.reply_text(
        f"🔧 *Адмін панель*\n\n"
        f"👥 Всього користувачів: {total}\n"
        f"⭐ Преміум: {premium_count}\n"
        f"🔗 Всього рефералів: {total_refs}\n"
        f"🧠 Активних сесій AI: {len(user_histories)}",
        parse_mode="Markdown",
        reply_markup=kb
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    action = q.data.split("|")[1]
    if action == "broadcast":
        user_state[q.from_user.id] = "admin_broadcast"
        await q.edit_message_text("📢 Введи текст розсилки — надішлю всім користувачам:")
    elif action == "users":
        users = {}
        if os.path.exists(USERS_FILE):
            try:
                users = json.load(open(USERS_FILE, "r", encoding="utf-8"))
            except:
                pass
        # Рахуємо повідомлення кожного юзера
        msg_counts = {}
        last_seen = {}
        if os.path.exists(DIALOG_FILE):
            try:
                history = json.load(open(DIALOG_FILE, "r", encoding="utf-8"))
                for e in history:
                    if e.get("role") == "user":
                        uid_str = str(e.get("user_id", ""))
                        msg_counts[uid_str] = msg_counts.get(uid_str, 0) + 1
                        date = e.get("date", "")
                        if date > last_seen.get(uid_str, ""):
                            last_seen[uid_str] = date
            except:
                pass
        # Сортуємо по кількості повідомлень
        sorted_users = sorted(users.items(), key=lambda x: msg_counts.get(x[0], 0), reverse=True)
        lines = []
        for i, (uid_str, v) in enumerate(sorted_users[:50]):
            name = v.get("name", "?")
            username = f"@{v.get('username')}" if v.get("username") else "без username"
            msgs = msg_counts.get(uid_str, 0)
            seen = last_seen.get(uid_str, v.get("joined", "?"))[:10]
            prem = "⭐" if is_premium(int(uid_str)) else ""
            lines.append(f"{i+1}. {prem}{name} ({username})\n   💬 {msgs} повід. | {seen}")
        text = "\n\n".join(lines) if lines else "Порожньо"
        # Розбиваємо якщо довго
        if len(text) > 3500:
            text = text[:3500] + "\n..."
        await q.edit_message_text(f"👥 Користувачі ({len(users)}):\n\n{text}")

async def premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    prem = is_premium(uid)

    if prem:
        data = load_premium()
        expires = data.get(str(uid), {}).get("expires", "")
        try:
            exp_str = datetime.fromisoformat(expires).strftime("%d.%m.%Y")
        except:
            exp_str = "?"
        await update.message.reply_text(
            f"⭐ У тебе вже є Преміум до {exp_str}!\n\nНасолоджуйся необмеженим AI 🚀"
        )
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 7 днів — 50 Stars",  callback_data="buy|7|50")],
        [InlineKeyboardButton("⭐ 30 днів — 150 Stars", callback_data="buy|30|150")],
        [InlineKeyboardButton("⭐ 90 днів — 350 Stars", callback_data="buy|90|350")],
    ])
    await update.message.reply_text(
        "⭐ *Преміум доступ*\n\n"
        "Що дає Преміум:\n"
        "• Необмежені AI запити\n"
        "• Пріоритетні відповіді\n"
        "• Значок ⭐ в профілі\n\n"
        "Оплата через Telegram Stars — безпечно і швидко:",
        parse_mode="Markdown",
        reply_markup=kb
    )

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, days, stars = q.data.split("|")
    days, stars = int(days), int(stars)
    await context.bot.send_invoice(
        chat_id=q.from_user.id,
        title=f"Преміум на {days} днів",
        description=f"Необмежений AI доступ на {days} днів",
        payload=f"premium_{days}",
        currency="XTR",
        prices=[{"label": f"Преміум {days}д", "amount": stars}],
        provider_token=""
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    payload = update.message.successful_payment.invoice_payload
    days = int(payload.split("_")[1])
    grant_premium(uid, days)
    await update.message.reply_text(
        f"✅ Оплата успішна! Преміум на {days} днів активовано!\n\n"
        f"Дякуємо за підтримку ⭐",
    )

async def ref_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    link = f"https://t.me/{bot_username}?start=ref{uid}"
    count = get_ref_count(uid)
    prem = is_premium(uid)

    if prem:
        data = load_premium()
        expires = data.get(str(uid), {}).get("expires", "")
        try:
            from datetime import datetime
            exp_str = datetime.fromisoformat(expires).strftime("%d.%m.%Y")
        except:
            exp_str = "?"
        prem_text = f"⭐ Преміум активний до {exp_str}"
    else:
        prem_text = "👤 Звичайний акаунт"

    next_reward = ""
    if count < 3:
        next_reward = f"\n🎯 До преміуму на 7 днів: ще {3 - count} друзів"
    elif count < 10:
        next_reward = f"\n🎯 До преміуму на 30 днів: ще {10 - count} друзів"

    await update.message.reply_text(
        f"<b>👥 Реферальна система</b>\n\n"
        f"Твоє посилання:\n{link}\n\n"
        f"Запрошено друзів: <b>{count}</b>\n"
        f"{prem_text}{next_reward}\n\n"
        f"3 друзі = Преміум 7 днів\n"
        f"10 друзів = Преміум 30 днів",
        parse_mode="HTML"
    )

def save_note(text: str):
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%d.%m %H:%M')}] {text}\n")

def read_notes() -> str:
    if not os.path.exists(NOTES_FILE):
        return "📭 Нотатки порожні."
    content = open(NOTES_FILE, "r", encoding="utf-8").read().strip()
    return content if content else "📭 Нотатки порожні."

def clear_notes():
    open(NOTES_FILE, "w").close()

# ══════════════════════════════════════
#  ЗАДАЧІ
# ══════════════════════════════════════
def load_tasks() -> list:
    if os.path.exists(TASKS_FILE):
        try:
            return json.load(open(TASKS_FILE, "r", encoding="utf-8"))
        except:
            pass
    return []

def save_tasks(tasks: list):
    json.dump(tasks, open(TASKS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def show_tasks() -> str:
    tasks = load_tasks()
    if not tasks:
        return "📭 Список задач порожній."
    done   = sum(1 for t in tasks if t["done"])
    lines  = [f"{'✅' if t['done'] else '🔲'} {i+1}. {t['text']}"
              for i, t in enumerate(tasks)]
    return "\n".join(lines) + f"\n\n📊 Виконано: {done}/{len(tasks)}"

# ══════════════════════════════════════
#  КОМАНДИ
# ══════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_new = register_user(update.effective_user)
    uid = update.effective_user.id

    # Сповіщення адміну про нового юзера
    if is_new:
        try:
            u = update.effective_user
            uname = f"@{u.username}" if u.username else "без username"
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"Новий юзер: {u.first_name} ({uname})\nID: {u.id}"
            )
        except:
            pass

    # Обробка реферального посилання
    if context.args and context.args[0].startswith("ref"):
        try:
            inviter_id = int(context.args[0][3:])
            if inviter_id != uid:
                is_new = add_referral(inviter_id, uid)
                if is_new:
                    reward_msg = check_ref_rewards(inviter_id)
                    if reward_msg:
                        try:
                            await context.bot.send_message(chat_id=inviter_id, text=f"🎁 {reward_msg}")
                        except:
                            pass
        except:
            pass

    name = update.effective_user.first_name
    msgs = count_dialogs(uid)
    mem = load_memory(uid)
    known_name = mem.get("name", name)

    if msgs > 0:
        # Юзер повертається
        greetings = [
            f"З поверненням, {known_name}! Скучив за тобою 😄",
            f"О, {known_name}! Радий тебе знову бачити 👋",
            f"Привіт, {known_name}! Готовий до нових питань 🚀",
            f"{known_name}, привіт! Що сьогодні цікавить? 🤔",
        ]
        greeting = random.choice(greetings)
        await update.message.reply_text(greeting, reply_markup=MAIN_KB)
    else:
        # Новий юзер
        await update.message.reply_text(
            f"Привіт, {name}! Я Марк — твій AI-асистент.\n\n"
            f"Можу відповісти на будь-яке питання, написати код, "
            f"порахувати калорії, перекласти текст, розсмішити жартом "
            f"і ще десятки речей.\n\n"
            f"Просто напиши що тебе цікавить — або обери кнопку нижче:",
            reply_markup=MAIN_KB
        )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    text = (
        f"Привіт, {name}! Ось що я вмію:\n\n"
        "Просто напиши мені будь-що — я відповім як розумний друг.\n\n"
        "Або використовуй кнопки:\n"
        "- Погода, Новини, Валюта, Крипта\n"
        "- Калькулятор, Переклад, Вікіпедія\n"
        "- Нотатки, Задачі, Нагадування\n"
        "- Генерація картинок, Музика\n"
        "- Калорії страв, Аналіз фото\n"
        "- Код на будь-якій мові\n"
        "- Жарти, Факти, Гороскоп, Ігри\n"
        "- І ще десятки функцій на сторінках 2 і 3\n\n"
        "Я також запам'ятовую про тебе важливі речі — /memory щоб побачити.\n\n"
        "Просто спілкуйся зі мною як з другом — я тут!"
    )
    await update.message.reply_text(text, reply_markup=MAIN_KB)

async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args) if context.args else "Kyiv"
    await update.message.reply_text(f"🌤 {get_weather(city)}")

async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.message.reply_text(f"📰 *Останні новини:*\n\n{get_news()}", parse_mode="Markdown")

async def currency_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) >= 3:
        try:
            await update.message.reply_text(
                get_currency(float(context.args[0]), context.args[1], context.args[2]),
                parse_mode="Markdown"
            )
        except:
            await update.message.reply_text("❌ Формат: /currency 100 USD UAH")
    else:
        user_state[update.effective_user.id] = "currency"
        await update.message.reply_text("💱 Введи: *кількість FROM TO*\nНаприклад: `100 USD UAH`", parse_mode="Markdown")

async def crypto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        aliases = {"btc":"bitcoin","eth":"ethereum","sol":"solana","bnb":"binancecoin","usdt":"tether","ton":"the-open-network"}
        coin = aliases.get(context.args[0].lower(), context.args[0].lower())
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text(get_crypto_price(coin), parse_mode="Markdown")
    else:
        await update.message.reply_text("₿ Обери криптовалюту:", reply_markup=crypto_keyboard())

async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        text = " ".join(context.args)
        await update.message.reply_text("🌐 На яку мову перекласти?", reply_markup=translate_keyboard(text))
    else:
        user_state[update.effective_user.id] = "translate"
        await update.message.reply_text("🌐 Введи текст для перекладу:")

async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(JOKES))

async def fact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🧠 *Цікавий факт:*\n\n{random.choice(FACTS)}", parse_mode="Markdown")

async def motivate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(MOTIVATIONS))

async def horoscope_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        sign = " ".join(context.args).lower()
        await update.message.reply_text(HOROSCOPES.get(sign, "❌ Знак не знайдено.\nСпробуй: овен, телець, близнюки, рак, лев, діва, терези, скорпіон, стрілець, козеріг, водолій, риби"))
    else:
        await update.message.reply_text("🔮 Обери свій знак зодіаку:", reply_markup=hs_keyboard())

async def note_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        save_note(" ".join(context.args))
        await update.message.reply_text("📝 Нотатку збережено ✅")
    else:
        user_state[update.effective_user.id] = "note"
        await update.message.reply_text("📝 Що записати?")

async def notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📋 *Твої нотатки:*\n\n{read_notes()}", parse_mode="Markdown")

async def clearnotes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_notes()
    await update.message.reply_text("🗑 Нотатки очищено ✅")

async def task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        tasks = load_tasks()
        tasks.append({"text": " ".join(context.args), "done": False,
                      "created": datetime.now().strftime("%d.%m %H:%M")})
        save_tasks(tasks)
        await update.message.reply_text(f"✅ Задачу додано!")
    else:
        user_state[update.effective_user.id] = "task"
        await update.message.reply_text("✅ Яку задачу додати?")

async def tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📋 *Твої задачі:*\n\n{show_tasks()}", parse_mode="Markdown")

async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        n = int(context.args[0])
        tasks = load_tasks()
        if 1 <= n <= len(tasks):
            tasks[n-1]["done"] = True
            save_tasks(tasks)
            await update.message.reply_text(f"✅ Задачу {n} виконано\\! Молодець 💪", parse_mode="MarkdownV2")
        else:
            await update.message.reply_text("❌ Задачу не знайдено.")
    except:
        await update.message.reply_text("❌ Вкажи номер: /done 1")

async def deltask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        n = int(context.args[0])
        tasks = load_tasks()
        if 1 <= n <= len(tasks):
            removed = tasks.pop(n-1)
            save_tasks(tasks)
            await update.message.reply_text(f"🗑 Задачу видалено.")
        else:
            await update.message.reply_text("❌ Задачу не знайдено.")
    except:
        await update.message.reply_text("❌ Вкажи номер: /deltask 1")

async def calc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await update.message.reply_text(calculate(" ".join(context.args)), parse_mode="Markdown")
    else:
        user_state[update.effective_user.id] = "calc"
        await update.message.reply_text("🧮 Введи вираз:\nНаприклад: `25 * 4 + 10`", parse_mode="Markdown")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        query = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "search"
        await update.message.reply_text(
            "🔍 Що шукати?\n\nМожна написати:\n"
            "• `iPhone 15 Pro OLX` — пошук на OLX\n"
            "• `Nike Air Max Rozetka` — пошук на Rozetka\n"
            "• `MacBook eBay` — пошук на eBay\n"
            "• Або просто назву товару",
            parse_mode="Markdown"
        )
        return
    await _do_search(update, context, query)

async def _do_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    import urllib.parse
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    q = urllib.parse.quote_plus(query)

    # Визначаємо на якому сайті шукати
    ql = query.lower()
    if "olx" in ql:
        q_clean = urllib.parse.quote_plus(query.lower().replace("olx","").strip())
        sites = [("🛒 OLX", f"https://www.olx.ua/uk/list/q-{q_clean}/")]
    elif "rozetka" in ql:
        q_clean = urllib.parse.quote_plus(query.lower().replace("rozetka","").strip())
        sites = [("🛍 Rozetka", f"https://rozetka.com.ua/ua/search/?text={q_clean}")]
    elif "ebay" in ql:
        q_clean = urllib.parse.quote_plus(query.lower().replace("ebay","").strip())
        sites = [("🌐 eBay", f"https://www.ebay.com/sch/i.html?_nkw={q_clean}")]
    elif "amazon" in ql:
        q_clean = urllib.parse.quote_plus(query.lower().replace("amazon","").strip())
        sites = [("📦 Amazon", f"https://www.amazon.com/s?k={q_clean}")]
    else:
        # Шукаємо на всіх одразу
        sites = [
            ("🛒 OLX",      f"https://www.olx.ua/uk/list/q-{q}/"),
            ("🛍 Rozetka",  f"https://rozetka.com.ua/ua/search/?text={q}"),
            ("🌐 eBay",     f"https://www.ebay.com/sch/i.html?_nkw={q}"),
            ("📦 Amazon",   f"https://www.amazon.com/s?k={q}"),
            ("🔍 Google",   f"https://www.google.com/search?q={q}"),
        ]

    # AI аналіз що шукати і поради
    ai_tip = ask_ai(update.effective_user.id,
        f"Дай короткі поради (2-3 речення) як краще шукати '{query}': на що звернути увагу, "
        f"яка середня ціна, як не натрапити на шахраїв. Відповідь коротка і практична.")

    buttons = [[InlineKeyboardButton(name, url=url)] for name, url in sites]
    kb = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        f"🔍 *Пошук: {query}*\n\n"
        f"💡 {ai_tip}\n\n"
        f"Натисни кнопку щоб відкрити:",
        parse_mode="Markdown",
        reply_markup=kb
    )

async def wiki_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text(search_wiki(" ".join(context.args)), parse_mode="Markdown")
    else:
        user_state[update.effective_user.id] = "wiki"
        await update.message.reply_text("📖 Про що шукати у Вікіпедії?")

async def qr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        buf = generate_qr(" ".join(context.args))
        await update.message.reply_photo(photo=buf, caption="📷 QR-код готовий ✅")
    else:
        user_state[update.effective_user.id] = "qr"
        await update.message.reply_text("📷 Введи текст або посилання для QR-коду:")

async def short_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await update.message.reply_text(shorten_url(context.args[0]))
    else:
        user_state[update.effective_user.id] = "short"
        await update.message.reply_text("🔗 Введи посилання для скорочення:")

async def ip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ip = context.args[0] if context.args else ""
    await update.message.reply_text(get_ip_info(ip), parse_mode="Markdown")

async def remind_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        minutes = int(context.args[0])
        text = " ".join(context.args[1:]) or "Нагадування! ⏰"
        chat_id = update.effective_chat.id
        await update.message.reply_text(f"⏰ Нагадаю через *{minutes} хв*: {text} ✅", parse_mode="Markdown")
        async def _remind():
            await asyncio.sleep(minutes * 60)
            await context.bot.send_message(chat_id=chat_id, text=f"🔔 *Нагадування:* {text}", parse_mode="Markdown")
        asyncio.create_task(_remind())
    except:
        await update.message.reply_text("❌ Формат: /remind 5 Зателефонувати другу")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = update.effective_user.first_name
    msgs = count_dialogs(uid)
    tasks = load_tasks()
    done  = sum(1 for t in tasks if t["done"])
    notes = len([l for l in read_notes().split("\n") if l.strip() and "порожні" not in l])
    mem   = len(user_histories.get(uid, []))

    text = (
        f"📊 Статистика {name}:\n\n"
        f"💬 Повідомлень до AI: {msgs}\n"
        f"✅ Задач виконано: {done}/{len(tasks)}\n"
        f"📝 Нотаток: {notes}\n"
        f"🧠 Повідомлень у пам'яті: {mem}/40"
    )

    # Адмін бачить загальну статистику
    if uid == ADMIN_ID:
        try:
            users = json.load(open(USERS_FILE, "r", encoding="utf-8")) if os.path.exists(USERS_FILE) else {}
            total_users = len(users)
            today = datetime.now().strftime("%Y-%m-%d")
            today_msgs = 0
            week_msgs = 0
            if os.path.exists(DIALOG_FILE):
                history = json.load(open(DIALOG_FILE, "r", encoding="utf-8"))
                today_msgs = sum(1 for e in history if e.get("role") == "user" and e.get("date", "").startswith(today))
                from datetime import timedelta
                week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                week_msgs = sum(1 for e in history if e.get("role") == "user" and e.get("date", "") >= week_ago)
            active_now = len(user_histories)
            text += (
                f"\n\n👑 Адмін-статистика:\n"
                f"👥 Всього користувачів: {total_users}\n"
                f"📨 Повідомлень сьогодні: {today_msgs}\n"
                f"📊 За тиждень: {week_msgs}\n"
                f"🟢 Активних зараз: {active_now}"
            )
        except:
            pass

    await update.message.reply_text(text)

async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("🗑 Пам'ять AI очищено ✅")

async def dice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = random.randint(1, 6)
    faces = ["⚀","⚁","⚂","⚃","⚄","⚅"]
    await update.message.reply_text(f"🎲 Кубик показав: {faces[n-1]} ({n})")

async def coin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🪙 Монетка: {random.choice(['Орел 🦅', 'Решка 🪙'])}")

async def guess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    number = random.randint(1, 100)
    guess_games[uid] = {"number": number, "attempts": 0}
    user_state[uid] = "guess"
    await update.message.reply_text("🎲 Я загадав число від *1* до *100*\\. Вгадуй\\! 🤔", parse_mode="MarkdownV2")

# ══════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════
async def translate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, lang, text = q.data.split("|", 2)
    await q.edit_message_text(f"🌐 *Переклад:*\n\n{translate_text(text, lang)}", parse_mode="Markdown")

async def horoscope_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    sign = q.data.split("|")[1]
    await q.edit_message_text(HOROSCOPES.get(sign, "❌ Знак не знайдено."))

async def crypto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Завантажую... ⏳")
    coin = q.data.split("|")[1]
    await q.edit_message_text(get_crypto_price(coin), parse_mode="Markdown")

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid    = q.from_user.id
    action = q.data.split("|")[1]

    if action == "guess":
        number = random.randint(1, 100)
        guess_games[uid] = {"number": number, "attempts": 0}
        user_state[uid] = "guess"
        await q.edit_message_text("🎲 Я загадав число від *1* до *100*\\. Напиши своє число\\! 🤔", parse_mode="MarkdownV2")
    elif action == "dice":
        n = random.randint(1, 6)
        faces = ["⚀","⚁","⚂","⚃","⚄","⚅"]
        await q.edit_message_text(f"🎲 Кубик показав: {faces[n-1]} ({n})", reply_markup=games_keyboard())
    elif action == "coin":
        await q.edit_message_text(f"🪙 Монетка: {random.choice(['Орел 🦅', 'Решка 🪙'])}", reply_markup=games_keyboard())
    elif action == "random":
        await q.edit_message_text(f"🔢 Випадкове число: *{random.randint(1, 100)}*", parse_mode="Markdown", reply_markup=games_keyboard())
    elif action == "rps":
        user_state[uid] = "rps"
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🪨 Камінь",  callback_data="rps|rock"),
            InlineKeyboardButton("✂️ Ножиці",  callback_data="rps|scissors"),
            InlineKeyboardButton("📄 Папір",   callback_data="rps|paper"),
        ]])
        await q.edit_message_text("✂️ Обери:", reply_markup=kb)

async def rps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    choices = {"rock": "🪨 Камінь", "scissors": "✂️ Ножиці", "paper": "📄 Папір"}
    wins    = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    user_choice = q.data.split("|")[1]
    bot_choice  = random.choice(list(choices.keys()))
    if user_choice == bot_choice:
        result = "🤝 Нічия!"
    elif wins[user_choice] == bot_choice:
        result = "🏆 Ти переміг!"
    else:
        result = "😅 Я переміг!"
    await q.edit_message_text(
        f"✂️ *Камінь-ножиці-папір*\n\n"
        f"Ти: {choices[user_choice]}\n"
        f"Я: {choices[bot_choice]}\n\n"
        f"{result}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Ще раз", callback_data="game|rps")
        ]])
    )

# ══════════════════════════════════════
#  ГОЛОВНИЙ ОБРОБНИК ПОВІДОМЛЕНЬ
# ══════════════════════════════════════
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    text = update.message.text

    # Антиспам
    if not check_antispam(uid):
        await update.message.reply_text("Надто багато повідомлень. Зачекай хвилину.")
        return

    # --- Кнопки що потребують вводу ---
    input_buttons = {
        "🌤 Погода":      ("weather",   "🌤 Введи назву міста:"),
        "💱 Валюта":      ("currency",  "💱 Введи: *кількість FROM TO*\nНаприклад: `100 USD UAH`"),
        "🌐 Переклад":    ("translate", "🌐 Введи текст для перекладу:"),
        "🧮 Калькулятор": ("calc",      "🧮 Введи вираз:\nНаприклад: `25 * 4 + 10`"),
        "📖 Вікіпедія":   ("wiki",      "📖 Про що шукати у Вікіпедії?"),
        "📷 QR-код":      ("qr",        "📷 Введи текст або посилання:"),
        "⏰ Нагадування": ("remind_btn","⏰ Введи: *хвилини текст*\nНаприклад: `10 Зателефонувати`"),
    }
    if text in input_buttons:
        state, prompt = input_buttons[text]
        user_state[uid] = state
        await update.message.reply_text(prompt, parse_mode="Markdown")
        return

    # --- Прості кнопки ---
    simple = {
        "📰 Новини":     news_cmd,
        "😂 Жарт":       joke_cmd,
        "🧠 Факт":       fact_cmd,
        "📝 Нотатки":    notes_cmd,
        "✅ Задачі":     tasks_cmd,
        "❓ Допомога":   help_cmd,
        "💪 Мотивація":  motivate_cmd,
        "📊 Статистика": stats_cmd,
    }
    if text in simple:
        await simple[text](update, context)
        return

    if text == "🔐 Пароль":
        await password_cmd(update, context)
        return
    if text == "🎭 Настрій":
        user_state[uid] = "mood"
        await update.message.reply_text("🎭 Введи текст для аналізу настрою:")
        return
    if text == "📐 Конвертер":
        user_state[uid] = "convert"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("km → mi", callback_data="conv|1|km|mi"),
             InlineKeyboardButton("mi → km", callback_data="conv|1|mi|km")],
            [InlineKeyboardButton("kg → lb", callback_data="conv|1|kg|lb"),
             InlineKeyboardButton("lb → kg", callback_data="conv|1|lb|kg")],
            [InlineKeyboardButton("°C → °F", callback_data="conv|100|c|f"),
             InlineKeyboardButton("°F → °C", callback_data="conv|212|f|c")],
            [InlineKeyboardButton("m → ft",  callback_data="conv|1|m|ft"),
             InlineKeyboardButton("cm → in", callback_data="conv|1|cm|in")],
        ])
        await update.message.reply_text(
            "📐 *Конвертер одиниць*\n\nОбери або напиши: `100 km mi`",
            parse_mode="Markdown", reply_markup=kb
        )
        return
    if text == "🌐 Мова AI":
        await lang_cmd(update, context)
        return
    if text == "📋 Шпаргалка":
        user_state[uid] = "cheatsheet"
        await update.message.reply_text("📋 Введи тему для шпаргалки:")
        return
    if text == "✍️ Граматика":
        user_state[uid] = "grammar"
        await update.message.reply_text("✍️ Введи текст для перевірки граматики:")
        return
    if text == "📱 Пост":
        user_state[uid] = "post"
        await update.message.reply_text("📱 На яку тему пост?\nНаприклад: `мотивація для школярів`")
        return
    if text == "💡 Бізнес-ідея":
        user_state[uid] = "idea"
        await update.message.reply_text("💡 В якій сфері шукаєш ідею?")
        return
    if text == "💰 Витрати":
        await expense_cmd(update, context)
        return
    if text == "🧠 Вікторина":
        await quiz_cmd(update, context)
        return
    if text == "💑 Сумісність":
        await compat_cmd(update, context)
        return
    if text == "📅 Розклад":
        await schedule_cmd(update, context)
        return
    if text == "➡️ Сторінка 3":
        await update.message.reply_text("Сторінка 3:", reply_markup=PAGE3_KB)
        return
    if text == "🍅 Помодоро":
        await pomodoro_cmd(update, context)
        return
    if text == "🎮 Нікнейм":
        await nickname_cmd(update, context)
        return
    if text == "🌐 Перевірка сайту":
        user_state[uid] = "checksite"
        await update.message.reply_text("🌐 Введи адресу сайту:\nНаприклад: `google.com`", parse_mode="Markdown")
        return
    if text == "📝 Резюме тексту":
        user_state[uid] = "summarize"
        await update.message.reply_text("📝 Введи текст для скорочення:")
        return
    if text == "🔄 Синоніми":
        user_state[uid] = "synonyms"
        await update.message.reply_text("🔄 Введи слово для пошуку синонімів:")
        return
    if text == "🌍 Країна по IP":
        await ip_cmd(update, context)
        return
    if text == "😂 Мем":
        user_state[uid] = "meme"
        await update.message.reply_text("😂 На яку тему мем?\nНаприклад: `школа`, `програмісти`", parse_mode="Markdown")
        return
    if text == "➡️ Ще функції":
        await update.message.reply_text("Сторінка 2:", reply_markup=PAGE2_KB)
        return
    if text == "⬅️ Назад":
        await update.message.reply_text("Головне меню:", reply_markup=MAIN_KB)
        return
    if text == "⭐ Купити Преміум":
        await premium_cmd(update, context)
        return
    if text == "👥 Реферали":
        await ref_cmd(update, context)
        return
    if text == "🔗 Моє посилання":
        await ref_cmd(update, context)
        return
    if text == "📊 Мій статус":
        uid2 = update.effective_user.id
        prem = is_premium(uid2)
        count = get_ref_count(uid2)
        if prem:
            data = load_premium()
            expires = data.get(str(uid2), {}).get("expires", "")
            try:
                exp_str = datetime.fromisoformat(expires).strftime("%d.%m.%Y")
            except:
                exp_str = "?"
            status = f"⭐ Преміум до {exp_str}"
        else:
            status = "👤 Звичайний акаунт"
        await update.message.reply_text(
            f"📊 *Твій статус*\n\n"
            f"{status}\n"
            f"👥 Запрошено друзів: {count}\n\n"
            f"3 друзі = Преміум 7 днів\n"
            f"10 друзів = Преміум 30 днів",
            parse_mode="Markdown"
        )
        return
    if text == "🎨 Генерація":
        user_state[uid] = "imagine"
        await update.message.reply_text("🎨 Опиши що намалювати (англійською краще):\nНаприклад: `beautiful sunset over mountains`", parse_mode="Markdown")
        return
    if text == "🎵 Музика":
        user_state[uid] = "music"
        await update.message.reply_text("🎵 Опиши яку музику згенерувати:\nНаприклад: `relaxing lofi beats`", parse_mode="Markdown")
        return
    if text == "⭐ Преміум":
        await premium_cmd(update, context)
        return
    if text == "🔍 Пошук":
        user_state[uid] = "search"
        await update.message.reply_text(
            "🔍 Що шукати?\n\nПриклади:\n"
            "• `iPhone 15 OLX`\n"
            "• `Nike Air Max Rozetka`\n"
            "• `MacBook eBay`\n"
            "• Або просто назву товару",
            parse_mode="Markdown"
        )
        return

    if text == "🍽 Калорії":
        await food_cmd(update, context)
        return

    if text == "ð» ÐÐ¾Ð´":
        await code_cmd(update, context)
        return

    if text == "ð¼ Ð¦Ð¸ÑÐ°ÑÐ°":
        await quote_cmd(update, context)
        return

    if text == "🧠 Моя пам'ять":
        await memory_cmd(update, context)
        return

    if text == "🔬 Глибокий аналіз":
        await deep_cmd(update, context)
        return

    if text == "🔗 Аналіз сайту":
        await url_cmd(update, context)
        return

    if text == "🎭 Дебати":
        await debate_cmd(update, context)
        return

    if text == "🎬 Комікс":
        await comic_cmd(update, context)
        return

    if text == "🏆 Лідерборд":
        await leaderboard_cmd(update, context)
        return

    if text == "📓 Щоденник":
        await diary_cmd(update, context)
        return

    if text == "💪 Звички":
        await habits_cmd(update, context)
        return

    if text == "📋 Резюме/CV":
        await cv_cmd(update, context)
        return

    if text == "🌅 Дайджест":
        await digest_cmd(update, context)
        return

    if text == "📺 YouTube":
        await youtube_cmd(update, context)
        return

    if text == "🎭 Персонаж":
        await persona_cmd(update, context)
        return

    if text == "📚 Вчитель":
        await teach_cmd(update, context)
        return

    if text == "�🔮 Гороскоп":
        await horoscope_cmd(update, context)
        return
    if text == "₿ Крипта":
        await crypto_cmd(update, context)
        return
    if text == "🎲 Ігри":
        await update.message.reply_text("🎮 Обери гру:", reply_markup=games_keyboard())
        return

    # --- Стани очікування ---
    state = user_state.pop(uid, None)

    if state == "weather":
        await update.message.reply_text(f"🌤 {get_weather(text)}")
        return
    if state == "currency":
        parts = text.split()
        if len(parts) >= 3:
            try:
                await update.message.reply_text(get_currency(float(parts[0]), parts[1], parts[2]), parse_mode="Markdown")
            except:
                await update.message.reply_text("❌ Формат: 100 USD UAH")
        else:
            await update.message.reply_text("❌ Формат: 100 USD UAH")
        return
    if state == "translate":
        await update.message.reply_text("🌐 На яку мову?", reply_markup=translate_keyboard(text))
        return
    if state == "note":
        save_note(text)
        await update.message.reply_text(f"📝 Записав ✅")
        return
    if state == "task":
        tasks = load_tasks()
        tasks.append({"text": text, "done": False, "created": datetime.now().strftime("%d.%m %H:%M")})
        save_tasks(tasks)
        await update.message.reply_text(f"✅ Задачу додано!")
        return
    if state == "calc":
        await update.message.reply_text(calculate(text), parse_mode="Markdown")
        return
    if state == "checksite":
        url = text if text.startswith("http") else "https://" + text
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                await update.message.reply_text(f"✅ Сайт {url} працює!")
            else:
                await update.message.reply_text(f"⚠️ Код відповіді: {r.status_code}")
        except:
            await update.message.reply_text(f"❌ Сайт {url} недоступний")
        return
    if state == "deep":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai_deep(uid, text)
        parts = split_long_message(result)
        for i, part in enumerate(parts):
            if len(parts) > 1:
                await update.message.reply_text(f"[{i+1}/{len(parts)}]\n\n{part}")
            else:
                await update.message.reply_text(part)
        return
    if state == "url":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        page_text = fetch_url_text(text)
        if page_text.startswith("ERROR:"):
            await update.message.reply_text(f"❌ Не вдалося відкрити: {page_text[6:]}")
        else:
            result = ask_ai(uid, f"Зроби короткий переказ суті цієї сторінки (5-7 речень):\n\n{page_text}")
            parts = split_long_message(result)
            for i, part in enumerate(parts):
                prefix = f"[{i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
                await update.message.reply_text(f"🔗 Аналіз:\n\n{prefix}{part}")
        return
    if state == "youtube":
        await _summarize_youtube(update, uid, text, context)
        return
    if state == "teach":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid,
            f"Поясни тему '{text}' максимально просто, як для 10-річної дитини. "
            f"Використовуй прості слова, аналогії, приклади. Без зірочок."
        )
        parts = split_long_message(result)
        for i, part in enumerate(parts):
            await update.message.reply_text(f"[{i+1}/{len(parts)}]\n\n{part}" if len(parts) > 1 else part)
        return
    if state == "ad_text":
        # Надсилаємо рекламу всім
        users = {}
        if os.path.exists(USERS_FILE):
            try:
                users = json.load(open(USERS_FILE, encoding='utf-8'))
            except:
                pass
        sent = 0
        for uid_str in users:
            try:
                await context.bot.send_message(chat_id=int(uid_str), text=f"📢 {text}")
                sent += 1
                await asyncio.sleep(0.05)
            except:
                pass
        await update.message.reply_text(f"Реклама надіслана {sent} юзерам.")
        return
    if state == "ad_auto":
        # Зберігаємо авторекламу
        json.dump({"text": text, "enabled": True},
                  open("ad_auto.json", "w", encoding="utf-8"), ensure_ascii=False)
        await update.message.reply_text("Авторекламу збережено. Буде надсилатись щодня о 12:00.")
        return
    if state == "calories_add":
        await _track_calories(update, uid, text)
        return
    if state == "tiktok_post":
        await _generate_tiktok_post(update, uid, text)
        return
    if state and state.startswith("persona_"):
        person = state[8:]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = ask_ai(uid,
            f"Ти — {person}. Відповідай ТІЛЬКИ від імені цієї людини, "
            f"використовуй їх стиль мовлення, цінності та погляди. "
            f"Питання: {text}"
        )
        await update.message.reply_text(reply)
        return
    if state == "comic":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        await _generate_comic(update, uid, text)
        return
    if state == "quote":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        if text.lower() == "авто":
            await update.message.reply_text("Придумую цитату...")
            quote = ask_ai(uid, "Придумай одну коротку потужну мотиваційну цитату українською. Тільки сам текст цитати, без лапок і пояснень. Максимум 10 слів.")
            author = "Mark AI"
        elif "|" in text:
            parts = text.split("|", 1)
            quote = parts[0].strip()
            author = parts[1].strip()
        else:
            quote = text.strip()
            author = ""
        try:
            buf = generate_quote_image(quote, author)
            await update.message.reply_photo(photo=buf, caption=f'"{quote}"\n{("— " + author) if author else ""}')
        except Exception as e:
            await update.message.reply_text(f"❌ Помилка генерації: {e}")
        return
    if state == "habits_add":
        habits = load_habits(uid)
        habits[text.strip()] = {"done_dates": [], "streak": 0}
        save_habits(uid, habits)
        await update.message.reply_text(f"Звичку '{text}' додано! Відмічай щодня через /habits")
        return
    if state == "habits_delete":
        habits = load_habits(uid)
        name = text.strip()
        if name in habits:
            del habits[name]
            save_habits(uid, habits)
            await update.message.reply_text(f"Звичку '{name}' видалено.")
        else:
            await update.message.reply_text(f"Звичку '{name}' не знайдено.")
        return
    if state == "digest_city":
        settings = load_digest_settings()
        key = str(uid)
        if key in settings:
            settings[key]["city"] = text.strip()
            save_digest_settings(settings)
            hour = settings[key].get("hour", 8)
            await update.message.reply_text(f"Дайджест налаштовано: щодня о {hour}:00, місто: {text.strip()}")
        return
    if state == "cv":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid,
            f"Створи професійне резюме/CV на основі цієї інформації. "
            f"Структуруй: Контакти, Мета, Досвід, Навички, Освіта. "
            f"Без Markdown зірочок:\n\n{text}"
        )
        parts = split_long_message(result)
        for i, part in enumerate(parts):
            prefix = f"[{i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
            await update.message.reply_text(f"📄 Резюме:\n\n{prefix}{part}")
        return
    if state == "debate":
        user_state[uid] = f"debate_{text}"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai_deep(uid,
            f"Ти граєш роль опонента в дебатах. Тема: '{text}'.\n"
            f"Займи ПРОТИЛЕЖНУ позицію і аргументуй її переконливо. Потім запитай мою думку."
        )
        await update.message.reply_text(f"🎭 Тема: {text}\n\n{result}")
        return
    if state and state.startswith("debate_"):
        topic = state[7:]
        user_state[uid] = state  # зберігаємо стан дебатів
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"[Дебати на тему '{topic}'] Відповідь опонента: {text}\nПродовжуй дебати, заперечуй аргументи.")
        await update.message.reply_text(result)
        return
    if state == "food_photo":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Дай інформацію про страву '{text}': 1) Калорії на 100г і на порцію 2) Основні інгредієнти 3) КБЖУ (білки/жири/вуглеводи) 4) Чи корисна ця страва. Відповідай структуровано.")
        await update.message.reply_text(f"🍽 {text}:\n\n{result}")
        return
    if state == "code":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Ти — досвідчений програміст. Напиши код будь-якою підходящою мовою: {text}\nПоясни коротко що робить код і як запустити.")
        await update.message.reply_text(result)
        return
    if state and state.startswith("code_"):
        lang = state[5:]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Ти — досвідчений програміст. Напиши код на {lang}: {text}\nПоясни коротко що робить код і як запустити.")
        await update.message.reply_text(result)
        return
    if state == "summarize":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Зроби коротке резюме 3-5 речень: {text}")
        await update.message.reply_text(f"📝 Резюме:\n\n{result}")
        return
    if state == "synonyms":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Дай 10 синонімів до слова '{text}' українською. Тільки список через кому.")
        await update.message.reply_text(f"🔄 Синоніми до '{text}':\n\n{result}")
        return
    if state == "nickname":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Згенеруй 10 унікальних нікнеймів у стилі '{text}'. Тільки список, кожен з нового рядка.")
        await update.message.reply_text(f"🎮 Нікнейми:\n\n{result}")
        return
    if state == "meme":
        await _generate_meme(update, text)
        return
    if state == "cheatsheet":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Зроби коротку шпаргалку по темі '{text}'. Ключові факти, дати, визначення — коротко і по суті. Максимум 20 пунктів.")
        await update.message.reply_text(f"📋 Шпаргалка: {text}\n\n{result}")
        return
    if state == "grammar":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Перевір граматику і стиль. Спочатку виправлений текст, потім список помилок: {text}")
        await update.message.reply_text(f"✍️ Перевірка:\n\n{result}")
        return
    if state == "post":
        await update.message.reply_text("📱 Обери платформу:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("TikTok", callback_data=f"post|tiktok|{text[:100]}"),
             InlineKeyboardButton("Instagram", callback_data=f"post|instagram|{text[:100]}")],
            [InlineKeyboardButton("Twitter/X", callback_data=f"post|twitter|{text[:100]}"),
             InlineKeyboardButton("Facebook", callback_data=f"post|facebook|{text[:100]}")],
        ]))
        return
    if state == "idea":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = ask_ai(uid, f"Згенеруй 5 конкретних бізнес-ідей для '{text}'. Для кожної: назва, суть, як почати, скільки заробити.")
        await update.message.reply_text(f"💡 Бізнес-ідеї:\n\n{result}")
        return
    if state == "search":
        await _do_search(update, context, text)
        return
    if state == "wiki":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text(search_wiki(text), parse_mode="Markdown")
        return
    if state == "qr":
        buf = generate_qr(text)
        await update.message.reply_photo(photo=buf, caption="📷 QR-код готовий ✅")
        return
    if state == "mood":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text(f"🎭 *Аналіз настрою:*\n\n{analyze_mood(text)}", parse_mode="Markdown")
        return
    if state == "convert":
        parts = text.split()
        if len(parts) >= 3:
            try:
                await update.message.reply_text(convert_units(float(parts[0]), parts[1], parts[2]), parse_mode="Markdown")
            except:
                await update.message.reply_text("❌ Формат: 100 km mi")
        else:
            await update.message.reply_text("❌ Формат: 100 km mi")
        return
    if state == "admin_broadcast":
        if update.effective_user.id != ADMIN_ID:
            return
        users = {}
        if os.path.exists(USERS_FILE):
            try:
                users = json.load(open(USERS_FILE, "r", encoding="utf-8"))
            except:
                pass
        sent, failed = 0, 0
        for uid_str in users:
            try:
                await context.bot.send_message(chat_id=int(uid_str), text=f"📢 {text}")
                sent += 1
            except:
                failed += 1
        await update.message.reply_text(f"✅ Розсилка завершена!\nНадіслано: {sent}\nПомилок: {failed}")
        return
    if state == "imagine":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        await update.message.reply_text("Добре, генерую зображення. Зачекай ~15 секунд.")
        img = generate_image(text)
        if isinstance(img, bytes):
            buf = io.BytesIO(img); buf.name = "img.jpg"
            await update.message.reply_photo(photo=buf, caption=f"🎨 {text[:100]}")
        else:
            await update.message.reply_photo(photo=img, caption=f"🎨 {text[:100]}")
        return
    if state == "music":
        import urllib.parse
        encoded = urllib.parse.quote(text)
        audio_url = f"https://audio.pollinations.ai/{encoded}"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_voice")
        try:
            r = requests.get(audio_url, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                buf = io.BytesIO(r.content)
                buf.name = "music.mp3"
                await update.message.reply_audio(audio=buf, title=text[:50], performer="Mark AI")
            else:
                raise Exception("empty")
        except Exception:
            suno_url = f"https://suno.com/create?prompt={encoded}"
            await update.message.reply_text(
                "🎵 Не вдалося згенерувати автоматично. Відкрий Suno:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎵 Відкрити Suno", url=suno_url)
                ]])
            )
        return
    if state == "short":
        await update.message.reply_text(shorten_url(text))
        return
    if state == "remind_btn":
        try:
            parts = text.split(maxsplit=1)
            minutes = int(parts[0])
            rtxt = parts[1] if len(parts) > 1 else "Нагадування! ⏰"
            chat_id = update.effective_chat.id
            await update.message.reply_text(f"⏰ Нагадаю через *{minutes} хв*: {rtxt} ✅", parse_mode="Markdown")
            async def _remind():
                await asyncio.sleep(minutes * 60)
                await context.bot.send_message(chat_id=chat_id, text=f"🔔 *Нагадування:* {rtxt}", parse_mode="Markdown")
            asyncio.create_task(_remind())
        except:
            await update.message.reply_text("❌ Формат: 10 Зателефонувати")
        return
    if state == "guess":
        try:
            guess  = int(text)
            game   = guess_games.get(uid, {})
            number = game.get("number", 50)
            game["attempts"] = game.get("attempts", 0) + 1
            guess_games[uid] = game
            if guess < number:
                user_state[uid] = "guess"
                await update.message.reply_text(f"📈 Більше\\! Спроба {game['attempts']} 🤔", parse_mode="MarkdownV2")
            elif guess > number:
                user_state[uid] = "guess"
                await update.message.reply_text(f"📉 Менше\\! Спроба {game['attempts']} 🤔", parse_mode="MarkdownV2")
            else:
                attempts = game["attempts"]
                del guess_games[uid]
                emoji = "🏆" if attempts <= 5 else "🎉"
                await update.message.reply_text(
                    f"{emoji} Правильно\\! Це було *{number}*\\!\nВгадав за *{attempts}* спроб\\!",
                    parse_mode="MarkdownV2"
                )
        except:
            user_state[uid] = "guess"
            await update.message.reply_text("🔢 Введи число від 1 до 100:")
        return

    # --- Автопошук ---
    search_triggers = ["знайди", "пошукай", "знайти", "пошукати", "де купити", "де знайти"]
    if any(text.lower().startswith(t) for t in search_triggers):
        query = text
        for t in search_triggers:
            if text.lower().startswith(t):
                query = text[len(t):].strip()
                break
        if query:
            await _do_search(update, context, query)
            return

    # --- AI відповідь ---
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Перевірка ліміту
    allowed, remaining = check_limit(uid)
    if not allowed:
        await update.message.reply_text(
            f"Ти використав {FREE_DAILY_LIMIT} безкоштовних повідомлень на сьогодні.\n\n"
            f"Купи Преміум для безлімітного доступу — /premium\n"
            f"Або запроси 3 друзів — /ref"
        )
        return

    save_dialog(uid, "user", text)

    # Підказка якщо схоже на команду кнопки
    button_hints = {
        "погода": "🌤 Натисни кнопку Погода або напиши /weather місто",
        "новини": "📰 Натисни кнопку Новини або /news",
        "валюта": "💱 Натисни кнопку Валюта або напиши: 100 USD UAH",
        "переклад": "🌐 Натисни кнопку Переклад або /translate текст",
        "калькулятор": "🧮 Натисни кнопку Калькулятор або /calc вираз",
        "нотатки": "📝 Натисни кнопку Нотатки або /notes",
        "задачі": "✅ Натисни кнопку Задачі або /tasks",
        "крипта": "₿ Натисни кнопку Крипта або /crypto",
        "гороскоп": "🔮 Натисни кнопку Гороскоп або /horoscope",
    }
    text_lower = text.lower()
    for keyword, hint in button_hints.items():
        if text_lower == keyword:
            await update.message.reply_text(hint)
            return

    # Автовизначення URL
    import re as _re
    urls_in_text = _re.findall(r'https?://\S+', text)
    if urls_in_text:
        url_found = urls_in_text[0]
        task = text.replace(url_found, "").strip()
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        # YouTube — окрема обробка
        if any(yt in url_found for yt in ["youtube.com", "youtu.be"]):
            await _summarize_youtube(update, uid, url_found, context)
            return

        page_text = fetch_url_text(url_found)
        if page_text.startswith("ERROR:"):
            page_text = f"Не вдалося відкрити сторінку: {url_found}"
        if task:
            prompt = (
                f"Користувач надіслав посилання: {url_found}\n"
                f"Вміст сторінки: {page_text[:2000]}\n\n"
                f"Задача від користувача: {task}\n\n"
                f"Виконай задачу користувача використовуючи контекст сторінки."
            )
            result = ask_ai(uid, prompt)
            parts = split_long_message(result)
            for i, part in enumerate(parts):
                prefix = f"[{i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
                await update.message.reply_text(f"{prefix}{part}")
        else:
            result = ask_ai(uid, f"Зроби короткий переказ суті цієї сторінки (5-7 речень):\n\n{page_text}")
            parts = split_long_message(result)
            for i, part in enumerate(parts):
                prefix = f"[{i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
                await update.message.reply_text(f"{prefix}{part}")
        return

    # Автовизначення запиту на генерацію зображення
    img_triggers = [
        "намалюй", "згенеруй картинку", "згенеруй фото", "згенеруй зображення",
        "зроби зображення", "зроби фото", "зроби картинку", "хочу фото",
        "хочу картинку", "хочу зображення", "покажи фото", "покажи картинку",
        "створи зображення", "створи картинку", "створи фото",
        "generate image", "draw", "create image", "make image",
        "зобрази", "намали", "зроби малюнок", "хочу малюнок",
        "картинка з", "фото з", "зображення з",
    ]
    # Перевіряємо чи є запит на кілька зображень
    multi_img = any(w in text_lower for w in ["5 фото", "5 картинок", "5 зображень", "кілька фото",
                                               "кілька картинок", "3 фото", "3 картинки", "4 фото"])
    if multi_img and any(w in text_lower for w in ["згенеруй", "зроби", "намалюй", "створи"]):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        count = min(3, 5 if "5" in text_lower else (3 if "3" in text_lower else 3))
        await update.message.reply_text(f"Добре, починаю генерувати {count} зображення. Зачекай приблизно {count * 15} секунд.")
        prompts_raw = ask_ai(uid,
            f"Придумай {count} коротких промптів англійською для генерації зображень. "
            f"Кожен з нового рядка, без нумерації. Запит: {text}"
        )
        prompts = [p.strip() for p in prompts_raw.strip().split("\n") if p.strip()][:count]
        sent = 0
        for prompt in prompts:
            try:
                img = generate_image(prompt)
                if isinstance(img, bytes):
                    buf = io.BytesIO(img); buf.name = "img.jpg"
                    await update.message.reply_photo(photo=buf)
                else:
                    await update.message.reply_photo(photo=img)
                sent += 1
                await asyncio.sleep(1)
            except Exception as e:
                pass
        if sent == 0:
            await update.message.reply_text("Не вдалося згенерувати. Спробуй ще раз.")
        return

    if any(t in text_lower for t in img_triggers):
        # Знаходимо що саме генерувати
        prompt = text
        for t in sorted(img_triggers, key=len, reverse=True):
            if t in text_lower:
                idx = text_lower.find(t)
                prompt = text[idx + len(t):].strip()
                if not prompt:
                    prompt = text
                break
        if prompt and len(prompt) > 3:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
            await update.message.reply_text("Добре, генерую зображення. Зачекай ~15 секунд.")
            try:
                url = generate_image(prompt)
                await update.message.reply_photo(photo=url)
            except Exception as e:
                await update.message.reply_text(f"Помилка: {e}")
            return

    reply = ask_ai(uid, text)
    save_dialog(uid, "assistant", reply)

    # Якщо AI відповів ідеями замість дії — перевіряємо
    reply_lower = reply.lower()
    was_img_request = any(w in text_lower for w in ["згенеруй", "намалюй", "зроби фото", "зроби картинку", "створи зображення"])
    has_only_ideas = ("фотографія" in reply_lower or "ідея" in reply_lower) and was_img_request and len(reply) < 800
    if has_only_ideas:
        # Бот дав ідеї — генеруємо реальні зображення
        prompts_raw = ask_ai(uid,
            f"Придумай 3 промпти для генерації зображень англійською на основі: {text}. "
            f"Кожен з нового рядка, тільки опис, без нумерації."
        )
        prompts = [p.strip() for p in prompts_raw.strip().split("\n") if p.strip()][:3]
        for i, prompt in enumerate(prompts):
            try:
                data = generate_image(prompt)
                if data:
                    buf = io.BytesIO(data); buf.name = "img.jpg"
                    await update.message.reply_photo(photo=buf)
            except:
                pass
        return

    # Розбиваємо якщо відповідь довга
    parts = split_long_message(reply)
    for i, part in enumerate(parts):
        if len(parts) > 1:
            await update.message.reply_text(f"[{i+1}/{len(parts)}]\n\n{part}")
        else:
            await update.message.reply_text(part)

    # Показуємо залишок ліміту якщо мало
    if not is_premium(uid) and uid != ADMIN_ID:
        remaining_after = remaining - 1
        if 0 < remaining_after <= 5:
            await update.message.reply_text(
                f"Залишилось {remaining_after} повідомлень сьогодні. /premium для безліміту"
            )
async def music_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        prompt = " ".join(context.args)
    else:
        user_state[update.effective_user.id] = "music"
        await update.message.reply_text(
            "🎵 Опиши яку музику згенерувати:\n"
            "Наприклад: `relaxing lofi hip hop beats` або `epic orchestral battle music`",
            parse_mode="Markdown"
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_voice")
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    audio_url = f"https://audio.pollinations.ai/{encoded}"
    try:
        r = requests.get(audio_url, timeout=30)
        if r.status_code == 200 and len(r.content) > 1000:
            buf = io.BytesIO(r.content)
            buf.name = "music.mp3"
            await update.message.reply_audio(audio=buf, title=prompt[:50], performer="Mark AI")
        else:
            raise Exception("empty response")
    except Exception:
        # Запасний варіант — посилання на Suno
        suno_url = f"https://suno.com/create?prompt={encoded}"
        await update.message.reply_text(
            f"🎵 Не вдалося згенерувати автоматично.\nВідкрий Suno і натисни Create:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🎵 Відкрити Suno", url=suno_url)
            ]])
        )

async def imagine_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        prompt = " ".join(context.args)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        await update.message.reply_text("Добре, генерую. Зачекай ~10 секунд.")
        img = generate_image(prompt)
        if isinstance(img, bytes):
            buf = io.BytesIO(img); buf.name = "img.jpg"
            await update.message.reply_photo(photo=buf, caption=f"🎨 {prompt[:100]}")
        else:
            await update.message.reply_photo(photo=img, caption=f"🎨 {prompt[:100]}")
    else:
        user_state[update.effective_user.id] = "imagine"
        await update.message.reply_text("🎨 Опиши що намалювати (англійською краще):\nНаприклад: `beautiful sunset over mountains`", parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє отримані фото — розпізнає через AI"""
    uid = update.effective_user.id
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_url = file.file_path

    caption = update.message.caption or ""
    caption_lower = caption.lower()

    # Тригери для генерації/зміни стилю
    gen_triggers = ["згенеруй", "зроби схожі", "намалюй", "зроби такі", "хочу такі",
                    "зроби фото", "зроби картинки", "створи", "generate",
                    "в іншому стилі", "інший стиль", "змін стиль", "але стиль",
                    "трохи інакше", "по-іншому"]
    is_gen_request = any(t in caption_lower for t in gen_triggers)

    if is_gen_request:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        await update.message.reply_text("Добре, аналізую фото і генерую нове. Зачекай ~20 секунд.")

        # Аналізуємо фото — витягуємо текст і стиль
        import re as _re, json as _json
        texts_on_image = []
        orig_style = "anime illustration"
        orig_subject = "people, urban scene"
        try:
            analysis = analyze_image(image_url,
                "Analyze this image and return JSON with these fields:\n"
                "- texts: list of all text/words visible on the image\n"
                "- style: visual style description in English (anime/realistic/cartoon etc)\n"
                "- subject: main subject in English\n"
                "Return ONLY valid JSON, nothing else."
            )
            j_match = _re.search(r'\{.*\}', analysis, _re.DOTALL)
            if j_match:
                j = _json.loads(j_match.group())
                texts_on_image = j.get("texts", [])
                orig_style = j.get("style", orig_style)
                orig_subject = j.get("subject", orig_subject)
        except:
            pass  # Продовжуємо без аналізу

        # Визначаємо новий стиль з підпису
        style_keywords = {
            "реалістичний": "photorealistic",
            "аніме": "anime style",
            "мультяшний": "cartoon style",
            "3d": "3D render",
            "акварель": "watercolor painting",
            "мінімалістичний": "minimalist",
            "темний": "dark dramatic",
            "яскравий": "vibrant colorful",
            "вінтаж": "vintage retro",
            "кіно": "cinematic film",
        }
        new_style = ""
        for uk, en in style_keywords.items():
            if uk in caption_lower:
                new_style = en
                break

        # Якщо стиль не вказаний — просимо AI придумати інший
        if not new_style:
            styles = ["photorealistic", "anime style", "cartoon", "3D render", "watercolor", "cinematic"]
            new_style = random.choice([s for s in styles if s.lower() not in orig_style.lower()])

        # Зберігаємо текст з оригіналу якщо просять
        keep_text = "залиш текст" in caption_lower or "текст залиш" in caption_lower or "той самий текст" in caption_lower

        # Генеруємо нову цитату тільки якщо просять
        new_quote_text = ""
        if any(w in caption_lower for w in ["цитата", "текст", "слова", "напис", "підпис"]):
            new_quote_text = ask_ai(uid,
                f"Придумай одну коротку мотиваційну цитату українською (3-6 слів). "
                f"Тільки сам текст цитати, без лапок, без пояснень, без перекладу. "
                f"Приклад: 'Не зупиняйся ніколи' або 'Дій і перемагай'. "
                f"Тема: '{caption}'."
            )
            # Очищаємо від зайвого
            new_quote_text = new_quote_text.strip().strip('"').strip("'").split('\n')[0][:50]
            texts_on_image = [new_quote_text]
            keep_text = True

        # Будуємо промпт для генерації (окремо від цитати)
        gen_prompt = (
            f"{new_style}, {orig_subject or 'people in urban scene'}, "
            f"highly detailed, sharp, professional quality, cinematic lighting, 8k resolution, "
            f"no text, no watermark, masterpiece"
        )

        # Генеруємо нове зображення
        img_result = generate_image(gen_prompt)

        if isinstance(img_result, bytes):
            img_data = img_result
        else:
            try:
                img_data = requests.get(img_result, timeout=20).content
            except:
                img_data = None

        if not img_data:
            await update.message.reply_text("Не вдалося згенерувати. Спробуй ще раз.")
            return

        if keep_text and texts_on_image:
            try:
                from PIL import Image, ImageDraw, ImageFont, ImageFilter
                import io as _io
                import textwrap as _tw

                img = Image.open(_io.BytesIO(img_data)).convert("RGB")
                img = img.resize((1080, 1080))

                # Красивий градієнт знизу
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                draw_ov = ImageDraw.Draw(overlay)
                for i in range(400):
                    alpha = int(200 * (i / 400) ** 1.5)
                    draw_ov.rectangle([(0, 680 + i), (1080, 681 + i)], fill=(0, 0, 0, alpha))
                img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

                draw = ImageDraw.Draw(img)
                try:
                    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 62)
                    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
                except:
                    font_big = ImageFont.load_default()
                    font_small = font_big

                # Центруємо текст
                full_text = " ".join(texts_on_image[:2])
                wrapped = _tw.fill(full_text, width=22)
                lines = wrapped.split("\n")
                total_h = len(lines) * 75
                y = 1080 - total_h - 60

                for line in lines:
                    # Тінь
                    for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2),(0,3),(3,0)]:
                        draw.text((540 + dx, y + dy), line, font=font_big, fill=(0, 0, 0, 200), anchor="mm")
                    # Основний текст
                    draw.text((540, y), line, font=font_big, fill=(255, 255, 255), anchor="mm")
                    y += 75

                buf = _io.BytesIO()
                img.save(buf, format="JPEG", quality=95)
                buf.seek(0)
                await update.message.reply_photo(photo=buf)
            except Exception as e:
                buf = io.BytesIO(img_data); buf.name = "img.jpg"
                await update.message.reply_photo(photo=buf)
        else:
            buf = io.BytesIO(img_data); buf.name = "img.jpg"
            await update.message.reply_photo(photo=buf)
        return

    # Їжа
    is_food = user_state.get(uid) == "food_photo" or any(
        w in caption_lower for w in ["їжа", "страва", "калорії", "food", "calories", "рецепт"]
    )
    if is_food:
        user_state.pop(uid, None)
        result = analyze_image(image_url,
            "Це фото їжі. Визнач: 1) Назву страви 2) Приблизні калорії на порцію 3) Основні інгредієнти 4) КБЖУ. Відповідай чітко і структуровано."
        )
        await update.message.reply_text(result)
        return

    # Звичайний аналіз
    question = caption if caption else ""
    result = analyze_image(image_url, question)
    await update.message.reply_text(result)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Читає PDF та текстові файли і аналізує через AI"""
    doc = update.message.document
    fname = doc.file_name or ""
    allowed = (".pdf", ".txt", ".py", ".js", ".html", ".css", ".json", ".csv", ".md")

    if not any(fname.lower().endswith(ext) for ext in allowed):
        await update.message.reply_text("❌ Підтримую: PDF, TXT, PY, JS, HTML, CSS, JSON, CSV, MD")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    file = await context.bot.get_file(doc.file_id)
    file_bytes = await file.download_as_bytearray()

    text = ""
    try:
        if fname.lower().endswith(".pdf"):
            import io as _io
            try:
                import pypdf
                reader = pypdf.PdfReader(_io.BytesIO(bytes(file_bytes)))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                await update.message.reply_text("❌ Для PDF потрібен pypdf. Надішли .txt файл.")
                return
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        await update.message.reply_text(f"❌ Не вдалося прочитати файл: {e}")
        return

    if not text.strip():
        await update.message.reply_text("😕 Файл порожній або не вдалося прочитати текст.")
        return

    # Обрізаємо до 4000 символів щоб не перевищити ліміт
    text = text[:4000]
    question = update.message.caption or "Проаналізуй цей файл і коротко опиши що в ньому."
    uid = update.effective_user.id
    reply = ask_ai(uid, f"{question}\n\n---\n{text}")
    await update.message.reply_text(f"📄 *{fname}*\n\n{reply}", parse_mode="Markdown")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Розпізнає голосове повідомлення через Groq Whisper"""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    # Завантажуємо аудіо
    audio_bytes = await file.download_as_bytearray()

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("voice.ogg", bytes(audio_bytes), "audio/ogg"),
        "model": (None, "whisper-large-v3"),
        "language": (None, "uk"),
        "response_format": (None, "text"),
    }
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers, files=files, timeout=30
        )
        r.raise_for_status()
        text = r.text.strip()
        if not text:
            await update.message.reply_text("😕 Не вдалося розпізнати. Спробуй ще раз.")
            return

        await update.message.reply_text(f"🎤 Ти сказав:\n_{text}_\n\n⏳ Думаю...", parse_mode="Markdown")

        # Відповідаємо через AI
        uid = update.effective_user.id
        reply = ask_ai(uid, text)
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"❌ Помилка розпізнавання: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Помилка: {context.error}")

# ══════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════
if __name__ == "__main__":
    # Примусово скидаємо всі попередні сесії
    try:
        requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook",
            params={"drop_pending_updates": "true"},
            timeout=10
        )
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/close",
            timeout=10
        )
        import time
        time.sleep(3)
    except:
        pass

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    commands = [
        ("start", start), ("help", help_cmd), ("weather", weather_cmd),
        ("news", news_cmd), ("currency", currency_cmd), ("crypto", crypto_cmd),
        ("translate", translate_cmd), ("joke", joke_cmd), ("fact", fact_cmd),
        ("motivate", motivate_cmd), ("horoscope", horoscope_cmd),
        ("note", note_cmd), ("notes", notes_cmd), ("clearnotes", clearnotes_cmd),
        ("task", task_cmd), ("tasks", tasks_cmd), ("done", done_cmd), ("deltask", deltask_cmd),
        ("calc", calc_cmd), ("wiki", wiki_cmd), ("qr", qr_cmd),
        ("short", short_cmd), ("ip", ip_cmd), ("remind", remind_cmd),
        ("stats", stats_cmd), ("clear", clear_cmd),
        ("guess", guess_cmd), ("dice", dice_cmd), ("coin", coin_cmd),
        ("imagine", imagine_cmd), ("ref", ref_cmd), ("premium", premium_cmd),
        ("music", music_cmd), ("admin", admin_cmd), ("lang", lang_cmd),
        ("password", password_cmd), ("mood", mood_cmd), ("convert", convert_cmd),
        ("search", search_cmd), ("cheatsheet", cheatsheet_cmd), ("grammar", grammar_cmd),
        ("post", post_cmd), ("idea", idea_cmd), ("expense", expense_cmd), ("quiz", quiz_cmd),
        ("compat", compat_cmd), ("schedule", schedule_cmd),
        ("schedule_add", schedule_add_cmd), ("meme", meme_cmd),
        ("pomodoro", pomodoro_cmd), ("nickname", nickname_cmd),
        ("checksite", checksite_cmd), ("summarize", summarize_cmd), ("synonyms", synonyms_cmd),
        ("food", food_cmd), ("memory", memory_cmd), ("forget", forget_cmd),
        ("code", code_cmd), ("users", users_cmd), ("deep", deep_cmd),
        ("url", url_cmd), ("debate", debate_cmd), ("leaderboard", leaderboard_cmd),
        ("diary", diary_cmd), ("habits", habits_cmd), ("digest", digest_cmd), ("cv", cv_cmd),
        ("quote", quote_cmd), ("comic", comic_cmd),
        ("youtube", youtube_cmd), ("calories", calories_cmd), ("calories_today", calories_today_cmd),
        ("tiktok", tiktok_post_cmd), ("mbti", mbti_cmd), ("persona", persona_cmd),
        ("teach", teach_cmd), ("ad", ad_cmd), ("rstats", realtime_stats_cmd),
    ]
    for cmd, handler in commands:
        app.add_handler(CommandHandler(cmd, handler))

    app.add_handler(CallbackQueryHandler(translate_callback, pattern="^tr\\|"))
    app.add_handler(CallbackQueryHandler(horoscope_callback, pattern="^hs\\|"))
    app.add_handler(CallbackQueryHandler(crypto_callback,    pattern="^crypto\\|"))
    app.add_handler(CallbackQueryHandler(game_callback,      pattern="^game\\|"))
    app.add_handler(CallbackQueryHandler(rps_callback,       pattern="^rps\\|"))
    app.add_handler(CallbackQueryHandler(buy_callback,        pattern="^buy\\|"))
    app.add_handler(CallbackQueryHandler(lang_callback,        pattern="^lang\\|"))
    app.add_handler(CallbackQueryHandler(admin_callback,       pattern="^admin\\|"))
    app.add_handler(CallbackQueryHandler(pwd_callback,         pattern="^pwd\\|"))
    app.add_handler(CallbackQueryHandler(conv_callback,        pattern="^conv\\|"))
    app.add_handler(CallbackQueryHandler(post_callback,        pattern="^post\\|"))
    app.add_handler(CallbackQueryHandler(exp_clear_callback,   pattern="^exp_clear\\|"))
    app.add_handler(CallbackQueryHandler(quiz_callback,        pattern="^quiz\\|\\d"))
    app.add_handler(CallbackQueryHandler(quiz_next_callback,   pattern="^quiz_next$"))
    app.add_handler(CallbackQueryHandler(compat1_callback,     pattern="^compat1\\|"))
    app.add_handler(CallbackQueryHandler(compat2_callback,     pattern="^compat2\\|"))
    app.add_handler(CallbackQueryHandler(pomo_callback,        pattern="^pomo\\|"))
    app.add_handler(CallbackQueryHandler(nick_callback,        pattern="^nick\\|"))
    app.add_handler(CallbackQueryHandler(code_lang_callback,   pattern="^code\\|"))
    app.add_handler(CallbackQueryHandler(diary_callback,        pattern="^diary\\|"))
    app.add_handler(CallbackQueryHandler(habits_callback,       pattern="^habit\\|"))
    app.add_handler(CallbackQueryHandler(digest_callback,       pattern="^digest\\|"))
    app.add_handler(CallbackQueryHandler(mbti_callback,         pattern="^mbti\\|"))
    app.add_handler(CallbackQueryHandler(persona_callback,      pattern="^persona\\|"))
    app.add_handler(CallbackQueryHandler(ad_callback,           pattern="^ad\\|"))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    from telegram.ext import PreCheckoutQueryHandler
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)

    print("🤖 Марк запущено! Ctrl+C щоб зупинити.")

    # Скидаємо попередні сесії
    try:
        import urllib.request
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true",
            timeout=5
        )
    except:
        pass

    # Фонова задача щоденного дайджесту
    async def daily_digest_task():
        while True:
            try:
                now = datetime.now()
                settings = load_digest_settings()
                for uid_str, cfg in settings.items():
                    if not cfg.get("enabled"):
                        continue
                    hour = cfg.get("hour", 8)
                    last_sent = cfg.get("last_sent", "")
                    today = now.strftime("%Y-%m-%d")
                    if now.hour == hour and last_sent != today:
                        try:
                            uid_int = int(uid_str)
                            city = cfg.get("city", "Київ")
                            weather = get_weather(city)
                            news = get_news()
                            motiv = random.choice(MOTIVATIONS)
                            msg = (
                                f"Доброго ранку! Твій дайджест на {today}:\n\n"
                                f"Погода: {weather}\n\n"
                                f"Новини:\n{news[:500]}\n\n"
                                f"{motiv}"
                            )
                            await app.bot.send_message(chat_id=uid_int, text=msg)
                            settings[uid_str]["last_sent"] = today
                            save_digest_settings(settings)
                        except:
                            pass
            except:
                pass
            # Авторозсилка реклами о 12:00
            try:
                if now.hour == 12 and now.minute == 0:
                    ad_file = "ad_auto.json"
                    if os.path.exists(ad_file):
                        ad_data = json.load(open(ad_file, encoding='utf-8'))
                        if ad_data.get("enabled") and ad_data.get("last_sent") != today:
                            users = json.load(open(USERS_FILE, encoding='utf-8')) if os.path.exists(USERS_FILE) else {}
                            for uid_str in users:
                                try:
                                    await app.bot.send_message(chat_id=int(uid_str), text=f"📢 {ad_data['text']}")
                                    await asyncio.sleep(0.05)
                                except:
                                    pass
                            ad_data["last_sent"] = today
                            json.dump(ad_data, open(ad_file, 'w', encoding='utf-8'), ensure_ascii=False)
            except:
                pass
            await asyncio.sleep(60)

    asyncio.get_event_loop().create_task(daily_digest_task())

    app.run_polling(drop_pending_updates=True)
