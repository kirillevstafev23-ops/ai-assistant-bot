# -*- coding: utf-8 -*-

import os
import asyncio
import sqlite3
import base64

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.enums import ChatAction

from openai import OpenAI


# ====================================
# TOKENS
# ====================================

TOKEN = os.getenv("TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ====================================
# BOT
# ====================================

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ====================================
# DATABASE
# ====================================

db = sqlite3.connect("database.db")

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    mode TEXT
)
""")

db.commit()


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
        "Ты полезный AI ассистент. "
        "Отвечай дружелюбно и понятно."
    ),

    "coder": (
        "Ты опытный программист. "
        "Помогай с кодом и объясняй просто."
    ),

    "business": (
        "Ты бизнес-консультант. "
        "Помогай с идеями и заработком."
    ),

    "psychologist": (
        "Ты спокойный психолог. "
        "Поддерживай пользователя."
    ),

    "copywriter": (
        "Ты профессиональный копирайтер. "
        "Пиши сильные тексты."
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
# START
# ====================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "🤖 AI Assistant\n\n"
        "Выбери режим AI 👇",
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

    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, mode) VALUES (?, ?)",
        (user_id, mode_name)
    )

    db.commit()

    user_memory[user_id] = [
        {
            "role": "system",
            "content": MODES[mode_name]
        }
    ]

    titles = {
        "coder": "👨‍💻 Программист",
        "business": "💰 Бизнес",
        "psychologist": "🧠 Психолог",
        "copywriter": "✍️ Копирайтер"
    }

    await callback.message.answer(
        f"Режим выбран:\n{titles[mode_name]}"
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
# CLEAR COMMAND
# ====================================

@dp.message(F.text == "/clear")
async def clear_chat(message: Message):

    user_id = message.from_user.id

    mode = user_modes.get(user_id, "default")

    user_memory[user_id] = [
        {
            "role": "system",
            "content": MODES[mode]
        }
    ]

    await message.answer("🧹 История очищена")


# ====================================
# PHOTO ANALYSIS
# ====================================

@dp.message(F.photo)
async def photo_handler(message: Message):

    await bot.send_chat_action(
        message.chat.id,
        ChatAction.TYPING
    )

    wait_message = await message.answer(
        "🖼 Анализирую изображение..."
    )

    try:

        photo = message.photo[-1]

        file = await bot.get_file(photo.file_id)

        file_path = file.file_path

        downloaded_file = await bot.download_file(file_path)

        image_bytes = downloaded_file.read()

        base64_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Проанализируй это изображение максимально подробно"
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
# CHAT
# ====================================

@dp.message()
async def chat(message: Message):

    user_id = message.from_user.id
    user_text = message.text

    # default mode
    if user_id not in user_modes:
        user_modes[user_id] = "default"

    # create memory
    if user_id not in user_memory:

        current_mode = user_modes[user_id]

        user_memory[user_id] = [
            {
                "role": "system",
                "content": MODES[current_mode]
            }
        ]

    # save user message
    user_memory[user_id].append(
        {
            "role": "user",
            "content": user_text
        }
    )

    # limit memory
    user_memory[user_id] = user_memory[user_id][-20:]

    await bot.send_chat_action(
        message.chat.id,
        ChatAction.TYPING
    )

    wait_message = await message.answer(
        "💭 Думаю..."
    )

    try:

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=user_memory[user_id]
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "AI не смог ответить."

        # save answer
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
