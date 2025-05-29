import os
import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook import SendMessage
from utils.pdf_parser import parse_pdf

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("BOT_TOKEN и WEBHOOK_URL должны быть заданы через переменные окружения.")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_FULL_URL = WEBHOOK_URL + WEBHOOK_PATH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("👋 Привет! Бот запущен и готов принять PDF.")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):
    document = message.document
    if document.mime_type != 'application/pdf':
        await message.reply("Пожалуйста, отправьте PDF файл.")
        return

    file_info = await bot.get_file(document.file_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)
    local_path = f"temp/{document.file_name}"

    os.makedirs("temp", exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(file.read())

    lines = parse_pdf(local_path)
    preview = "\n".join(lines)
    await message.reply(f"📄 PDF обработан:

{preview}")

@app.on_event("startup")
async def on_startup():
    logger.info("⚙️ Устанавливаю вебхук...")
    await bot.set_webhook(WEBHOOK_FULL_URL)
    logger.info(f"✅ Вебхук установлен: {WEBHOOK_FULL_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🧹 Удаляю вебхук...")
    await bot.delete_webhook()

@app.post(WEBHOOK_PATH)
async def handle_webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "бот работает", "webhook": WEBHOOK_FULL_URL}