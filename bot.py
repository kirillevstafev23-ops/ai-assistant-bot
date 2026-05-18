# -*- coding: utf-8 -*-

import os
import asyncio
import sqlite3
import tempfile
import base64

from PIL import Image
import pytesseract

import PyPDF2
from docx import Document

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from openai import OpenAI

# =====================
# TOKENS
# =====================
TOKEN = os.getenv("TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# =====================
# BOT
# =====================
bot = Bot(token=TOKEN)
dp = Dispatcher()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# =====================
# DB
# =====================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT,
    content TEXT
)
""")
conn.commit()

# =====================
# MEMORY
# =====================
def save_memory(user_id, role, content):
    cursor.execute(
        "INSERT INTO memory (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    conn.commit()

def load_memory(user_id):
    cursor.execute(
        "SELECT role, content FROM memory WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (user_id,)
    )
    rows = cursor.fetchall()[::-1]

    messages = [
        {"role": "system", "content": "Ты умный AI ассистент. Отвечай кратко и понятно."}
    ]

    for r in rows:
        messages.append({"role": r[0], "content": r[1]})

    return messages

def clear_memory(user_id):
    cursor.execute("DELETE FROM memory WHERE user_id=?", (user_id,))
    conn.commit()

# =====================
# START
# =====================
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🚀 AI бот запущен\n\n"
        "📌 Можно:\n"
        "- писать текст\n"
        "- отправлять фото\n"
        "- PDF / DOCX / TXT\n"
    )

# =====================
# TEXT CHAT
# =====================
@dp.message(F.text)
async def chat(message: Message):

    user_id = message.from_user.id

    await message.answer("🧠 Думаю...")

    save_memory(user_id, "user", message.text)

    messages = load_memory(user_id)
    messages.append({"role": "user", "content": message.text})

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages
        )

        answer = response.choices[0].message.content

        save_memory(user_id, "assistant", answer)

        await message.answer(answer)

    except Exception as e:
        await message.answer(f"Ошибка AI: {e}")

# =====================
# PHOTO + OCR + GPT VISION
# =====================
@dp.message(F.photo)
async def photo_handler(message: Message):

    wait = await message.answer("🖼 Анализирую фото...")

    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
            await bot.download_file(file.file_path, temp.name)

            image = Image.open(temp.name)

            # OCR
            ocr_text = pytesseract.image_to_string(image, lang="eng+rus")

            # base64
            with open(temp.name, "rb") as img:
                b64 = base64.b64encode(img.read()).decode()

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Реши задачу с изображения.\nOCR:\n{ocr_text}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}"
                            }
                        }
                    ]
                }
            ]
        )

        await message.answer(response.choices[0].message.content)

    except Exception as e:
        await message.answer(f"Ошибка фото: {e}")

    await wait.delete()

# =====================
# DOCUMENTS (PDF / DOCX / TXT)
# =====================
@dp.message(F.document)
async def doc_handler(message: Message):

    wait = await message.answer("📄 Читаю файл...")

    try:
        doc = message.document
        file = await bot.get_file(doc.file_id)

        suffix = os.path.splitext(doc.file_name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            await bot.download_file(file.file_path, temp.name)

            text = ""

            # PDF
            if suffix == ".pdf":
                with open(temp.name, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() or ""

            # TXT
            elif suffix == ".txt":
                with open(temp.name, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()

            # DOCX
            elif suffix == ".docx":
                docx = Document(temp.name)
                for p in docx.paragraphs:
                    text += p.text + "\n"

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"Проанализируй документ:\n\n{text[:15000]}"
                }
            ]
        )

        await message.answer(response.choices[0].message.content)

    except Exception as e:
        await message.answer(f"Ошибка файла: {e}")

    await wait.delete()

# =====================
# START BOT
# =====================
async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
