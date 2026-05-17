# -*- coding: utf-8 -*-

import os
import asyncio
import requests
import tempfile
import base64

import PyPDF2
from docx import Document

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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
# USER DATA
# ====================================

user_memory = {}
user_modes = {}
user_stats = {}


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
# INLINE MENU
# ====================================

menu = InlineKeyboardMarkup(
    inline_keyboard=[

        [
            InlineKeyboardButton(
                text="👨‍💻 Программист",
                callback_data="coder"
            )
        ],

        [
            InlineKeyboardButton(
                text="💰 Бизнес",
                callback_data="business"
            )
        ],

        [
            InlineKeyboardButton(
                text="🧠 Психолог",
                callback_data="psychologist"
            )
        ],

        [
            InlineKeyboardButton(
                text="✍️ Копирайтер",
                callback_data="copywriter"
            )
        ],

        [
            InlineKeyboardButton(
                text="🧹 Новый чат",
                callback_data="new_chat"
            )
        ]
    ]
)


# ====================================
# REPLY MENU
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
            KeyboardButton(text="👨‍💻 Код"),
            KeyboardButton(text="✍️ Тексты")
        ],

        [
            KeyboardButton(text="💰 Бизнес"),
            KeyboardButton(text="🧘 Психолог")
        ],

        [
            KeyboardButton(text="🧹 Очистить чат"),
            KeyboardButton(text="👤 Профиль")
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
# USER PROFILE
# ====================================

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):

    user_id = message.from_user.id
    name = message.from_user.first_name

    if user_id not in user_stats:

        user_stats[user_id] = {
            "messages": 0
        }

    messages_count = user_stats[user_id]["messages"]

    current_mode = user_modes.get(
        user_id,
        "default"
    )

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

━━━━━━━━━━━━━━━

🤖 AI Assistant
"""

    await message.answer(
        text,
        parse_mode="HTML"
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
4. Если это обучение —
объясни простым языком
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
Внимательно проанализируй изображение.

1. Определи предмет:
- физика
- математика
- химия
- геометрия
- программирование
- текст
- документ
- таблица
- другое

2. Если это школьная или университетская задача:
- реши именно ту задачу, которая на изображении
- НЕ придумывай свои примеры
- используй данные только с картинки
- объясняй решение пошагово

3. Если есть формулы —
обязательно используй их.

4. Если на фото текст —
прочитай и кратко перескажи.

5. Если задача по физике —
используй физические формулы и законы.

6. Не придумывай задания, которых нет на изображении.
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
# BUTTON HANDLERS
# ====================================

@dp.message(F.text == "👨‍💻 Код")
async def code_mode(message: Message):

    user_modes[message.from_user.id] = "coder"

    await message.answer(
        "👨‍💻 Режим программиста включен"
    )


@dp.message(F.text == "💰 Бизнес")
async def business_text_mode(message: Message):

    user_modes[message.from_user.id] = "business"

    await message.answer(
        "💰 Бизнес режим включен"
    )


@dp.message(F.text == "🧘 Психолог")
async def psycho_mode(message: Message):

    user_modes[message.from_user.id] = "psychologist"

    await message.answer(
        "🧘 Режим психолога включен"
    )


@dp.message(F.text == "✍️ Тексты")
async def copy_mode(message: Message):

    user_modes[message.from_user.id] = "copywriter"

    await message.answer(
        "✍️ Режим копирайтера включен"
    )


@dp.message(F.text == "🧹 Очистить чат")
async def clear_chat(message: Message):

    user_memory[message.from_user.id] = []

    await message.answer(
        "🧹 История очищена"
    )


@dp.message(F.text == "🌐 Интернет")
async def internet_info(message: Message):

    await message.answer(
        "🌐 Просто отправьте запрос.\n\nНапример:\n• цена биткоина\n• новости AI\n• курс доллара"
    )


@dp.message(F.text == "📄 Документ")
async def docs_info(message: Message):

    await message.answer(
        "📄 Отправьте PDF, DOCX или TXT файл."
    )


@dp.message(F.text == "🖼 Фото")
async def photo_info(message: Message):

    await message.answer(
        "🖼 Отправьте изображение для анализа."
    )


@dp.message(F.text == "🧠 AI Чат")
async def ai_chat(message: Message):

    user_modes[message.from_user.id] = "default"

    await message.answer(
        "🧠 Обычный AI режим включен"
    )


# ====================================
# CHAT
# ====================================

@dp.message()
async def chat(message: Message):

    user_id = message.from_user.id
    user_text = message.text

    if user_id not in user_stats:

        user_stats[user_id] = {
            "messages": 0
        }

    user_stats[user_id]["messages"] += 1

    if user_id not in user_modes:
        user_modes[user_id] = "default"

    if user_id not in user_memory:

        current_mode = user_modes[user_id]

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
Вопрос пользователя:
{user_text}

Информация из интернета:
{internet_data}

Если это задача —
реши её пошагово.

Если это обучение —
объясни просто и понятно.

Не придумывай примеры,
если пользователь их не отправлял.
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
