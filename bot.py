# -*- coding: utf-8 -*-

import os
import asyncio
import requests
import tempfile
import base64
import sqlite3

from io import BytesIO

import PyPDF2
from docx import Document

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
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
# ADMIN
# ====================================

ADMIN_ID = 123456789


# ====================================
# DATABASE
# ====================================

conn = sqlite3.connect(
    "database.db"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    user_id INTEGER PRIMARY KEY,
    mode TEXT,
    messages INTEGER
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

    create_user(user_id)

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

    create_user(user_id)

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

    create_user(user_id)

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

user_memory = {}

image_waiting_users = set()


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

reply_menu = ReplyKeyboardMarkup(
    keyboard=[

        [
            KeyboardButton(text="🧠 AI Чат"),
            KeyboardButton(text="🌐 Интернет")
        ],

        [
            KeyboardButton(text="📄 Документ"),
            KeyboardButton(text="🖼 Фото")
        ],

        [
            KeyboardButton(text="🎨 Картинка"),
            KeyboardButton(text="👨‍💻 Код")
        ],

        [
            KeyboardButton(text="✍️ Тексты"),
            KeyboardButton(text="💰 Бизнес")
        ],

        [
            KeyboardButton(text="🧘 Психолог"),
            KeyboardButton(text="👤 Профиль")
        ],

        [
            KeyboardButton(text="🧹 Очистить чат")
        ]
    ],

    resize_keyboard=True
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

Твой умный помощник с AI возможностями.

━━━━━━━━━━━━━━━

🔥 <b>Что умеет бот:</b>

🧠 Решение задач  
🌐 Поиск в интернете  
📄 Анализ PDF / DOCX / TXT  
🖼 Анализ изображений  
🎨 Генерация картинок
👨‍💻 Помощь с кодом  
✍️ Написание текстов  
💰 Бизнес-идеи  
🧘 Поддержка и общение  

━━━━━━━━━━━━━━━

⚡ <b>Выберите действие ниже:</b>
"""

    await message.answer(
        text,
        reply_markup=reply_menu,
        parse_mode="HTML"
    )


# ====================================
# PROFILE
# ====================================

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):

    user_id = message.from_user.id
    name = message.from_user.first_name

    messages_count = get_messages(user_id)

    current_mode = get_mode(user_id)

    mode_names = {
        "default": "🧠 AI Чат",
        "coder": "👨‍💻 Код",
        "business": "💰 Бизнес",
        "psychologist": "🧘 Психолог",
        "copywriter": "✍️ Тексты"
    }

    text = f"""
╔══════════════╗
      👤 ПРОФИЛЬ
╚══════════════╝

✨ Имя: <b>{name}</b>

🆔 ID: <code>{user_id}</code>

🧠 Режим:
<b>{mode_names.get(current_mode)}</b>

📨 Сообщений:
<b>{messages_count}</b>

🚀 Статус:
<b>Premium User</b>
"""

    await message.answer(
        text,
        parse_mode="HTML"
    )


# ====================================
# ADMIN PANEL
# ====================================

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    users_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT SUM(messages) FROM users"
    )

    total_messages = cursor.fetchone()[0]

    if total_messages is None:
        total_messages = 0

    text = f"""
👑 <b>ADMIN PANEL</b>

👥 Пользователей:
<b>{users_count}</b>

💬 Сообщений:
<b>{total_messages}</b>

Команды:

/users
/broadcast текст
"""

    await message.answer(
        text,
        parse_mode="HTML"
    )


# ====================================
# USERS
# ====================================

@dp.message(F.text == "/users")
async def users_list(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute(
        """
        SELECT user_id, messages
        FROM users
        ORDER BY messages DESC
        LIMIT 20
        """
    )

    users = cursor.fetchall()

    text = "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"

    for user in users:

        text += (
            f"🆔 <code>{user[0]}</code>\n"
            f"💬 {user[1]} сообщений\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )


# ====================================
# BROADCAST
# ====================================

@dp.message(F.text.startswith("/broadcast"))
async def broadcast(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    text_to_send = message.text.replace(
        "/broadcast",
        ""
    ).strip()

    if not text_to_send:

        await message.answer(
            "❌ Введите текст"
        )

        return

    cursor.execute(
        "SELECT user_id FROM users"
    )

    users = cursor.fetchall()

    success = 0

    for user in users:

        try:

            await bot.send_message(
                user[0],
                f"📢 {text_to_send}"
            )

            success += 1

        except:
            pass

    await message.answer(
        f"✅ Отправлено: {success}"
    )


# ====================================
# IMAGE GENERATION
# ====================================

@dp.message(F.text == "🎨 Картинка")
async def image_mode(message: Message):

    image_waiting_users.add(
        message.from_user.id
    )

    await message.answer(
        "🎨 Напишите описание картинки"
    )


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

            else:

                await message.answer(
                    "❌ Поддерживаются PDF / TXT / DOCX"
                )

                return

        prompt = f"""
Вот текст файла:

{text[:15000]}

1. Определи тему документа
2. Сделай краткое содержание
3. Если это задача —
реши её пошагово
"""

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = response.choices[0].message.content

        await message.answer(answer)

    except Exception as e:

        await message.answer(
            f"❌ Ошибка файла:\n{str(e)}"
        )

    await wait_message.delete()


# ====================================
# IMAGE ANALYSIS
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

            with open(temp_file.name, "rb") as image_file:

                base64_image = base64.b64encode(
                    image_file.read()
                ).decode("utf-8")

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
Проанализируй изображение.

Если это задача —
реши её пошагово.

Если это текст —
прочитай и перескажи.
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
            f"❌ Ошибка изображения:\n{str(e)}"
        )

    await wait_message.delete()


# ====================================
# BUTTONS
# ====================================

@dp.message(F.text == "👨‍💻 Код")
async def code_mode(message: Message):

    set_mode_db(
        message.from_user.id,
        "coder"
    )

    await message.answer(
        "👨‍💻 Режим программиста включен"
    )


@dp.message(F.text == "💰 Бизнес")
async def business_mode(message: Message):

    set_mode_db(
        message.from_user.id,
        "business"
    )

    await message.answer(
        "💰 Бизнес режим включен"
    )


@dp.message(F.text == "🧘 Психолог")
async def psycho_mode(message: Message):

    set_mode_db(
        message.from_user.id,
        "psychologist"
    )

    await message.answer(
        "🧘 Режим психолога включен"
    )


@dp.message(F.text == "✍️ Тексты")
async def copy_mode(message: Message):

    set_mode_db(
        message.from_user.id,
        "copywriter"
    )

    await message.answer(
        "✍️ Режим копирайтера включен"
    )


@dp.message(F.text == "🧠 AI Чат")
async def ai_chat(message: Message):

    set_mode_db(
        message.from_user.id,
        "default"
    )

    await message.answer(
        "🧠 AI режим включен"
    )


@dp.message(F.text == "🧹 Очистить чат")
async def clear_chat(message: Message):

    user_memory[message.from_user.id] = []

    await message.answer(
        "🧹 История очищена"
    )


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

    current_mode = get_mode(user_id)

    if user_id not in user_memory:

        user_memory[user_id] = [
            {
                "role": "system",
                "content": MODES[current_mode]
            }
        ]

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

Если это задача —
реши её пошагово.
"""

        user_memory[user_id].append(
            {
                "role": "user",
                "content": prompt
            }
        )

        response = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=user_memory[user_id]
        )

        answer = response.choices[0].message.content

        user_memory[user_id].append(
            {
                "role": "assistant",
                "content": answer
            }
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

async def main():

    print("AI бот запущен...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
