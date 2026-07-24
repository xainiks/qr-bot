import os
import cv2
import numpy as np
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Я бот для распознавания QR-кодов.\n\n"
        "просто отправь мне картинку или фото с QR-кодом, и я его расшифрую.\n\n"
        "📋 **Доступные команды:**\n"
        "/help — помощь и инструкция\n"
        "/status — проверить работоспособность бота"
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "💡 **Как пользоваться ботом:**\n"
        "1. Отправь в чат скриншот или фото, где есть QR-код.\n"
        "2. Старайся отправлять картинку так, чтобы сам квадрат QR-кода был хорошо виден и не обрезался.\n"
        "3. Бот мгновенно пришлет тебе расшифрованную ссылку или текст."
    )

@dp.message(Command("status"))
async def status_cmd(message: Message):
    await message.answer("🟢 Бот в сети, работает стабильно и ждет твои картинки!")

@dp.message(F.photo | F.document)
async def scan_qr(message: Message):
    # Сразу даем знать, что бот получил файл и приступил к работе
    processing_msg = await message.answer("🔍 Получил картинку, ищу QR-код...")

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
    else:
        file_info = await bot.get_file(message.document.file_id)
        
    downloaded_file = await bot.download_file(file_info.file_path)
    
    file_bytes = np.asarray(bytearray(downloaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if img is None:
        await processing_msg.edit_text("❌ Не удалось прочитать файл картинки.")
        return

    detector = cv2.QRCodeDetector()
    
    variants = [
        img,
        cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
        cv2.bitwise_not(img)
    ]

    val = ""
    for variant in variants:
        v, _, _ = detector.detectAndDecode(variant)
        if v:
            val = v
            break

    if val:
        await processing_msg.edit_text(f"✅ **QR-код успешно расшифрован:**\n\n{val}", parse_mode="Markdown")
    else:
        await processing_msg.edit_text("❌ На этой картинке не удалось найти QR-код. Попробуй обрезать скриншот ближе к самому QR-коду.")

# Код для удержания открытого порта на Render
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
    
