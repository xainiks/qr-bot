import os
import cv2
import numpy as np
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from qreader import QReader

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализируем QReader один раз при запуске бота
qreader = QReader()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет! Отправь мне картинку или скриншот с QR-кодом, и я его расшифрую.")

@dp.message(F.photo)
async def scan_qr(message: Message):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    
    file_bytes = np.asarray(bytearray(downloaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if img is None:
        await message.answer("Не удалось прочитать файл картинки.")
        return

    # QReader работает с RGB-изображениями (OpenCV по умолчанию открывает в BGR)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Распознаем QR-код с помощью нейросети
    val = qreader.detect_and_decode(image=rgb_img)
    
    # QReader возвращает кортеж/список строк, берем первую найденную
    if val and val[0]:
        await message.answer(f"✅ **QR-код успешно расшифрован:**\n\n{val[0]}", parse_mode="Markdown")
    else:
        await message.answer("❌ На этой картинке не удалось найти QR-код.")

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
    
