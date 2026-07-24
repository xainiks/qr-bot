import os
import cv2
import numpy as np
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import CommandStart, Command

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Я бот для распознавания QR-кодов (включая сложные с логотипами).\n\n"
        "Просто отправь мне картинку или фото с QR-кодом, и я его расшифрую.\n\n"
        "📋 **Команды:**\n"
        "/help — помощь и инструкция\n"
        "/status — проверить работоспособность"
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "💡 **Как пользоваться:**\n"
        "Отправь скриншот или фото с QR-кодом, и бот выдаст результат."
    )

@dp.message(Command("status"))
async def status_cmd(message: Message):
    await message.answer("🟢 Бот в сети и готов к работе!")

@dp.message(F.photo | F.document)
async def scan_qr(message: Message):
    processing_msg = await message.answer("🔍 Получил картинку, ищу QR-код...")

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
    else:
        file_info = await bot.get_file(message.document.file_id)
        
    downloaded_file = await bot.download_file(file_info.file_path)
    file_bytes_array = downloaded_file.read()
    
    # 1. Пробуем сначала стандартный OpenCV
    img_np = np.asarray(bytearray(file_bytes_array), dtype=np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    
    val = ""
    if img is not None:
        detector = cv2.QRCodeDetector()
        variants = [
            img,
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
            cv2.bitwise_not(img)
        ]
        for variant in variants:
            v, _, _ = detector.detectAndDecode(variant)
            if v:
                val = v
                break

    # 2. Если OpenCV не справился (например, из-за крупного логотипа в центре), отправляем на API декодер
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
        await processing_msg.edit_text(f"✅ **QR-код успешно расшифрован:**\n\n{val}", parse_mode="Markdown")
    else:
        await processing_msg.edit_text("❌ На этой картинке не удалось найти QR-код. Попробуй обрезать скриншот ближе к самому QR-коду.")

# Удержание порта для Render
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
            
