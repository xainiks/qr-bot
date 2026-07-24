import os
import cv2
import numpy as np
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from aiogram.filters import CommandStart, Command

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = f"https://qr-bot-c80q.onrender.com/webhook/{TOKEN}"
WEBHOOK_PATH = f"/webhook/{TOKEN}"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    print(f"[LOG] User {message.from_user.id} started the bot.")
    await message.answer(
        "👋 Привет! Я бот для распознавания QR и матричных кодов.\n\n"
        "Отправь мне картинку или фото с кодом, и я его расшифрую."
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("💡 Отправь скриншот или фото с кодом, и бот выдаст результат.")

@dp.message(Command("status"))
async def status_cmd(message: Message):
    print("[LOG] Status command checked.")
    await message.answer("🟢 Бот в сети и работает через Webhook!")

@dp.message(F.photo | F.document)
async def scan_qr(message: Message):
    print(f"[LOG] Received an image/document from user {message.from_user.id}")
    processing_msg = await message.answer("🔍 Ищу код на картинке...")
    val = ""
    
    try:
        if message.photo:
            photo = message.photo[-1]
            file_info = await bot.get_file(photo.file_id)
        else:
            file_info = await bot.get_file(message.document.file_id)
            
        print(f"[LOG] Downloading file from Telegram: {file_info.file_path}")
        downloaded_file = await bot.download_file(file_info.file_path)
        file_bytes_array = downloaded_file.read()
        
        img_np = np.asarray(bytearray(file_bytes_array), dtype=np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
        
        if img is not None:
            height, width = img.shape[:2]
            if max(height, width) > 1280:
                img = cv2.resize(img, (width // 2, height // 2), interpolation=cv2.INTER_AREA)

            print("[LOG] Starting OpenCV detection...")
            detector = cv2.QRCodeDetector()
            variants = [img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.bitwise_not(img)]
            for variant in variants:
                v, _, _ = detector.detectAndDecode(variant)
                if v:
                    val = v
                    print(f"[LOG] OpenCV successfully found code: {val}")
                    break

        if not val:
            print("[LOG] OpenCV missed. Trying external QR API...")
            url = "https://api.qrserver.com/v1/read-qr-code/"
            data = aiohttp.FormData()
            data.add_field('file', file_bytes_array, filename='image.png', content_type='image/png')
            
            client_timeout = aiohttp.ClientTimeout(total=4)
            async with aiohttp.ClientSession(timeout=client_timeout) as session:
                async with session.post(url, data=data) as response:
                    res_json = await response.json()
                    if res_json and res_json[0].get("symbol"):
                        symbol = res_json[0]["symbol"][0]
                        if symbol.get("data"):
                            val = symbol["data"]
                            print(f"[LOG] External API successfully found code: {val}")
                            
    except Exception as e:
        print(f"[ERROR] Exception during processing image: {e}")

    try:
        if val:
            await processing_msg.edit_text(f"✅ **Код успешно расшифрован:**\n\n{val}", parse_mode="Markdown")
            print("[LOG] Result sent to user successfully.")
        else:
            await processing_msg.edit_text("❌ На этой картинке не удалось найти код или вышло время ожидания.")
            print("[LOG] Code not found message sent.")
    except Exception as e:
        print(f"[ERROR] Could not edit processing message: {e}")

async def handle_webhook(request: web.Request):
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"[ERROR] Handling webhook update: {e}")
    return web.Response(text="OK")

async def handle_ping(request: web.Request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.router.add_get("/", handle_ping)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[LOG] Server successfully started on port {port}")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
