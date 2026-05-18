# -*- coding: utf-8 -*-

import os
import sqlite3
import asyncio
import requests
import tempfile
import base64
import pytesseract

from io import BytesIO
from PIL import Image

import PyPDF2
from docx import Document

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

from openai import OpenAI


# =========================================
# TOKENS
# =========================================

TOKEN = os.getenv("TOKEN")

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)

HF_TOKEN = os.getenv("HF_TOKEN")


# =========================================
# URL RENDER
# =========================================

WEBHOOK_URL = "https://ai-assistant-bot-production-11dd.up.railway.app"


WEB_APP_URL = "https://ai-assistant-bot-production-11dd.up.railway.app"


# =========================================
# ADMIN
# =========================================

ADMIN_ID = 1739947062


# =========================================
# FLASK
# =========================================

app = Flask(__name__)


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
    mode TEXT,
    messages INTEGER
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
# BOT
# =========================================

bot = Bot(token=TOKEN)

dp = Dispatcher()


# =========================================
# OPENROUTER
# =========================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)


# =========================================
# WEB APP PAGE
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

        <style>

            body {

                background: #0f172a;
                color: white;
                font-family: Arial;
                padding: 20px;
                margin: 0;
            }

            h1 {

                text-align: center;
                margin-bottom: 30px;
            }

            .grid {

                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }

            button {

                background: #1e293b;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 20px;
                font-size: 18px;
                cursor: pointer;
            }

            button:hover {

                background: #334155;
            }

        </style>

    </head>

    <body>

        <h1>🚀 AI Assistant</h1>

        <div class="grid">

            <button onclick="sendData('ai_chat')">
                🧠 AI Chat
            </button>

            <button onclick="sendData('image')">
                🎨 Картинки
            </button>

            <button onclick="sendData('docs')">
                📄 Документы
            </button>

            <button onclick="sendData('internet')">
                🌐 Интернет
            </button>

        </div>

        <script src="https://telegram.org/js/telegram-web-app.js"></script>

        <script>

            let tg = window.Telegram.WebApp;

            tg.expand();

            function sendData(data) {

                tg.sendData(data);
            }

        </script>

    </body>
    </html>
    """


# =========================================
# DATABASE FUNCTIONS
# =========================================

def create_user(user_id):

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:

        cursor.execute(
            """
            INSERT INTO users
            (user_id, mode, messages)

            VALUES (?, ?, ?)
            """,
            (
                user_id,
                "default",
                0
            )
        )

        conn.commit()


def get_mode(user_id):

    create_user(user_id)

    cursor.execute(
        """
        SELECT mode
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    if result is None:
        return "default"

    return result[0]


def set_mode(user_id, mode):

    cursor.execute(
        """
        UPDATE users
        SET mode=?
        WHERE user_id=?
        """,
        (
            mode,
            user_id
        )
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

    if result is None:

        create_user(user_id)

        return 0

    return result[0]


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

    memory = []

    memory.append({
        "role": "system",
        "content": "Ты мощный AI ассистент."
    })

    for row in rows:

        memory.append({
            "role": row[0],
            "content": row[1]
        })

    return memory


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
                text="🧹 Очистить чат",
                callback_data="clear"
            )
        ]
    ]
)


# =========================================
# START
# =========================================

@dp.message(CommandStart())
async def start(message: Message):

    create_user(message.from_user.id)

    text = """
🚀 <b>AI Assistant</b>

Умный AI бот:
• чат
• фото
• файлы
• Mini App
"""

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=menu
    )


# =========================================
# CLEAR
# =========================================

@dp.callback_query(F.data == "clear")
async def clear_callback(callback: CallbackQuery):

    clear_memory(callback.from_user.id)

    await callback.message.answer(
        "🧹 История очищена"
    )

    await callback.answer()


# =========================================
# PHOTO
# =========================================

@dp.message(F.photo)
async def photo_handler(message: Message):

    wait = await message.answer(
        "🖼 Анализирую фото..."
    )

    try:

        photo = message.photo[-1]

        file = await bot.get_file(photo.file_id)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        ) as temp:

            await bot.download_file(
                file.file_path,
                temp.name
            )

            image = Image.open(temp.name)

            ocr_text = pytesseract.image_to_string(
                image,
                lang="eng+rus"
            )

            with open(temp.name, "rb") as img:

                base64_image = base64.b64encode(
                    img.read()
                ).decode("utf-8")

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
Реши задачу по изображению.

OCR:
{ocr_text}
"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )

        answer = response.choices[0].message.content

        await message.answer(answer)

    except Exception as e:

        await message.answer(
            f"Ошибка:\n{str(e)}"
        )

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

                with open(temp.name, "rb") as pdf:

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

            answer = response.choices[0].message.content

            await message.answer(answer)

    except Exception as e:

        await message.answer(
            f"Ошибка:\n{str(e)}"
        )

    await wait.delete()


# =========================================
# CHAT
# =========================================

@dp.message()
async def chat(message: Message):

    user_id = message.from_user.id

    create_user(user_id)

    add_message(user_id)

    wait = await message.answer(
        "🧠 Думаю..."
    )

    try:

        messages = load_memory(user_id)

        save_memory(
            user_id,
            "user",
            message.text
        )

        messages.append({
            "role": "user",
            "content": message.text
        })

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=messages
        )

        answer = response.choices[0].message.content

        save_memory(
            user_id,
            "assistant",
            answer
        )

        await message.answer(answer)

    except Exception as e:

        await message.answer(
            f"Ошибка:\n{str(e)}"
        )

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

        await dp.feed_update(
            bot,
            update
        )

        return "ok"

    except Exception as e:

        print(e)

        return "error"

# =========================================
# START WEBHOOK
# =========================================

async def set_webhook():

    await bot.set_webhook(
        WEBHOOK_URL
    )



# =========================================
# MAIN
# =========================================

if __name__ == "__main__":

    async def startup():

        await bot.delete_webhook(
            drop_pending_updates=True
        )

        await bot.set_webhook(
            WEBHOOK_URL
        )

    asyncio.run(startup())

    port = int(
        os.environ.get("PORT", 8080)
    )

    app.run(
    host="0.0.0.0",
    port=port,
    threaded=True
)
