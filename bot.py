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
TELEGRAM_TOKEN = "8252626800:AAEKP5lYp1BhkJIbZ7_SQIhu1GQM3idjFuQ"
GROQ_API_KEY   = "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"
GROQ_URL       = "https://api.groq.com/openai/v1/chat/completions"
DIALOG_FILE    = "dialog_history.json"
NOTES_FILE     = "notes_tg.txt"
TASKS_FILE     = "tasks_tg.json"
USERS_FILE     = "users_tg.json"
REFS_FILE      = "refs_tg.json"
PREMIUM_FILE   = "premium_tg.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Стани та дані в пам'яті
user_histories : dict[int, list]  = {}
user_state     : dict[int, str]   = {}
guess_games    : dict[int, dict]  = {}   # {user_id: {number, attempts}}
user_profiles  : dict[int, dict]  = {}

# ══════════════════════════════════════
#  КОНТЕНТ
# ══════════════════════════════════════
SYSTEM_PROMPT = """Ти — Марк, геніальний AI-асистент з рівнем інтелекту як у Нікола Тесли, Айнштайна і Стіва Джобса разом.

Твій характер:
• Ти надзвичайно розумний, глибокий і проникливий
• Даєш точні, вичерпні та геніальні відповіді
• Мислиш нестандартно і знаходиш неочевидні рішення
• Пояснюєш складні речі просто і зрозуміло
• Маєш енциклопедичні знання в усіх сферах

Правила відповідей:
• Відповідай ВИКЛЮЧНО українською мовою
• Використовуй емодзі ПОМІРНО — лише 1-2 де дійсно доречно, не в кожному реченні
• Для коду — давай чіткий робочий приклад з поясненням
• Складні теми розбивай на кроки
• Якщо не знаєш — чесно скажи і запропонуй альтернативу
• Будь дружнім але не надмірно емоційним
• Відповіді мають бути змістовними, точними і корисними"""

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
    ["💪 Мотивація", "📊 Статистика","❓ Допомога"],
    ["➡️ Ще функції"],
], resize_keyboard=True)

PAGE2_KB = ReplyKeyboardMarkup([
    ["⭐ Купити Преміум", "👥 Реферали"],
    ["📊 Мій статус",    "🔗 Моє посилання"],
    ["⬅️ Назад"],
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
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:],
        "temperature": 0.8,
        "max_tokens": 1500,
    }
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        if len(history) > 40:
            user_histories[user_id] = history[-40:]
        return reply
    except Exception as e:
        return f"😴 AI тимчасово недоступний. Спробуй ще раз! ({e})"

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
    if uid not in users:
        users[uid] = {
            "name": user.first_name,
            "username": user.username,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

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

def generate_image(prompt: str) -> str:
    """Генерує зображення через Pollinations AI — повертає URL"""
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&enhance=true"

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

def shorten_url(url: str) -> str:
    try:
        r = requests.get(f"https://tinyurl.com/api-create.php?url={url}", timeout=6)
        if r.status_code == 200 and r.text.startswith("http"):
            return f"🔗 Коротке посилання:\n{r.text}"
        return "❌ Не вдалося скоротити посилання."
    except:
        return "❌ Помилка скорочення посилання."

# ══════════════════════════════════════
#  НОТАТКИ
# ══════════════════════════════════════
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
        f"👥 *Реферальна система*\n\n"
        f"Твоє посилання:\n`{link}`\n\n"
        f"Запрошено друзів: *{count}*\n"
        f"{prem_text}{next_reward}\n\n"
        f"3 друзі = Преміум 7 днів\n"
        f"10 друзів = Преміум 30 днів",
        parse_mode="Markdown"
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
    register_user(update.effective_user)
    uid = update.effective_user.id

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
    await update.message.reply_text(
        f"👋 Привіт, *{name}*\\! Я *Марк* — твій розумний AI\\-асистент 🤖✨\n\n"
        f"🧠 Відповім на будь\\-яке питання\n"
        f"💻 Напишу код будь\\-якою мовою\n"
        f"🌤 Покажу погоду та новини\n"
        f"📝 Збережу нотатки та задачі\n"
        f"💱 Конвертую валюти та крипту\n"
        f"🎲 Розважу іграми\n\n"
        f"Просто напиши або обери кнопку 👇",
        parse_mode="MarkdownV2",
        reply_markup=MAIN_KB
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Команди Марка:*\n\n"
        "🌤 /weather \\[місто\\] — погода\n"
        "📰 /news — новини\n"
        "💱 /currency 100 USD UAH — валюта\n"
        "₿ /crypto — ціна криптовалюти\n"
        "🌐 /translate \\[текст\\] — переклад\n"
        "😂 /joke — жарт\n"
        "🧠 /fact — факт\n"
        "💪 /motivate — мотивація\n"
        "🔮 /horoscope \\[знак\\] — гороскоп\n"
        "📝 /note \\[текст\\] — нотатка\n"
        "📋 /notes — переглянути нотатки\n"
        "🗑 /clearnotes — очистити нотатки\n"
        "✅ /task \\[текст\\] — задача\n"
        "📋 /tasks — список задач\n"
        "✔ /done \\[N\\] — виконати задачу\n"
        "❌ /deltask \\[N\\] — видалити задачу\n"
        "🧮 /calc \\[вираз\\] — калькулятор\n"
        "📖 /wiki \\[тема\\] — Вікіпедія\n"
        "📷 /qr \\[текст\\] — QR\\-код\n"
        "🔗 /short \\[url\\] — скоротити посилання\n"
        "🌍 /ip \\[адреса\\] — інфо про IP\n"
        "⏰ /remind \\[хв\\] \\[текст\\] — нагадування\n"
        "🎲 /guess — вгадай число\n"
        "🎲 /dice — кубик\n"
        "🪙 /coin — монетка\n"
        "📊 /stats — статистика\n"
        "🗑 /clear — очистити пам'ять AI\n\n"
        "💬 Або просто напиши — відповім\\! 🤖"
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=MAIN_KB)

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
    await update.message.reply_text(
        f"📊 *Статистика {name}:*\n\n"
        f"💬 Повідомлень до AI: {msgs}\n"
        f"✅ Задач виконано: {done}/{len(tasks)}\n"
        f"📝 Нотаток: {notes}\n"
        f"🧠 Повідомлень у пам'яті: {mem}/40",
        parse_mode="Markdown"
    )

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

    if text == "🔮 Гороскоп":
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
    if state == "wiki":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text(search_wiki(text), parse_mode="Markdown")
        return
    if state == "qr":
        buf = generate_qr(text)
        await update.message.reply_photo(photo=buf, caption="📷 QR-код готовий ✅")
        return
    if state == "imagine":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        url = generate_image(text)
        await update.message.reply_photo(photo=url, caption=f"🎨 *{text}*", parse_mode="Markdown")
        return
    if state == "music":
        import urllib.parse
        encoded = urllib.parse.quote(text)
        audio_url = f"https://audio.pollinations.ai/{encoded}"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_voice")
        await update.message.reply_text("🎵 Генерую музику, зачекай...")
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

    # --- AI відповідь ---
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    save_dialog(uid, "user", text)
    reply = ask_ai(uid, text)
    save_dialog(uid, "assistant", reply)
    await update.message.reply_text(reply)

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
    await update.message.reply_text("🎵 Генерую музику, зачекай...")
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
        url = generate_image(prompt)
        await update.message.reply_photo(photo=url, caption=f"🎨 *{prompt}*", parse_mode="Markdown")
    else:
        user_state[update.effective_user.id] = "imagine"
        await update.message.reply_text("🎨 Опиши що намалювати (англійською краще):\nНаприклад: `beautiful sunset over mountains`", parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє отримані фото — розпізнає через AI"""
    uid = update.effective_user.id
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Отримуємо файл
    photo = update.message.photo[-1]  # найбільша якість
    file = await context.bot.get_file(photo.file_id)
    image_url = file.file_path

    question = update.message.caption or ""
    await update.message.reply_text("🔍 Аналізую зображення...")
    result = analyze_image(image_url, question)
    await update.message.reply_text(f"🖼 Аналіз зображення:\n\n{result}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Читає PDF та текстові файли і аналізує через AI"""
    doc = update.message.document
    fname = doc.file_name or ""
    allowed = (".pdf", ".txt", ".py", ".js", ".html", ".css", ".json", ".csv", ".md")

    if not any(fname.lower().endswith(ext) for ext in allowed):
        await update.message.reply_text("❌ Підтримую: PDF, TXT, PY, JS, HTML, CSS, JSON, CSV, MD")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.message.reply_text("📄 Читаю файл...")

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
    await update.message.reply_text("🎤 Розпізнаю голос...")

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
        ("music", music_cmd),
    ]
    for cmd, handler in commands:
        app.add_handler(CommandHandler(cmd, handler))

    app.add_handler(CallbackQueryHandler(translate_callback, pattern="^tr\\|"))
    app.add_handler(CallbackQueryHandler(horoscope_callback, pattern="^hs\\|"))
    app.add_handler(CallbackQueryHandler(crypto_callback,    pattern="^crypto\\|"))
    app.add_handler(CallbackQueryHandler(game_callback,      pattern="^game\\|"))
    app.add_handler(CallbackQueryHandler(rps_callback,       pattern="^rps\\|"))
    app.add_handler(CallbackQueryHandler(buy_callback,        pattern="^buy\\|"))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    from telegram.ext import PreCheckoutQueryHandler
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)

    print("🤖 Марк запущено! Ctrl+C щоб зупинити.")
    app.run_polling(drop_pending_updates=True)
