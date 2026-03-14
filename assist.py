import os
import pyttsx3
import wikipediaapi
import psutil
import pyautogui
import webbrowser
import json
import random
import requests
import threading
import time
import subprocess
import feedparser
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DIALOG_FILE = "dialog_history.json"
chat_history = []

def save_dialog(role, text):
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "role": role,
        "text": text
    }
    history = []
    if os.path.exists(DIALOG_FILE):
        try:
            with open(DIALOG_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []
    history.append(entry)
    with open(DIALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def ask_ai(message):
    save_dialog("user", message)
    try:
        chat_history.append({"role": "user", "content": message})
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        messages = [
            {"role": "system", "content": (
                "Ти — Марк, просунутий персональний AI-асистент. "
                "Ти розумний, лаконічний і маєш почуття гумору. "
                "Відповідай українською мовою. "
                "Можеш писати код, пояснювати теми, допомагати з задачами, "
                "перекладати, аналізувати тексти, генерувати ідеї — все що попросять."
            )}
        ] + chat_history[-20:]  # зберігаємо останні 20 повідомлень
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        r = requests.post(GROQ_URL, headers=headers, json=data, timeout=15)
        result = r.json()
        if "choices" in result:
            reply = result["choices"][0]["message"]["content"]
            chat_history.append({"role": "assistant", "content": reply})
            save_dialog("assistant", reply)
            return reply
        return f"Помилка API: {result.get('error', {}).get('message', str(result))}"
    except Exception as e:
        return f"AI недоступний: {e}"

def clear_chat_history():
    chat_history.clear()

def banner():
    print(Fore.CYAN + Style.BRIGHT + """
  ███╗   ███╗ █████╗ ██████╗ ██╗  ██╗     █████╗ ██╗
  ████╗ ████║██╔══██╗██╔══██╗██║ ██╔╝    ██╔══██╗██║
  ██╔████╔██║███████║██████╔╝█████╔╝     ███████║██║
  ██║╚██╔╝██║██╔══██║██╔══██╗██╔═██╗     ██╔══██║██║
  ██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██╗    ██║  ██║██║
  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝  ╚═╝╚═╝
    """ + Fore.WHITE + "         Персональний AI-асистент v2.0\n")

def divider():
    print(Fore.BLUE + "─" * 55)

_anim_running = False

def run_cat_animation():
    """Котик бігає по рядку поки думає"""
    global _anim_running
    cat = "=^.^="
    width = 50
    pos = 0
    direction = 1
    while _anim_running:
        line = " " * pos + Fore.YELLOW + cat
        print(f"\r{line:<{width + 5}}", end="", flush=True)
        pos += direction
        if pos >= width - len(cat):
            direction = -1
        if pos <= 0:
            direction = 1
        time.sleep(0.07)
    print(f"\r{' ' * (width + 10)}\r", end="", flush=True)

def thinking_start():
    global _anim_running
    _anim_running = True
    t = threading.Thread(target=run_cat_animation, daemon=True)
    t.start()
    return t

def thinking_stop():
    global _anim_running
    _anim_running = False
    time.sleep(0.1)

def status_bar():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    now = datetime.now().strftime('%H:%M:%S')
    bar = (
        Fore.BLUE + "─" * 55 + "\n" +
        Fore.WHITE + "  🕐 " + Fore.YELLOW + now +
        Fore.WHITE + "   💻 CPU: " + Fore.GREEN + f"{cpu}%" +
        Fore.WHITE + "   🧠 RAM: " + Fore.MAGENTA + f"{ram}%" +
        "\n" + Fore.BLUE + "─" * 55
    )
    print(bar)


NOTES_FILE = "notes.txt"
TASKS_FILE = "tasks.json"
USER_FILE = "user.json"

session_stats = {"commands": 0, "start": datetime.now()}

JOKES = [
    "Чому програмісти не люблять природу? Там забагато багів.",
    "Скільки програмістів треба щоб замінити лампочку? Жодного — це апаратна проблема.",
    "Оптиміст каже: склянка наполовину повна. Програміст каже: буфер вдвічі більший ніж треба.",
    "Чому Java-розробники носять окуляри? Бо не бачать C#.",
    "99 маленьких багів у коді. Виправив один — 127 маленьких багів у коді.",
]

FACTS = [
    "Восьминоги мають три серця і блакитну кров.",
    "Мед ніколи не псується — в єгипетських пірамідах знайшли їстівний мед віком 3000 років.",
    "Банани радіоактивні через вміст калію-40.",
    "Блискавка вдаряє в Землю близько 100 разів на секунду.",
    "Людський мозок генерує близько 70 000 думок на день.",
    "Мурахи ніколи не сплять і не мають легень.",
    "Акули старіші за дерева — вони існують вже 450 мільйонів років.",
]

MOOD_RESPONSES = {
    "чудово": ["Це круто! Продуктивного дня, заряджай на повну!", "Відмінно! Такий настрій — половина успіху."],
    "добре": ["Добре — вже непогано. Головне не зупинятися!", "Стабільно добре — це теж результат."],
    "нормально": ["Нормально — значить є куди рости. Тримайся!", "Буває. Головне що ти тут і рухаєшся вперед."],
    "погано": ["Шкода чути. Зроби паузу, випий чаю — все мине.", "Важкі дні бувають у всіх. Ти впораєшся."],
    "жахливо": ["Ой. Це серйозно. Відпочинь, не тягни все на собі.", "Такі дні теж проходять. Я поруч, якщо треба."],
}

# ================= ГОЛОС =================
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 180)
    for voice in engine.getProperty('voices'):
        if "ukrainian" in voice.name.lower() or "uk" in voice.id.lower():
            engine.setProperty('voice', voice.id)
            break
except Exception as e:
    print(f"Помилка звуку: {e}")

wiki = wikipediaapi.Wikipedia(language='uk', user_agent="MarkBot/5.0")

def speak(text):
    print(Fore.CYAN + Style.BRIGHT + " 🤖 " + Fore.WHITE + text)
    save_dialog("assistant", text)
    try:
        engine.say(text)
        engine.runAndWait()
    except:
        pass

def info(text):
    print(Fore.BLUE + " ℹ  " + Fore.WHITE + text)

def success(text):
    print(Fore.GREEN + " ✔  " + Fore.WHITE + text)

def warn(text):
    print(Fore.YELLOW + " ⚠  " + Fore.WHITE + text)

# ================= КОРИСТУВАЧ =================
def load_user():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user(data):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_data = load_user()

# ================= НОТАТКИ =================
def save_note(text):
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d')}] {text}\n")

def read_notes():
    if not os.path.exists(NOTES_FILE):
        return "Нотатки порожні."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return content if content else "Нотатки порожні."

def clear_notes():
    open(NOTES_FILE, "w").close()

# ================= ЗАДАЧІ =================
def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def add_task(text):
    tasks = load_tasks()
    tasks.append({"text": text, "done": False})
    save_tasks(tasks)

def show_tasks():
    tasks = load_tasks()
    if not tasks:
        return "Список задач порожній."
    lines = []
    for i, t in enumerate(tasks, 1):
        mark = Fore.GREEN + "✓" if t["done"] else Fore.YELLOW + "○"
        lines.append(f"  {Fore.WHITE}{i}. [{mark}{Fore.WHITE}] {t['text']}")
    return "\n".join(lines)

def done_task(n):
    tasks = load_tasks()
    if 1 <= n <= len(tasks):
        tasks[n-1]["done"] = True
        save_tasks(tasks)
        return f"Задачу {n} відмічено як виконану."
    return "Задачу не знайдено."

def delete_task(n):
    tasks = load_tasks()
    if 1 <= n <= len(tasks):
        removed = tasks.pop(n-1)
        save_tasks(tasks)
        return f"Задачу '{removed['text']}' видалено."
    return "Задачу не знайдено."

# ================= ІНШІ ФУНКЦІЇ =================
def get_weather(city):
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3&lang=uk", timeout=5)
        return r.text.strip() if r.status_code == 200 else "Не вдалося отримати погоду."
    except:
        return "Немає з'єднання з інтернетом."

def calculate(expr):
    try:
        safe = ''.join(c for c in expr if c in '0123456789+-*/(). ')
        return f"Результат: {eval(safe)}"
    except:
        return "Не можу порахувати. Перевір вираз."

def check_mood(name):
    print(f"[Mark AI]: Як твій настрій сьогодні, {name}?")
    print("  1 - чудово  2 - добре  3 - нормально  4 - погано  5 - жахливо")
    choice = input("Твій вибір: ").strip()
    moods = {"1": "чудово", "2": "добре", "3": "нормально", "4": "погано", "5": "жахливо"}
    mood = moods.get(choice, "нормально")
    speak(random.choice(MOOD_RESPONSES[mood]))

def set_reminder(text, seconds):
    def _remind():
        time.sleep(seconds)
        speak(f"Нагадування: {text}")
    threading.Thread(target=_remind, daemon=True).start()

def search_wiki(topic):
    page = wiki.page(topic)
    return page.summary[:400] if page.exists() else f"Нічого не знайдено про '{topic}'."

def get_battery():
    try:
        b = psutil.sensors_battery()
        if b:
            status = "заряджається" if b.power_plugged else "розряджається"
            return f"Батарея: {int(b.percent)}%, {status}."
        return "Інформація про батарею недоступна."
    except:
        return "Не вдалося отримати дані батареї."

def open_folder(path):
    try:
        target = path if os.path.isabs(path) else os.path.expanduser(f"~/{path}")
        subprocess.Popen(f'explorer "{target}"')
        return f"Відкриваю папку: {target}"
    except:
        return "Не вдалося відкрити папку."

def get_news():
    try:
        feed = feedparser.parse("https://www.ukrinform.ua/rss/block-lastnews")
        if feed.entries:
            top = feed.entries[:3]
            lines = [f"{i+1}. {e.title}" for i, e in enumerate(top)]
            return "\n".join(lines)
        return "Новини недоступні."
    except:
        return "Не вдалося завантажити новини."

def type_text(text):
    try:
        time.sleep(1)
        pyautogui.typewrite(text, interval=0.05)
        return "Текст надруковано."
    except:
        return "Не вдалося надрукувати текст."

def lock_screen():
    try:
        subprocess.run("rundll32.exe user32.dll,LockWorkStation")
        return "Екран заблоковано."
    except:
        return "Не вдалося заблокувати екран."

def guess_game():
    number = random.randint(1, 100)
    speak("Я загадав число від 1 до 100. Вгадуй!")
    attempts = 0
    while True:
        try:
            guess = int(input("Твоя спроба: ").strip())
            attempts += 1
            if guess < number:
                speak("Більше!")
            elif guess > number:
                speak("Менше!")
            else:
                speak(f"Правильно! Ти вгадав за {attempts} спроб.")
                break
        except:
            speak("Введи число.")

def session_info():
    elapsed = datetime.now() - session_stats["start"]
    mins = int(elapsed.total_seconds() // 60)
    secs = int(elapsed.total_seconds() % 60)
    return f"Сесія: {mins} хв {secs} сек. Команд виконано: {session_stats['commands']}."

def show_help():
    cmds = [
        ("привіт",                        "вітання"),
        ("час / дата",                    "час і дата"),
        ("погода [місто]",                "погода"),
        ("новини",                        "останні новини"),
        ("знайди / гугл [запит]",         "пошук Google"),
        ("ютуб [запит]",                  "пошук YouTube"),
        ("музика [назва]",                "відкрити пісню на YouTube"),
        ("що таке / розкажи про [тема]",  "Вікіпедія"),
        ("порахуй [вираз]",               "калькулятор"),
        ("запиши [текст]",                "нотатка"),
        ("нотатки / очисти нотатки",      "нотатки"),
        ("задача [текст]",                "додати задачу"),
        ("задачі",                        "список задач"),
        ("виконано [N]",                  "відмітити задачу"),
        ("видали задачу [N]",             "видалити задачу"),
        ("нагадай через [N] хвилин [текст]", "нагадування"),
        ("настрій",                       "перевірка настрою"),
        ("жарт / факт",                   "жарт або факт"),
        ("скрін",                         "знімок екрана"),
        ("статус",                        "CPU і RAM"),
        ("батарея",                       "заряд батареї"),
        ("відкрий папку [шлях]",          "відкрити папку"),
        ("надрукуй [текст]",              "друкує текст"),
        ("заблокуй",                      "блокування екрана"),
        ("вгадай число",                  "міні-гра"),
        ("сесія",                         "статистика сесії"),
        ("очисти чат",                    "скинути пам'ять розмови"),
        ("вихід",                         "завершити роботу"),
    ]
    divider()
    print(Fore.CYAN + Style.BRIGHT + "  ДОСТУПНІ КОМАНДИ")
    divider()
    for cmd, desc in cmds:
        print(f"  {Fore.YELLOW}{cmd:<40}{Fore.WHITE}{desc}")
    divider()

# ================= ОСНОВНИЙ ЦИКЛ =================
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner()
    status_bar()

    if "name" not in user_data:
        speak("Система активована. Як мені до тебе звертатися?")
        name = input(Fore.GREEN + "  Введи ім'я: " + Fore.WHITE).strip()
        user_data["name"] = name
        save_user(user_data)
        speak(f"Приємно познайомитися, {name}. Я готовий. Напиши 'допомога' щоб побачити команди.")
    else:
        name = user_data["name"]
        speak(f"Привіт, {name}! Як справи? З чим можу допомогти?")

    divider()

    while True:
        try:
            cmd = input(f"\n{Fore.GREEN}[{datetime.now().strftime('%H:%M')}] {name}: {Fore.WHITE}").lower().strip()
            if not cmd:
                continue

            session_stats["commands"] += 1
            save_dialog("user", cmd)
            thinking_start()
            time.sleep(0.4)
            thinking_stop()

            if any(w in cmd for w in ["вихід", "стоп", "бувай"]):
                speak("Вимикаюся. Гарного дня!")
                break

            elif any(w in cmd for w in ["привіт", "хай", "здрастуй"]):
                speak(f"Привіт, {name}! Чим можу допомогти?")

            elif cmd in ["допомога", "help", "команди", "що ти вмієш", "які функції", "що ти можеш", "можливості", "функції"]:
                show_help()

            elif "час" in cmd or "година" in cmd:
                speak(f"Зараз {datetime.now().strftime('%H:%M:%S')}")

            elif "дата" in cmd:
                speak(f"Сьогодні {datetime.now().strftime('%d.%m.%Y')}")

            elif "погода" in cmd:
                city = cmd.replace("погода", "").strip() or "Kyiv"
                speak(get_weather(city))

            elif "новини" in cmd:
                news = get_news()
                info("Останні новини:")
                print(Fore.WHITE + news)

            elif "порахуй" in cmd:
                expr = cmd.replace("порахуй", "").strip()
                speak(calculate(expr))

            elif "жарт" in cmd:
                speak(random.choice(JOKES))

            elif "факт" in cmd:
                speak(random.choice(FACTS))

            elif "нагадай" in cmd:
                try:
                    parts = cmd.split()
                    idx = next(i for i, p in enumerate(parts) if p.startswith("хвилин"))
                    minutes = int(parts[idx - 1])
                    text = " ".join(parts[idx + 1:]) or "час!"
                    set_reminder(text, minutes * 60)
                    speak(f"Нагадаю через {minutes} хвилин: {text}")
                except:
                    speak("Спробуй: нагадай через 5 хвилин [текст]")

            elif "музика" in cmd:
                query = cmd.replace("музика", "").strip()
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                speak(f"Відкриваю музику: {query}")

            elif "гугл" in cmd or "знайди" in cmd:
                search = cmd.replace("гугл", "").replace("знайди", "").strip()
                webbrowser.open(f"https://www.google.com/search?q={search}")
                speak(f"Відкриваю пошук для {search}")

            elif "ютуб" in cmd:
                search = cmd.replace("ютуб", "").strip()
                webbrowser.open(f"https://www.youtube.com/results?search_query={search}")
                speak(f"Відкриваю YouTube для {search}")

            elif "скрін" in cmd or "знімок" in cmd:
                path = f"screen_{datetime.now().strftime('%H%M%S')}.png"
                pyautogui.screenshot(path)
                speak(f"Знімок збережено як {path}")

            elif "статус" in cmd:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                speak(f"Процесор: {cpu}%. Пам'ять: {ram}%.")

            elif "батарея" in cmd:
                speak(get_battery())

            elif "відкрий папку" in cmd:
                path = cmd.replace("відкрий папку", "").strip() or ""
                speak(open_folder(path))

            elif "надрукуй" in cmd:
                text = cmd.replace("надрукуй", "").strip()
                speak(f"Друкую: {text}")
                type_text(text)

            elif "заблокуй" in cmd:
                speak(lock_screen())

            elif "вгадай число" in cmd:
                guess_game()

            elif "сесія" in cmd:
                speak(session_info())

            elif "запиши" in cmd or "нотатка" in cmd:
                note = cmd.replace("запиши", "").replace("нотатка", "").strip()
                if note:
                    save_note(note)
                    speak(f"Записав: {note}")
                else:
                    speak("Що записати? Скажи: запиши [текст]")

            elif "нотатки" in cmd or "що записано" in cmd:
                notes = read_notes()
                info("Твої нотатки 📝:")
                print(Fore.WHITE + notes)

            elif "очисти нотатки" in cmd:
                clear_notes()
                success("Нотатки очищено.")

            elif "задача " in cmd:
                text = cmd.replace("задача", "").strip()
                add_task(text)
                speak(f"Задачу додано: {text}")

            elif "задачі" in cmd:
                tasks = show_tasks()
                info("Твої задачі 📋:")
                print(tasks)

            elif "виконано" in cmd:
                try:
                    n = int(''.join(filter(str.isdigit, cmd)))
                    speak(done_task(n))
                except:
                    speak("Вкажи номер задачі: виконано 1")

            elif "видали задачу" in cmd:
                try:
                    n = int(''.join(filter(str.isdigit, cmd)))
                    speak(delete_task(n))
                except:
                    speak("Вкажи номер задачі: видали задачу 1")

            elif "настрій" in cmd:
                check_mood(name)

            elif "очисти чат" in cmd:
                clear_chat_history()
                success("Історію розмови очищено.")

            elif "що таке" in cmd or "хто такий" in cmd or "розкажи про" in cmd:
                topic = cmd.replace("що таке", "").replace("хто такий", "").replace("розкажи про", "").strip()
                result = search_wiki(topic)
                if "Нічого не знайдено" in result:
                    speak(ask_ai(cmd))
                else:
                    speak(result)

            else:
                answer = ask_ai(cmd)
                speak(answer)

        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f" ✖  Помилка: {e}")
            speak("Сталася помилка в системі.")

if __name__ == "__main__":
    main()
