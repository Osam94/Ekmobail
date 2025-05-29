import logging
import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook
from utils.pdf_parser import parse_pdf  # исправлено
from pathlib import Path

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

app = FastAPI()
logging.basicConfig(level=logging.INFO)

PDF_PATH = Path("data") / "current.pdf"
PDF_PATH.parent.mkdir(exist_ok=True)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("👋 Привет! Отправьте PDF-файл, и я его обработаю.")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_pdf(message: types.Message):
    document = message.document
    if not document.mime_type == "application/pdf":
        await message.reply("❗ Пожалуйста, отправьте PDF-файл.")
        return

    file = await bot.get_file(document.file_id)
    file_path = file.file_path
    await bot.download_file(file_path, destination=PDF_PATH)

    try:
        rows = parse_pdf(PDF_PATH)
        preview = "\n".join(rows[:10])
        await message.reply(f"📄 PDF обработан:\n\n{preview}")
    except Exception as e:
        logging.error(f"Ошибка при обработке PDF: {e}")
        await message.reply("❌ Произошла ошибка при обработке PDF.")

@app.post(WEBHOOK_PATH)
async def handle_webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return "ok"

@app.on_event("startup")
async def on_startup():
    logging.warning("⚙️ Устанавливаю вебхук...")
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Вебхук установлен: {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    logging.warning("🔻 Удаляю вебхук...")
    await bot.delete_webhook()
