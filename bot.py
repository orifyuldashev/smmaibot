import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

from dotenv import load_dotenv
from openai import OpenAI

# ========= LOAD ENV =========
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID_STR = os.getenv("ADMIN_ID")

# Короткая проверка всех ключей
if not all([BOT_TOKEN, OPENAI_API_KEY, ADMIN_ID_STR]):
    raise ValueError("❌ .env faylida ma'lumotlar yetishmayapti!")

try:
    ADMIN_ID = int(ADMIN_ID_STR)
except ValueError:
    raise ValueError("❌ ADMIN_ID faqat son bo'lishi kerak!")

# ========= INIT =========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
client = OpenAI(api_key=OPENAI_API_KEY)

# ========= DATABASE (Пример) =========
db = sqlite3.connect("bot_database.db")
cursor = db.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT, 
        joined_at TEXT
    )
""")
db.commit()


# ========= INIT =========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
client = OpenAI(api_key=OPENAI_API_KEY)

# ========= MEMORY =========
user_state = {}
user_memory = {}

# ========= DATABASE =========
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    last_seen TEXT
)
""")
conn.commit()

def save_user(user):
    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, full_name, last_seen)
    VALUES (?, ?, ?)
    """, (user.id, user.full_name, datetime.now().isoformat()))
    conn.commit()

# ========= KEYBOARD =========
kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(
    KeyboardButton("📊 Bepul analiz"),
    KeyboardButton("💰 Narx"),
    KeyboardButton("📞 Aloqa")
)

# ========= AI =========
def ai_reply(user_id, text):
    try:
        if user_id not in user_memory:
            user_memory[user_id] = []

        user_memory[user_id].append({"role": "user", "content": text})

        messages = [
    {
"role": "system",
"content": """
Sen Orif Yuldashevning professional SMM AI sotuv yordamchisisan.

🎯 MAQSADING:
- mijozni tushunish
- muammoni aniqlash
- mos yechim berish
- har doim mijozni fikrini to'g'ri ekanligini aytib undan keyin psixalogik yaxshi yondashib tog' yechim va qoshimcha savol yoki taklif ber

---

🧠 HAR BIR JAVOBDAN OLDIN ICHINGDA ANALIZ QIL:
1. Bu user nimani xohlayapti?
2. U qaysi bosqichda?
   - sovuq (shunchaki so‘rayapti)
   - qiziqqan
   - tayyor (bog‘lanmoqchi)

3. Shu odamga hozir nima kerak:
   - savolmi?
   - tushuntirishmi?
   - yopish (link berish)mi?

---

📌 MUHIM QOIDALAR:

- mijozga har daim dialog oxirida unga foydali taklif ber sohasi qiziqishi bo'yicha
- Agar user tushunmayotgan bo‘lsa → oddiy qilib tushuntir

---

💬 JAVOB STRUKTURASI:

1. qisqa tushunish (empatya)
2. foydali fikr / yechim
3. yumshoq savol  (doim oxirida)

---

❌ QILMA:
- uzun gapirma
- keraksiz savol berma
- userni e’tiborsiz qoldirma

---

🧠 SEN:
- sotuvchi emassan, maslahatchisan
- majburlamaysan, qiziqtirasan

---

🎯 YAKUNI:
agar mijoz rostan qiziqadigan smm hizmat sotib olishga yaqin bo'lsa mijozni Orif bilan ishlashga olib kel lekin birdaniga psixalogik bosim berma
"""
}
        ] + user_memory[user_id][-25:]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        reply = response.choices[0].message.content

        user_memory[user_id].append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "Xatolik bo‘ldi, yana urinib ko‘ring 🙂"

# ========= START =========
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = "start"

    save_user(message.from_user)

    await message.answer(
        "Salom 🙂\n\n"
        "Men Orif Yuldashevning AI yordamchisiman.\n"
        "Sizga bepul analiz qilib, qanday o‘sish mumkinligini ko‘rsataman.\n\n"
        "Boshlaymizmi?",
        reply_markup=kb
    )

# ========= BUTTONS =========
@dp.message_handler(lambda msg: msg.text == "📊 Bepul analiz")
async def analiz(message: types.Message):
    user_state[message.from_user.id] = "biznes"
    await message.answer("Zo‘r 👍\n\nQaysi sohada ishlaysiz va nima sotasiz?")

@dp.message_handler(lambda msg: "narx" in msg.text.lower())
async def narx(message: types.Message):
    await message.answer("Narx xizmatga qarab farq qiladi 🙂\nAvval analiz qilib beraymi?")

@dp.message_handler(lambda msg: msg.text == "📞 Aloqa")
async def contact(message: types.Message):
    await message.answer(
        '<a href="https://t.me/yyyl_o">ORIF YULDASHEV</a>',
        parse_mode="HTML"
    )

# ========= CHAT =========
@dp.message_handler()
async def chat(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    save_user(message.from_user)

    await bot.send_chat_action(user_id, "typing")

    if user_id not in user_state:
        user_state[user_id] = "start"

    state = user_state[user_id]

    # ===== FUNNEL =====
    if state == "start":
        user_state[user_id] = "biznes"
        await message.answer("Qaysi sohada ishlaysiz?")
        return

    elif state == "biznes":
        user_state[user_id] = "muammo"
        await message.answer("Hozir eng katta muammo nimada?")
        return

    elif state == "muammo":
        user_state[user_id] = "yopish"

        reply = ai_reply(user_id, text)
        await message.answer(reply)
        return

    elif state == "yopish":
        reply = ai_reply(user_id, text)

        reply += '\n\n<a href="https://t.me/yyyl_o">ORIF YULDASHEV</a> bilan bog‘lanish'

        await message.answer(reply, parse_mode="HTML")

        # 🔥 ADMINGA LEAD
        await bot.send_message(
            ADMIN_ID,
            f"🔥 YANGI LEAD\n\n"
            f"ID: {user_id}\n"
            f"Username: @{message.from_user.username}\n"
            f"Text: {text}"
        )

        return

# ========= RUN =========
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)