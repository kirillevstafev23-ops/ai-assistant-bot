# =========================================
# IMPORTS
# =========================================

import os
import asyncio
import sqlite3
import tempfile
import base64

from flask import Flask, request

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    CallbackQuery
)

from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from openai import OpenAI

from PIL import Image

import pytesseract
import PyPDF2

from docx import Document

print("BOT STARTING...")


# =========================================
# TOKENS
# =========================================

TOKEN = "8990614240:AAH7is1k5dNKgNpl_FbUXarn0SXo1aHhYSY"

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

HF_TOKEN = os.getenv("HF_TOKEN")

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)


# =========================================
# URLS
# =========================================

WEBHOOK_URL = "https://ai-assistant-bot-kcm7.onrender.com/webhook"

WEB_APP_URL = "https://ai-assistant-bot-kcm7.onrender.com"


# =========================================
# ADMIN
# =========================================

ADMIN_ID = 1739947062


# =========================================
# FLASK
# =========================================

app = Flask(__name__)


# =========================================
# BOT
# =========================================

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# =========================================
# OPENROUTER
# =========================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)


# =========================================
# DATABASE
# =========================================

conn = sqlite3.connect(
    "database.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    user_id INTEGER PRIMARY KEY,
    messages INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS memory (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT,
    content TEXT
)
""")

conn.commit()


# =========================================
# DATABASE FUNCTIONS
# =========================================

def add_user(user_id):

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id)

        VALUES (?)
        """,
        (user_id,)
    )

    conn.commit()


def add_message(user_id):

    cursor.execute(
        """
        UPDATE users
        SET messages = messages + 1
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()


def get_messages(user_id):

    cursor.execute(
        """
        SELECT messages
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return 0


def get_all_users():

    cursor.execute(
        "SELECT user_id FROM users"
    )

    return cursor.fetchall()


# =========================================
# MEMORY
# =========================================

def save_memory(user_id, role, content):

    cursor.execute(
        """
        INSERT INTO memory
        (user_id, role, content)

        VALUES (?, ?, ?)
        """,
        (
            user_id,
            role,
            content
        )
    )

    conn.commit()


def load_memory(user_id):

    cursor.execute(
        """
        SELECT role, content
        FROM memory
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 20
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    rows.reverse()

    messages = []

    messages.append({
        "role": "system",
        "content": "Ты мощный AI ассистент."
    })

    for row in rows:

        messages.append({
            "role": row[0],
            "content": row[1]
        })

    return messages


def clear_memory(user_id):

    cursor.execute(
        """
        DELETE FROM memory
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()


# =========================================
# MENU
# =========================================

menu = InlineKeyboardMarkup(
    inline_keyboard=[

        [
            InlineKeyboardButton(
                text="🌐 Mini App",
                web_app=WebAppInfo(
                    url=WEB_APP_URL
                )
            )
        ],

        [
            InlineKeyboardButton(
                text="🧹 Очистить память",
                callback_data="clear"
            )
        ],

        [
            InlineKeyboardButton(
                text="📊 Профиль",
                callback_data="profile"
            )
        ]
    ]
)


# =========================================
# WEB APP
# =========================================

@app.route("/")
def home():

    return """
    <!DOCTYPE html>
    <html lang="ru">

    <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>AI Assistant</title>

        <script src="https://telegram.org/js/telegram-web-app.js"></script>

        <style>

            body {

                background: #0f172a;
                color: white;
                font-family: Arial;
                padding: 20px;
            }

            textarea {

                width: 100%;
                height: 150px;
                border-radius: 10px;
                padding: 10px;
                margin-top: 10px;
            }

            button {

                margin-top: 10px;
                width: 100%;
                height: 50px;
                border: none;
                border-radius: 10px;
                background: #2563eb;
                color: white;
                font-size: 18px;
            }

        </style>

    </head>

    <body>

        <h1>🚀 AI Assistant</h1>

        <textarea id="prompt"
                  placeholder="Напиши сообщение..."></textarea>

        <button onclick="sendMessage()">
            Отправить
        </button>

        <script>

            function sendMessage() {

                let text =
                    document.getElementById(
                        "prompt"
                    ).value;

                Telegram.WebApp.sendData(text);

                alert("Отправлено!");
            }

        </script>

    </body>
    </html>
    """


# =========================================
# START
# =========================================

@dp.message(CommandStart())
async def start(message: Message):

    print("START COMMAND RECEIVED")

    await message.answer("Бот работает")

    add_user(message.from_user.id)

    text = """
🚀 <b>AI Assistant</b>

Возможности:
• GPT AI
• Фото OCR
• PDF / DOCX
• Mini App
• Память диалога
"""

    await message.answer(
        text,
        reply_markup=menu
    )


# =========================================
# PROFILE
# =========================================

@dp.callback_query(F.data == "profile")
async def profile_callback(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    messages_count = get_messages(user_id)

    text = f"""
👤 <b>Профиль</b>

🧠 Сообщений:
{messages_count}
"""

    await callback.message.answer(text)

    await callback.answer()


# =========================================
# CLEAR MEMORY
# =========================================

@dp.callback_query(F.data == "clear")
async def clear_callback(
    callback: CallbackQuery
):

    clear_memory(callback.from_user.id)

    await callback.message.answer(
        "🧹 Память очищена"
    )

    await callback.answer()


# =========================================
# ADMIN
# =========================================

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()

    text = f"""
🛠 <b>Админ панель</b>

👥 Пользователей:
{len(users)}
"""

    await message.answer(text)


# =========================================
# BROADCAST
# =========================================

@dp.message(F.text.startswith("/broadcast "))
async def broadcast(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace(
        "/broadcast ",
        ""
    )

    users = get_all_users()

    success = 0

    for user in users:

        try:

            await bot.send_message(
                user[0],
                text
            )

            success += 1

        except:
            pass

    await message.answer(
        f"✅ Отправлено: {success}"
    )


# =========================================
# PHOTO OCR
# =========================================

@dp.message(F.photo)
async def photo_handler(message: Message):

    wait = await message.answer(
        "🖼 Анализирую фото..."
    )

    try:

        photo = message.photo[-1]

        file = await bot.get_file(
            photo.file_id
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        ) as temp:

            await bot.download_file(
                file.file_path,
                temp.name
            )

            image = Image.open(temp.name)

            text = pytesseract.image_to_string(
                image,
                lang="eng+rus"
            )

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[
                {
                    "role": "user",
                    "content": f"""
Распознай и реши:

{text}
"""
                }
            ]
        )

        answer = response.choices[
            0
        ].message.content

        await message.answer(answer)

    except Exception as e:

        await message.answer(str(e))

    await wait.delete()


# =========================================
# FILES
# =========================================

@dp.message(F.document)
async def file_handler(message: Message):

    wait = await message.answer(
        "📄 Анализирую файл..."
    )

    try:

        document = message.document

        file = await bot.get_file(
            document.file_id
        )

        suffix = os.path.splitext(
            document.file_name
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp:

            await bot.download_file(
                file.file_path,
                temp.name
            )

            text = ""

            if suffix == ".pdf":

                with open(
                    temp.name,
                    "rb"
                ) as pdf:

                    reader = PyPDF2.PdfReader(pdf)

                    for page in reader.pages:

                        extracted = page.extract_text()

                        if extracted:
                            text += extracted

            elif suffix == ".txt":

                with open(
                    temp.name,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as txt:

                    text = txt.read()

            elif suffix == ".docx":

                doc = Document(temp.name)

                for para in doc.paragraphs:

                    text += para.text + "\n"

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[
                {
                    "role": "user",
                    "content": f"""
Проанализируй файл:

{text[:15000]}
"""
                }
            ]
        )

        answer = response.choices[
            0
        ].message.content

        await message.answer(answer)

    except Exception as e:

        await message.answer(str(e))

    await wait.delete()


# =========================================
# CHAT
# =========================================

@dp.message()
async def ai_chat(message: Message):

    user_id = message.from_user.id

    add_user(user_id)

    add_message(user_id)

    wait = await message.answer(
        "🧠 Думаю..."
    )

    try:

        save_memory(
            user_id,
            "user",
            message.text
        )

        messages = load_memory(user_id)

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=messages
        )

        answer = response.choices[
            0
        ].message.content

        save_memory(
            user_id,
            "assistant",
            answer
        )

        await message.answer(answer)

    except Exception as e:

        await message.answer(str(e))

    await wait.delete()


# =========================================
# WEBHOOK
# =========================================

@app.route("/webhook", methods=["POST"])
async def webhook():

    try:

        update = Update.model_validate(
            request.json,
            context={"bot": bot}
        )

        await dp.feed_update(bot, update)

        return "ok"

    except Exception as e:

        print("WEBHOOK ERROR:")
        print(str(e))

        return "error", 500


# =========================================
# MAIN
# =========================================

print("FLASK START...")

if __name__ == "__main__":

    try:

        print("SETTING WEBHOOK...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(
            bot.delete_webhook(
                drop_pending_updates=True
            )
        )

        loop.run_until_complete(
            bot.set_webhook(
                WEBHOOK_URL
            )
        )

        info = loop.run_until_complete(
            bot.get_webhook_info()
        )

        print(info)

        print("WEBHOOK OK")

        port = int(
            os.environ.get("PORT", 10000)
        )

        print("START SERVER...")

        app.run(
            host="0.0.0.0",
            port=port
        )

    except Exception as e:

        print("ERROR:")
        print(str(e))
