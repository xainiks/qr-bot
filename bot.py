import os
import cv2
import numpy as np
import requests
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from aiogram.filters import CommandStart, Command
from pylibdmtx.pylibdmtx import decode as decode_dmtx  # Импортируем детектор Data Matrix

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = f"https://qr-bot-c80q.onrender.com/webhook/{TOKEN}"
WEBHOOK_PATH = f"/webhook/{TOKEN}"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Я бот для распознавания QR и Data Matrix кодов.\n\n"
        "Отправь мне картинку или фото с кодом, и я его расшифрую."
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("💡 Отправь скриншот или фото с кодом (включая точечные Data Matrix), и бот выдаст результат.")

@dp.message(Command("status"))
async def status_cmd(message: Message):
    await message.answer("🟢 Бот в сети и работает через Webhook!")

@dp.message(F.photo | F.document)
async def scan_qr(message: Message):
    processing_msg = await message.answer("🔍 Анализирую код на картинке...")

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
    else:
        file_info = await bot.get_file(message.document.file_id)
        
    downloaded_file = await bot.download_file(file_info.file_path)
    file_bytes_array = downloaded_file.read()
    
    img_np = np.asarray(bytearray(file_bytes_array), dtype=np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    
    val = ""
    
    # 1. Сначала проверяем через Pylibdmtx (специально для точечных Data Matrix кодов)
    if img is not None:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray) # Повышаем контраст
        
        decoded_objects = decode_dmtx(gray)
        if decoded_objects:
            val = decoded_objects[0].data.decode('utf-8')

    # 2. Если не нашли Data Matrix, пробуем классический OpenCV QR-детектор
    if not val and img is not None:
        detector = cv2.QRCodeDetector()
        variants = [img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.bitwise_not(img)]
        for variant in variants:
            v, _, _ = detector.detectAndDecode(variant)
            if v:
                val = v
                break

    # 3. Если всё еще пусто, отправляем на внешнее API для подстраховки
    if not val:
        try:
            response = requests.post(
                "https://api.qrserver.com/v1/read-qr-code/",
                files={"file": ("qr.png", file_bytes_array)}
            )
            res_json = response.json()
            if res_json and res_json[0]["symbol"][0]["data"]:
                val = res_json[0]["symbol"][0]["data"]
        except Exception:
            pass

    if val:
        await processing_msg.edit_text(f"✅ **Код успешно расшифрован:**\n\n{val}", parse_mode="Markdown")
    else:
        await processing_msg.edit_text("❌ На этой картинке не удалось найти код. Попробуй сделать фото чуть ровнее.")

# Настройка aiohttp для Webhook
async def handle_webhook(request: web.Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return web.Response()

async def handle_ping(request: web.Request):
    return web.Response(text="Bot is running!")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.router.add_get("/", handle_ping)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
    
