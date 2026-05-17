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
    InlineKeyboardButton
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

    await message.answer(
        "🤖 AI Assistant\n\n"
        "Возможности:\n"
        "• AI чат\n"
        "• Интернет 🌐\n"
        "• PDF/DOCX/TXT 📄\n"
        "• Анализ фото 🖼\n"
        "• Решение задач 🧠",
        reply_markup=menu
    )


# ====================================
# SET MODE
# ====================================

async def set_mode(
    callback: CallbackQuery,
    mode_name: str
):

    user_id = callback.from_user.id

    user_modes[user_id] = mode_name

    user_memory[user_id] = [
        {
            "role": "system",
            "content": MODES[mode_name]
        }
    ]

    await callback.message.answer(
        f"✅ Режим: {mode_name}"
    )

    await callback.answer()


# ====================================
# MODE BUTTONS
# ====================================

@dp.callback_query(F.data == "coder")
async def coder_mode(callback: CallbackQuery):
    await set_mode(callback, "coder")


@dp.callback_query(F.data == "business")
async def business_mode(callback: CallbackQuery):
    await set_mode(callback, "business")


@dp.callback_query(F.data == "psychologist")
async def psychologist_mode(callback: CallbackQuery):
    await set_mode(callback, "psychologist")


@dp.callback_query(F.data == "copywriter")
async def copywriter_mode(callback: CallbackQuery):
    await set_mode(callback, "copywriter")


# ====================================
# NEW CHAT
# ====================================

@dp.callback_query(F.data == "new_chat")
async def new_chat(callback: CallbackQuery):

    user_id = callback.from_user.id

    current_mode = user_modes.get(
        user_id,
        "default"
    )

    user_memory[user_id] = [
        {
            "role": "system",
            "content": MODES[current_mode]
        }
    ]

    await callback.message.answer(
        "🧹 История очищена"
    )

    await callback.answer()


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

            # PDF
            if suffix == ".pdf":

                with open(temp_file.name, "rb") as pdf_file:

                    reader = PyPDF2.PdfReader(pdf_file)

                    for page in reader.pages:
                        extracted = page.extract_text()

                        if extracted:
                            text += extracted

            # TXT
            elif suffix == ".txt":

                with open(
                    temp_file.name,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as txt_file:

                    text = txt_file.read()

            # DOCX
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

1. Сделай краткое содержание
2. Если это задача — реши её
3. Если это обучение — объясни просто
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
                            "text": (
                                "Опиши изображение. "
                                "Если это задача — реши её пошагово. "
                                "Если на фото есть текст — прочитай его."
                            )
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
# CHAT
# ====================================

@dp.message()
async def chat(message: Message):

    user_id = message.from_user.id
    user_text = message.text

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
объясни просто.
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
