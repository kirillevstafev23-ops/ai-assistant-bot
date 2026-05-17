# -*- coding: utf-8 -*-

import os
import asyncio
import requests
import tempfile
import base64
import sqlite3
import pytesseract

from io import BytesIO
from PIL import Image

import PyPDF2
from docx import Document

from flask import Flask, send_file
from threading import Thread

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    WebAppInfo
)
from aiogram.filters import CommandStart

from openai import OpenAI


# ====================================
# TOKENS
# ====================================

TOKEN = os.getenv("TOKEN")

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)

HF_TOKEN = os.getenv("HF_TOKEN")


# ====================================
# ВСТАВЬ СВОЮ ССЫЛКУ RAILWAY
# ====================================

WEB_APP_URL = "https://ai-assistant-bot-production-11dd.up.railway.app"


# ====================================
# ADMIN
# ====================================

ADMIN_ID = 1739947062


# ====================================
# FLASK WEB APP
# ====================================

app = Flask(__name__)


@app.route("/")
def home():

    return open(
    "webapp.html",
    "r",
    encoding="utf-8"
).read()


def run_web():

    port = int(
        os.environ.get("PORT", 8080)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
    )

# ====================================
# DATABASE
# ====================================

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


# ====================================
# DATABASE FUNCTIONS
# ====================================

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
        "SELECT mode FROM users WHERE user_id=?",
        (user_id,)
    )

    result = cursor.fetchone()

    return result[0]


def set_mode_db(user_id, mode):

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

    return result[0]


# ====================================
# BOT
# ====================================

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ====================================
# OPENROUTER
# ====================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# ====================================
# MEMORY
# ====================================

image_waiting_users = set()


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

    current_mode = get_mode(user_id)

    memory.append({
        "role": "system",
        "content": MODES[current_mode]
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


# ====================================
# AI MODES
# ====================================

MODES = {

    "default": (
        "Ты мощный AI ассистент. "
        "Помогай максимально полезно."
    ),

    "coder": (
        "Ты опытный программист. "
        "Помогай с кодом."
    ),

    "business": (
        "Ты бизнес-консультант."
    ),

    "psychologist": (
        "Ты спокойный психолог."
    ),

    "copywriter": (
        "Ты профессиональный копирайтер."
    )
}


# ====================================
# MENU
# ====================================

main_inline_menu = InlineKeyboardMarkup(
    inline_keyboard=[

        [
            InlineKeyboardButton(
                text="🧠 AI Чат",
                callback_data="ai_chat"
            ),

            InlineKeyboardButton(
                text="🌐 Интернет",
                callback_data="internet"
            )
        ],

        [
            InlineKeyboardButton(
                text="📄 Документы",
                callback_data="docs"
            ),

            InlineKeyboardButton(
                text="🖼 Фото",
                callback_data="photo"
            )
        ],

        [
            InlineKeyboardButton(
                text="🎨 Картинки",
                callback_data="image_gen"
            ),

            InlineKeyboardButton(
                text="👨‍💻 Код",
                callback_data="coder"
            )
        ],

        [
            InlineKeyboardButton(
                text="✍️ Тексты",
                callback_data="copywriter"
            ),

            InlineKeyboardButton(
                text="💰 Бизнес",
                callback_data="business"
            )
        ],

        [
            InlineKeyboardButton(
                text="🧘 Психолог",
                callback_data="psychologist"
            ),

            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="profile"
            )
        ],

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
                callback_data="clear_chat"
            )
        ]
    ]
)


# ====================================
# INTERNET SEARCH
# ====================================

def search_internet(query):

    try:

        url = "https://api.tavily.com/search"

        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 5
        }

        response = requests.post(
            url,
            json=payload
        )

        data = response.json()

        results = data.get("results", [])

        text = ""

        for item in results:

            text += (
                f"{item['title']}\n"
                f"{item['content']}\n\n"
            )

        return text

    except:
        return "Интернет-поиск недоступен."


# ====================================
# START
# ====================================

@dp.message(CommandStart())
async def start(message: Message):

    create_user(message.from_user.id)

    user_name = message.from_user.first_name

    text = f"""
✨ <b>Добро пожаловать, {user_name}!</b>

🤖 <b>AI Assistant</b>

Твой умный AI помощник 🚀
"""

    await message.answer(
        text,
        reply_markup=main_inline_menu,
        parse_mode="HTML"
    )


# ====================================
# CALLBACKS
# ====================================

@dp.callback_query(F.data == "ai_chat")
async def ai_chat_callback(callback: CallbackQuery):

    set_mode_db(
        callback.from_user.id,
        "default"
    )

    await callback.message.answer(
        "🧠 AI режим включен"
    )

    await callback.answer()


@dp.callback_query(F.data == "coder")
async def coder_callback(callback: CallbackQuery):

    set_mode_db(
        callback.from_user.id,
        "coder"
    )

    await callback.message.answer(
        "👨‍💻 Режим программиста включен"
    )

    await callback.answer()


@dp.callback_query(F.data == "business")
async def business_callback(callback: CallbackQuery):

    set_mode_db(
        callback.from_user.id,
        "business"
    )

    await callback.message.answer(
        "💰 Бизнес режим включен"
    )

    await callback.answer()


@dp.callback_query(F.data == "psychologist")
async def psychologist_callback(callback: CallbackQuery):

    set_mode_db(
        callback.from_user.id,
        "psychologist"
    )

    await callback.message.answer(
        "🧘 Режим психолога включен"
    )

    await callback.answer()


@dp.callback_query(F.data == "copywriter")
async def copywriter_callback(callback: CallbackQuery):

    set_mode_db(
        callback.from_user.id,
        "copywriter"
    )

    await callback.message.answer(
        "✍️ Режим текстов включен"
    )

    await callback.answer()


@dp.callback_query(F.data == "clear_chat")
async def clear_callback(callback: CallbackQuery):

    clear_memory(callback.from_user.id)

    await callback.message.answer(
        "🧹 История очищена"
    )

    await callback.answer()


@dp.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):

    user_id = callback.from_user.id
    name = callback.from_user.first_name

    messages_count = get_messages(user_id)

    current_mode = get_mode(user_id)

    text = f"""
👤 <b>ПРОФИЛЬ</b>

✨ Имя: <b>{name}</b>

🆔 ID:
<code>{user_id}</code>

🧠 Режим:
<b>{current_mode}</b>

📨 Сообщений:
<b>{messages_count}</b>

🚀 Статус:
<b>Premium User</b>
"""

    await callback.message.answer(
        text,
        parse_mode="HTML"
    )

    await callback.answer()


# ====================================
# WEB APP DATA
# ====================================

@dp.message(F.web_app_data)
async def web_app_handler(message: Message):

    data = message.web_app_data.data

    if data == "ai_chat":

        await message.answer(
            "🧠 AI Chat открыт"
        )

    elif data == "image":

        image_waiting_users.add(
            message.from_user.id
        )

        await message.answer(
            "🎨 Напиши описание картинки"
        )

    elif data == "docs":

        await message.answer(
            "📄 Отправь документ"
        )

    elif data == "internet":

        await message.answer(
            "🌐 Напиши запрос"
        )


# ====================================
# IMAGE ANALYSIS + OCR
# ====================================

@dp.message(F.photo)
async def image_handler(message: Message):

    wait_message = await message.answer(
        "🖼 Анализирую изображение..."
    )

    try:

        photo = message.photo[-1]

        file = await bot.get_file(photo.file_id)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        ) as temp_file:

            await bot.download_file(
                file.file_path,
                temp_file.name
            )

            image = Image.open(temp_file.name)

            extracted_text = pytesseract.image_to_string(
                image,
                lang="eng+rus"
            )

            with open(temp_file.name, "rb") as image_file:

                base64_image = base64.b64encode(
                    image_file.read()
                ).decode("utf-8")

        prompt = f"""
Ты получил изображение.

OCR текст:

{extracted_text}

Если это задача —
реши пошагово.
"""

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
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
            f"❌ Ошибка:\n{str(e)}"
        )

    await wait_message.delete()


# ====================================
# FILE ANALYSIS
# ====================================

@dp.message(F.document)
async def file_handler(message: Message):

    document = message.document

    wait_message = await message.answer(
        "📄 Анализирую файл..."
    )

    try:

        file = await bot.get_file(document.file_id)

        suffix = os.path.splitext(
            document.file_name
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            await bot.download_file(
                file.file_path,
                temp_file.name
            )

            text = ""

            if suffix == ".pdf":

                with open(temp_file.name, "rb") as pdf_file:

                    reader = PyPDF2.PdfReader(pdf_file)

                    for page in reader.pages:

                        extracted = page.extract_text()

                        if extracted:
                            text += extracted

            elif suffix == ".txt":

                with open(
                    temp_file.name,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as txt_file:

                    text = txt_file.read()

            elif suffix == ".docx":

                doc = Document(temp_file.name)

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
            f"❌ Ошибка:\n{str(e)}"
        )

    await wait_message.delete()


# ====================================
# MAIN CHAT
# ====================================

@dp.message()
async def chat(message: Message):

    user_id = message.from_user.id
    user_text = message.text

    if user_id in image_waiting_users:

        wait_message = await message.answer(
            "🎨 Генерирую картинку..."
        )

        try:

            API_URL = (
                "https://api-inference.huggingface.co/models/"
                "stabilityai/stable-diffusion-xl-base-1.0"
            )

            headers = {
                "Authorization": f"Bearer {HF_TOKEN}"
            }

            response = requests.post(
                API_URL,
                headers=headers,
                json={
                    "inputs": user_text
                },
                timeout=120
            )

            image_bytes = response.content

            image_stream = BytesIO(image_bytes)

            await message.answer_photo(
                image_stream,
                caption=f"🎨 {user_text}"
            )

        except Exception as e:

            await message.answer(
                f"❌ Ошибка:\n{str(e)}"
            )

        image_waiting_users.remove(user_id)

        await wait_message.delete()

        return

    add_message(user_id)

    messages = load_memory(user_id)

    wait_message = await message.answer(
        "🧠 Думаю..."
    )

    try:

        internet_data = search_internet(user_text)

        prompt = f"""
Вопрос:
{user_text}

Интернет:
{internet_data}
"""

        save_memory(
            user_id,
            "user",
            prompt
        )

        messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

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
            f"❌ Ошибка:\n{str(e)}"
        )

    await wait_message.delete()


# ====================================
# MAIN
# ====================================

if __name__ == "__main__":

    web_thread = Thread(target=run_web)

    web_thread.daemon = True

    web_thread.start()

    asyncio.run(dp.start_polling(bot))
